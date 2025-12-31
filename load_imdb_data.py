import gzip
import shutil
import os
import urllib.request
import pymysql
from config import connection
import time
import json

# IMDb dataset URL'leri
DATASETS = {
    'title.basics': 'https://datasets.imdbws.com/title.basics.tsv.gz',
    'title.ratings': 'https://datasets.imdbws.com/title.ratings.tsv.gz',
    'title.crew': 'https://datasets.imdbws.com/title.crew.tsv.gz',
    'title.principals': 'https://datasets.imdbws.com/title.principals.tsv.gz',
    'name.basics': 'https://datasets.imdbws.com/name.basics.tsv.gz',
    'title.akas': 'https://datasets.imdbws.com/title.akas.tsv.gz',
    'title.episode': 'https://datasets.imdbws.com/title.episode.tsv.gz'
}

DATA_DIR = 'imdb_data'

def create_data_directory():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"✓ {DATA_DIR} dizini oluşturuldu")

def download_dataset(name, url):
    gz_filename = os.path.join(DATA_DIR, f"{name}.tsv.gz")
    tsv_filename = os.path.join(DATA_DIR, f"{name}.tsv")
    if os.path.exists(tsv_filename):
        return tsv_filename
    print(f"→ {name} indiriliyor ve çıkarılıyor...")
    urllib.request.urlretrieve(url, gz_filename)
    with gzip.open(gz_filename, 'rb') as f_in:
        with open(tsv_filename, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    os.remove(gz_filename)
    return tsv_filename

def convert_value(value):
    if value == '\\N' or value == '' or value == 'NULL':
        return None
    return value

# 1. TITLES & GENRES
def load_titles_and_genres(cursor, filename, limit):
    print("\n→ Titles ve Genre verileri işleniyor...")
    title_genres_data = []
    unique_genres = set()
    
    with open(filename, 'r', encoding='utf-8') as f:
        next(f)
        count = 0
        batch = []
        for line in f:
            if limit and count >= limit: break
            parts = line.strip().split('\t')
            tconst = parts[0]
            batch.append((tconst, convert_value(parts[1]), convert_value(parts[2]), 
                          convert_value(parts[3]), 1 if parts[4]=='1' else 0, 
                          convert_value(parts[5]), convert_value(parts[6]), convert_value(parts[7])))
            
            genres = convert_value(parts[8])
            if genres:
                for g in genres.split(','):
                    g = g.strip()
                    unique_genres.add(g)
                    title_genres_data.append((tconst, g))
            
            count += 1
            if len(batch) >= 2000:
                cursor.executemany("INSERT IGNORE INTO titles VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", batch)
                batch = []
        if batch: cursor.executemany("INSERT IGNORE INTO titles VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", batch)
    
    # Genres tablosunu doldur
    cursor.executemany("INSERT IGNORE INTO genres (genre_name) VALUES (%s)", [(g,) for g in unique_genres])
    connection.commit()
    
    # Title_Genres mapping
    cursor.execute("SELECT genre_id, genre_name FROM genres")
    g_map = {r['genre_name']: r['genre_id'] for r in cursor.fetchall()}
    tg_batch = [(tc, g_map[gn]) for tc, gn in title_genres_data if gn in g_map]
    cursor.executemany("INSERT IGNORE INTO title_genres (tconst, genre_id) VALUES (%s, %s)", tg_batch)
    connection.commit()
    print(f"✓ Titles ve Genres yüklendi.")

# 2. RATINGS
def load_ratings(cursor, filename, limit):
    print("→ Ratings yükleniyor...")
    with open(filename, 'r', encoding='utf-8') as f:
        next(f)
        batch = []
        for i, line in enumerate(f):
            if limit and i >= limit: break
            p = line.strip().split('\t')
            batch.append((p[0], convert_value(p[1]), convert_value(p[2])))
            if len(batch) >= 2000:
                cursor.executemany("INSERT IGNORE INTO ratings (title_id, average_rating, num_votes) VALUES (%s,%s,%s)", batch)
                batch = []
        if batch: cursor.executemany("INSERT IGNORE INTO ratings (title_id, average_rating, num_votes) VALUES (%s,%s,%s)", batch)
    connection.commit()

# 3. CREW (3NF: Directors & Writers)
def load_crew_3nf(cursor, filename, limit):
    print("→ Crew (Yönetmenler ve Yazarlar) 3NF olarak işleniyor...")
    with open(filename, 'r', encoding='utf-8') as f:
        next(f)
        for i, line in enumerate(f):
            if limit and i >= limit: break
            p = line.strip().split('\t')
            tconst = p[0]
            cursor.execute("INSERT IGNORE INTO crew (tconst) VALUES (%s)", (tconst,))
            
            if convert_value(p[1]): # directors
                dirs = [(tconst, d.strip()) for d in p[1].split(',')]
                cursor.executemany("INSERT IGNORE INTO crew_directors (tconst, nconst) VALUES (%s,%s)", dirs)
            
            if convert_value(p[2]): # writers
                writs = [(tconst, w.strip()) for w in p[2].split(',')]
                cursor.executemany("INSERT IGNORE INTO crew_writers (tconst, nconst) VALUES (%s,%s)", writs)
            
            if i % 1000 == 0: connection.commit()
    connection.commit()

# 4. PEOPLE & PROFESSIONS
def load_people_3nf(cursor, filename, limit):
    print("→ People ve Meslekler yükleniyor...")
    unique_profs = set()
    people_profs = []
    with open(filename, 'r', encoding='utf-8') as f:
        next(f)
        batch = []
        for i, line in enumerate(f):
            if limit and i >= limit: break
            p = line.strip().split('\t')
            nconst = p[0]
            most_known = p[5].split(',')[0] if convert_value(p[5]) else None
            batch.append((nconst, convert_value(p[1]), convert_value(p[2]), convert_value(p[3]), most_known))
            
            if convert_value(p[4]):
                for prof in p[4].split(','):
                    prof = prof.strip()
                    unique_profs.add(prof)
                    people_profs.append((nconst, prof))
            
            if len(batch) >= 2000:
                cursor.executemany("INSERT IGNORE INTO people VALUES (%s,%s,%s,%s,%s)", batch)
                batch = []
        if batch: cursor.executemany("INSERT IGNORE INTO people VALUES (%s,%s,%s,%s,%s)", batch)
    
    cursor.executemany("INSERT IGNORE INTO professions (profession_name) VALUES (%s)", [(pr,) for pr in unique_profs])
    connection.commit()
    
    cursor.execute("SELECT profession_id, profession_name FROM professions")
    p_map = {r['profession_name']: r['profession_id'] for r in cursor.fetchall()}
    pp_batch = [(nc, p_map[pn]) for nc, pn in people_profs if pn in p_map]
    cursor.executemany("INSERT IGNORE INTO people_professions (nconst, profession_id) VALUES (%s,%s)", pp_batch)
    connection.commit()

# 5. PRINCIPALS & CHARACTERS
def load_principals_and_chars(cursor, filename, limit):
    print("→ Principals ve Karakter isimleri yükleniyor...")
    with open(filename, 'r', encoding='utf-8') as f:
        next(f)
        for i, line in enumerate(f):
            if limit and i >= limit: break
            p = line.strip().split('\t')
            cursor.execute("INSERT INTO principals (tconst, ordering, nconst, category, job) VALUES (%s,%s,%s,%s,%s)",
                           (p[0], p[1], p[2], convert_value(p[3]), convert_value(p[4])))
            pid = cursor.lastrowid
            
            chars = convert_value(p[5])
            if chars:
                # IMDb character format: ["Char1","Char2"]
                chars_list = chars.strip('[]').replace('"', '').split(',')
                for cname in chars_list:
                    if cname.strip():
                        cursor.execute("INSERT INTO principal_characters (principal_id, character_name) VALUES (%s,%s)", (pid, cname.strip()))
            
            if i % 1000 == 0: connection.commit()
    connection.commit()

# 6. AKAS
def load_akas(cursor, filename, limit):
    print("→ Alternatif isimler (AKAS) yükleniyor...")
    with open(filename, 'r', encoding='utf-8') as f:
        next(f)
        batch = []
        for i, line in enumerate(f):
            if limit and i >= limit: break
            p = line.strip().split('\t')
            # titleId, ordering, title, region, language, types, attributes, isOriginalTitle
            batch.append((p[0], p[1], convert_value(p[2]), convert_value(p[3]), convert_value(p[4]), 
                          convert_value(p[5]), convert_value(p[6]), 1 if p[7]=='1' else 0))
            if len(batch) >= 2000:
                cursor.executemany("INSERT IGNORE INTO akas VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", batch)
                batch = []
        if batch: cursor.executemany("INSERT IGNORE INTO akas VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", batch)
    connection.commit()

# 7. EPISODES
def load_episodes(cursor, filename, limit):
    print("→ Bölüm bilgileri (Episodes) yükleniyor...")
    with open(filename, 'r', encoding='utf-8') as f:
        next(f)
        batch = []
        for i, line in enumerate(f):
            if limit and i >= limit: break
            p = line.strip().split('\t')
            batch.append((p[0], p[1], convert_value(p[2]), convert_value(p[3])))
            if len(batch) >= 2000:
                cursor.executemany("INSERT IGNORE INTO episodes VALUES (%s,%s,%s,%s)", batch)
                batch = []
        if batch: cursor.executemany("INSERT IGNORE INTO episodes VALUES (%s,%s,%s,%s)", batch)
    connection.commit()

def main():
    start = time.time()
    create_data_directory()
    LIMIT = 200000 # Test için her tablodan 10 bin kayıt. Tamamı için None yap.
    
    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        load_titles_and_genres(cursor, download_dataset('title.basics', DATASETS['title.basics']), LIMIT)
        load_ratings(cursor, download_dataset('title.ratings', DATASETS['title.ratings']), LIMIT)
        load_crew_3nf(cursor, download_dataset('title.crew', DATASETS['title.crew']), LIMIT)
        load_people_3nf(cursor, download_dataset('name.basics', DATASETS['name.basics']), LIMIT)
        load_principals_and_chars(cursor, download_dataset('title.principals', DATASETS['title.principals']), LIMIT)
        load_akas(cursor, download_dataset('title.akas', DATASETS['title.akas']), LIMIT)
        load_episodes(cursor, download_dataset('title.episode', DATASETS['title.episode']), LIMIT)
        
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        print(f"\n✅ İşlem tamamlandı! Toplam süre: {time.time()-start:.2f} saniye.")
    except Exception as e:
        print(f"\n❌ HATA: {e}")
        connection.rollback()
    finally:
        cursor.close()

if __name__ == "__main__":
    main()