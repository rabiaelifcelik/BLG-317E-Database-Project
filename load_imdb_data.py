"""
IMDb Non-Commercial Datasets Yükleme Scripti
https://developer.imdb.com/non-commercial-datasets/

Bu script IMDb'nin TSV formatındaki datasetlerini indirir ve MySQL veritabanına yükler.
"""

import gzip
import shutil
import os
import urllib.request
import pymysql
from config import connection
import time

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
    """Veri dizinini oluştur"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"✓ {DATA_DIR} dizini oluşturuldu")

def download_dataset(name, url, limit_mb=None):
    """Dataset'i indir"""
    gz_filename = os.path.join(DATA_DIR, f"{name}.tsv.gz")
    tsv_filename = os.path.join(DATA_DIR, f"{name}.tsv")
    
    # Eğer TSV dosyası zaten varsa atla
    if os.path.exists(tsv_filename):
        print(f"✓ {name} zaten mevcut, indirme atlanıyor")
        return tsv_filename
    
    # GZ dosyası varsa sadece çıkar
    if os.path.exists(gz_filename):
        print(f"✓ {name}.gz mevcut, çıkarılıyor...")
    else:
        print(f"→ {name} indiriliyor... (Bu işlem biraz zaman alabilir)")
        try:
            urllib.request.urlretrieve(url, gz_filename)
            print(f"✓ {name} indirildi")
        except Exception as e:
            print(f"✗ Hata: {name} indirilemedi: {e}")
            return None
    
    # GZ dosyasını çıkar
    try:
        with gzip.open(gz_filename, 'rb') as f_in:
            with open(tsv_filename, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        print(f"✓ {name} çıkarıldı")
        
        # GZ dosyasını sil (disk alanı için)
        os.remove(gz_filename)
        
        return tsv_filename
    except Exception as e:
        print(f"✗ Hata: {name} çıkarılamadı: {e}")
        return None

def convert_value(value):
    """\\N değerlerini NULL'a çevir"""
    if value == '\\N' or value == '' or value == 'NULL':
        return None
    return value

def load_titles(cursor, filename, limit=None):
    """Titles tablosunu yükle (genres olmadan)"""
    print("\n→ Titles tablosu yükleniyor...")
    
    title_genres_data = []  # Genre verilerini sakla
    
    with open(filename, 'r', encoding='utf-8') as f:
        next(f)  # Header'ı atla
        
        batch = []
        count = 0
        
        for line in f:
            if limit and count >= limit:
                break
                
            parts = line.strip().split('\t')
            if len(parts) >= 9:
                tconst = parts[0]
                titleType = convert_value(parts[1])
                primaryTitle = convert_value(parts[2])
                originalTitle = convert_value(parts[3])
                isAdult = 1 if parts[4] == '1' else 0
                startYear = convert_value(parts[5])
                endYear = convert_value(parts[6])
                runtimeMinutes = convert_value(parts[7])
                genres = convert_value(parts[8])
                
                # Titles tablosuna genres olmadan ekle
                batch.append((tconst, titleType, primaryTitle, originalTitle, 
                            isAdult, startYear, endYear, runtimeMinutes))
                
                # Genre verilerini sakla
                if genres:
                    for genre in genres.split(','):
                        genre = genre.strip()
                        if genre:
                            title_genres_data.append((tconst, genre))
                
                if len(batch) >= 1000:
                    cursor.executemany(
                        """INSERT IGNORE INTO titles 
                        (tconst, titleType, primaryTitle, originalTitle, isAdult, 
                         startYear, endYear, runtimeMinutes) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                        batch
                    )
                    connection.commit()
                    count += len(batch)
                    print(f"  {count} kayıt yüklendi...", end='\r')
                    batch = []
        
        # Kalan kayıtları yükle
        if batch:
            cursor.executemany(
                """INSERT IGNORE INTO titles 
                (tconst, titleType, primaryTitle, originalTitle, isAdult, 
                 startYear, endYear, runtimeMinutes) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                batch
            )
            connection.commit()
            count += len(batch)
    
    print(f"\n✓ {count} titles kaydı yüklendi")
    return title_genres_data

def load_genres(cursor, genres_data):
    """Genres tablosunu yükle"""
    print("\n→ Genres tablosu yükleniyor...")
    
    # Unique genres al
    unique_genres = list(set([genre for _, genre in genres_data]))
    
    batch = []
    count = 0
    
    for genre in unique_genres:
        batch.append((genre,))
        
        if len(batch) >= 1000:
            cursor.executemany(
                """INSERT IGNORE INTO genres (genre_name) 
                VALUES (%s)""",
                batch
            )
            connection.commit()
            count += len(batch)
            print(f"  {count} kayıt yüklendi...", end='\r')
            batch = []
    
    if batch:
        cursor.executemany(
            """INSERT IGNORE INTO genres (genre_name) 
            VALUES (%s)""",
            batch
        )
        connection.commit()
        count += len(batch)
    
    print(f"\n✓ {count} genres kaydı yüklendi")

def load_title_genres(cursor, title_genres_data):
    """Title-Genres ilişki tablosunu yükle"""
    print("\n→ Title_Genres ilişkileri yükleniyor...")
    
    # Genre name'leri ID'lere çevirmek için bir mapping oluştur
    cursor.execute("SELECT genre_id, genre_name FROM genres")
    all_genres = cursor.fetchall()
    genre_map = {genre['genre_name']: genre['genre_id'] for genre in all_genres}
    
    batch = []
    count = 0
    
    for tconst, genre_name in title_genres_data:
        if genre_name in genre_map:
            genre_id = genre_map[genre_name]
            batch.append((tconst, genre_id))
            
            if len(batch) >= 1000:
                cursor.executemany(
                    """INSERT IGNORE INTO title_genres 
                    (tconst, genre_id) 
                    VALUES (%s, %s)""",
                    batch
                )
                connection.commit()
                count += len(batch)
                print(f"  {count} kayıt yüklendi...", end='\r')
                batch = []
    
    if batch:
        cursor.executemany(
            """INSERT IGNORE INTO title_genres 
            (tconst, genre_id) 
            VALUES (%s, %s)""",
            batch
        )
        connection.commit()
        count += len(batch)
    
    print(f"\n✓ {count} title_genres kaydı yüklendi")

def load_ratings(cursor, filename, limit=None):
    """Ratings tablosunu yükle"""
    print("\n→ Ratings tablosu yükleniyor...")
    
    with open(filename, 'r', encoding='utf-8') as f:
        next(f)  # Header'ı atla
        
        batch = []
        count = 0
        
        for line in f:
            if limit and count >= limit:
                break
                
            parts = line.strip().split('\t')
            if len(parts) >= 3:
                title_id = parts[0]
                average_rating = convert_value(parts[1])
                num_votes = convert_value(parts[2])
                
                batch.append((title_id, average_rating, num_votes))
                
                if len(batch) >= 1000:
                    cursor.executemany(
                        """INSERT IGNORE INTO ratings 
                        (title_id, average_rating, num_votes) 
                        VALUES (%s, %s, %s)""",
                        batch
                    )
                    connection.commit()
                    count += len(batch)
                    print(f"  {count} kayıt yüklendi...", end='\r')
                    batch = []
        
        if batch:
            cursor.executemany(
                """INSERT IGNORE INTO ratings 
                (title_id, average_rating, num_votes) 
                VALUES (%s, %s, %s)""",
                batch
            )
            connection.commit()
            count += len(batch)
    
    print(f"\n✓ {count} ratings kaydı yüklendi")

def load_crew(cursor, filename, limit=None):
    """Crew tablosunu yükle"""
    print("\n→ Crew tablosu yükleniyor...")
    
    with open(filename, 'r', encoding='utf-8') as f:
        next(f)  # Header'ı atla
        
        batch = []
        count = 0
        
        for line in f:
            if limit and count >= limit:
                break
                
            parts = line.strip().split('\t')
            if len(parts) >= 3:
                tconst = parts[0]
                directors = convert_value(parts[1])
                writers = convert_value(parts[2])
                
                batch.append((tconst, directors, writers))
                
                if len(batch) >= 1000:
                    cursor.executemany(
                        """INSERT IGNORE INTO crew 
                        (tconst, directors, writers) 
                        VALUES (%s, %s, %s)""",
                        batch
                    )
                    connection.commit()
                    count += len(batch)
                    print(f"  {count} kayıt yüklendi...", end='\r')
                    batch = []
        
        if batch:
            cursor.executemany(
                """INSERT IGNORE INTO crew 
                (tconst, directors, writers) 
                VALUES (%s, %s, %s)""",
                batch
            )
            connection.commit()
            count += len(batch)
    
    print(f"\n✓ {count} crew kaydı yüklendi")

def load_principals(cursor, filename, limit=None):
    """Principals tablosunu yükle (characters olmadan)"""
    print("\n→ Principals tablosu yükleniyor...")
    
    characters_data = []  # Character verilerini sakla
    
    with open(filename, 'r', encoding='utf-8') as f:
        next(f)  # Header'ı atla
        
        batch = []
        count = 0
        principal_id_counter = 1  # Manuel ID sayacı
        
        for line in f:
            if limit and count >= limit:
                break
                
            parts = line.strip().split('\t')
            if len(parts) >= 6:
                tconst = parts[0]
                ordering = convert_value(parts[1])
                nconst = parts[2]
                category = convert_value(parts[3])
                job = convert_value(parts[4])
                characters = convert_value(parts[5])
                
                # Principals tablosuna characters olmadan ekle
                batch.append((tconst, ordering, nconst, category, job))
                
                # Character verilerini sakla (principal_id ile)
                if characters:
                    # Characters JSON formatında olabilir: ["Character 1","Character 2"]
                    # Köşeli parantezleri ve tırnak işaretlerini temizle
                    chars_clean = characters.strip('[]').replace('"', '')
                    for char in chars_clean.split(','):
                        char = char.strip()
                        if char:
                            characters_data.append((principal_id_counter, char))
                
                principal_id_counter += 1
                
                if len(batch) >= 1000:
                    cursor.executemany(
                        """INSERT IGNORE INTO principals 
                        (tconst, ordering, nconst, category, job) 
                        VALUES (%s, %s, %s, %s, %s)""",
                        batch
                    )
                    connection.commit()
                    count += len(batch)
                    print(f"  {count} kayıt yüklendi...", end='\r')
                    batch = []
        
        if batch:
            cursor.executemany(
                """INSERT IGNORE INTO principals 
                (tconst, ordering, nconst, category, job) 
                VALUES (%s, %s, %s, %s, %s)""",
                batch
            )
            connection.commit()
            count += len(batch)
    
    print(f"\n✓ {count} principals kaydı yüklendi")
    return characters_data

def load_principal_characters(cursor, characters_data):
    """Principal Characters tablosunu yükle"""
    print("\n→ Principal_Characters tablosu yükleniyor...")
    
    # Önce principals tablosundan gerçek ID'leri al
    cursor.execute("SELECT principal_id, tconst, ordering, nconst FROM principals ORDER BY principal_id")
    principals = cursor.fetchall()
    
    # Manuel ID'leri gerçek ID'lerle eşleştir
    # Bu basit bir yaklaşım - sırayla eşleştirir
    batch = []
    count = 0
    
    for manual_id, character_name in characters_data:
        # Manuel ID, principals listesindeki index'e karşılık gelir
        if manual_id <= len(principals):
            real_principal_id = principals[manual_id - 1]['principal_id']
            batch.append((real_principal_id, character_name))
            
            if len(batch) >= 1000:
                cursor.executemany(
                    """INSERT IGNORE INTO principal_characters 
                    (principal_id, character_name) 
                    VALUES (%s, %s)""",
                    batch
                )
                connection.commit()
                count += len(batch)
                print(f"  {count} kayıt yüklendi...", end='\r')
                batch = []
    
    if batch:
        cursor.executemany(
            """INSERT IGNORE INTO principal_characters 
            (principal_id, character_name) 
            VALUES (%s, %s)""",
            batch
        )
        connection.commit()
        count += len(batch)
    
    print(f"\n✓ {count} principal_characters kaydı yüklendi")

def load_people(cursor, filename, limit=None):
    """People/Names tablosunu yükle"""
    print("\n→ People tablosu yükleniyor...")
    
    with open(filename, 'r', encoding='utf-8') as f:
        next(f)  # Header'ı atla
        
        batch = []
        professions_data = []  # Professions için veri
        people_professions_data = []  # People-Professions ilişkisi için veri
        count = 0
        
        for line in f:
            if limit and count >= limit:
                break
                
            parts = line.strip().split('\t')
            if len(parts) >= 6:
                nconst = parts[0]
                primaryName = convert_value(parts[1])
                birthYear = convert_value(parts[2])
                deathYear = convert_value(parts[3])
                primaryProfession = convert_value(parts[4])  # Virgülle ayrılmış liste
                knownForTitles = convert_value(parts[5])  # Virgülle ayrılmış liste
                
                # İlk bilinen title'ı most_known_title olarak al
                most_known_title = None
                if knownForTitles:
                    titles_list = knownForTitles.split(',')
                    if titles_list:
                        most_known_title = titles_list[0].strip()
                
                batch.append((nconst, primaryName, birthYear, deathYear, most_known_title))
                
                # Professions'ı kaydet (sonra işlenecek)
                if primaryProfession:
                    prof_list = primaryProfession.split(',')
                    for prof in prof_list:
                        prof = prof.strip()
                        if prof:
                            professions_data.append(prof)
                            people_professions_data.append((nconst, prof))
                
                if len(batch) >= 1000:
                    cursor.executemany(
                        """INSERT IGNORE INTO people 
                        (nconst, primaryName, birthYear, deathYear, most_known_title) 
                        VALUES (%s, %s, %s, %s, %s)""",
                        batch
                    )
                    connection.commit()
                    count += len(batch)
                    print(f"  {count} kayıt yüklendi...", end='\r')
                    batch = []
        
        if batch:
            cursor.executemany(
                """INSERT IGNORE INTO people 
                (nconst, primaryName, birthYear, deathYear, most_known_title) 
                VALUES (%s, %s, %s, %s, %s)""",
                batch
            )
            connection.commit()
            count += len(batch)
    
    print(f"\n✓ {count} people kaydı yüklendi")
    print(f"  → Toplanan profession sayısı: {len(professions_data)}")
    print(f"  → Toplanan people-profession ilişki sayısı: {len(people_professions_data)}")
    return professions_data, people_professions_data

def load_professions(cursor, professions_data):
    """Professions tablosunu yükle"""
    print("\n→ Professions tablosu yükleniyor...")
    print(f"  Alınan veri sayısı: {len(professions_data)}")
    
    # Unique professions al
    unique_professions = list(set(professions_data))
    print(f"  Unique profession sayısı: {len(unique_professions)}")
    print(f"  İlk 5 örnek: {unique_professions[:5]}")
    
    count = 0
    successful_inserts = 0
    
    for profession in unique_professions:
        try:
            cursor.execute(
                """INSERT IGNORE INTO professions (profession_name) 
                VALUES (%s)""",
                (profession,)
            )
            if cursor.rowcount > 0:
                successful_inserts += 1
            count += 1
        except Exception as e:
            print(f"\n  ✗ Hata ({profession}): {e}")
    
    connection.commit()
    
    print(f"\n✓ {count} professions kaydı işlendi, {successful_inserts} başarılı insert")

def load_people_professions(cursor, people_professions_data):
    """People-Professions ilişki tablosunu yükle"""
    print("\n→ People_Professions ilişkileri yükleniyor...")
    print(f"  Alınan veri sayısı: {len(people_professions_data)}")
    
    # Debug: Tablodaki kayıt sayısını kontrol et
    cursor.execute("SELECT COUNT(*) as count FROM professions")
    count_result = cursor.fetchone()
    print(f"  Professions tablosundaki toplam kayıt: {count_result['count']}")
    
    # Profession name'leri ID'lere çevirmek için bir mapping oluştur
    cursor.execute("SELECT profession_id, profession_name FROM professions")
    all_profs = cursor.fetchall()
    print(f"  SELECT ile dönen kayıt sayısı: {len(all_profs)}")
    if len(all_profs) > 0:
        print(f"  İlk 5 profession: {all_profs[:5]}")
    
    # Dictionary'den doğru şekilde mapping oluştur
    prof_map = {prof['profession_name']: prof['profession_id'] for prof in all_profs}
    print(f"  Profession mapping sayısı: {len(prof_map)}")
    
    batch = []
    count = 0
    
    for nconst, profession_name in people_professions_data:
        if profession_name in prof_map:
            profession_id = prof_map[profession_name]
            batch.append((nconst, profession_id))
            
            if len(batch) >= 1000:
                cursor.executemany(
                    """INSERT IGNORE INTO people_professions 
                    (nconst, profession_id) 
                    VALUES (%s, %s)""",
                    batch
                )
                connection.commit()
                count += len(batch)
                print(f"  {count} kayıt yüklendi...", end='\r')
                batch = []
    
    if batch:
        cursor.executemany(
            """INSERT IGNORE INTO people_professions 
            (nconst, profession_id) 
            VALUES (%s, %s)""",
            batch
        )
        connection.commit()
        count += len(batch)
    
    print(f"\n✓ {count} people_professions kaydı yüklendi")

def load_akas(cursor, filename, limit=None):
    """Akas tablosunu yükle"""
    print("\n→ Akas tablosu yükleniyor...")
    
    with open(filename, 'r', encoding='utf-8') as f:
        next(f)  # Header'ı atla
        
        batch = []
        count = 0
        
        for line in f:
            if limit and count >= limit:
                break
                
            parts = line.strip().split('\t')
            if len(parts) >= 8:
                titleId = parts[0]  # tconst
                ordering = convert_value(parts[1])
                title = convert_value(parts[2])
                region = convert_value(parts[3])
                language = convert_value(parts[4])
                types = convert_value(parts[5])
                attributes = convert_value(parts[6])
                is_original_title = 1 if parts[7] == '1' else 0
                
                batch.append((titleId, ordering, title, region, language, 
                            types, attributes, is_original_title))
                
                if len(batch) >= 1000:
                    cursor.executemany(
                        """INSERT IGNORE INTO akas 
                        (titleId, ordering, title, region, language, 
                         types, attributes, is_original_title) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                        batch
                    )
                    connection.commit()
                    count += len(batch)
                    print(f"  {count} kayıt yüklendi...", end='\r')
                    batch = []
        
        if batch:
            cursor.executemany(
                """INSERT IGNORE INTO akas 
                (titleId, ordering, title, region, language, 
                 types, attributes, is_original_title) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                batch
            )
            connection.commit()
            count += len(batch)
    
    print(f"\n✓ {count} akas kaydı yüklendi")

def load_episodes(cursor, filename, limit=None):
    """Episodes tablosunu yükle"""
    print("\n→ Episodes tablosu yükleniyor...")
    
    with open(filename, 'r', encoding='utf-8') as f:
        next(f)  # Header'ı atla
        
        batch = []
        count = 0
        
        for line in f:
            if limit and count >= limit:
                break
                
            parts = line.strip().split('\t')
            if len(parts) >= 4:
                tconst = parts[0]
                parentTconst = parts[1]
                seasonNumber = convert_value(parts[2])
                episodeNumber = convert_value(parts[3])
                
                batch.append((tconst, parentTconst, seasonNumber, episodeNumber))
                
                if len(batch) >= 1000:
                    cursor.executemany(
                        """INSERT IGNORE INTO episodes 
                        (tconst, parentTconst, seasonNumber, episodeNumber) 
                        VALUES (%s, %s, %s, %s)""",
                        batch
                    )
                    connection.commit()
                    count += len(batch)
                    print(f"  {count} kayıt yüklendi...", end='\r')
                    batch = []
        
        if batch:
            cursor.executemany(
                """INSERT IGNORE INTO episodes 
                (tconst, parentTconst, seasonNumber, episodeNumber) 
                VALUES (%s, %s, %s, %s)""",
                batch
            )
            connection.commit()
            count += len(batch)
    
    print(f"\n✓ {count} episodes kaydı yüklendi")

def main():
    """Ana fonksiyon"""
    print("=" * 60)
    print("IMDb Non-Commercial Datasets Yükleme (HİBRİT MOD)")
    print("=" * 60)
    
    # Veri dizinini oluştur
    create_data_directory()
    
    # --- AYARLAR ---
    # People ve Principals tabloları çok şişkin olduğu için onları limitliyoruz.
    # Diğerlerini (Titles, Ratings, Akas) FULL yüklüyoruz ki eşleşme sorunu olmasın.
    HEAVY_TABLE_LIMIT = 50000  # İnsanlar ve Roller için 50.000 kayıt yeterli
    
    print(f"\n{'!' * 60}")
    print(f"AYAR: Titles, Ratings, Crew ve Akas -> FULL YÜKLENECEK (Limitsiz)")
    print(f"AYAR: People ve Principals -> {HEAVY_TABLE_LIMIT:,} kayıt ile sınırlanacak")
    print(f"{'!' * 60}\n")
    
    try:
        cursor = connection.cursor()
        
        # Tabloları temizle (Foreign key sırasına göre)
        print("\n→ Mevcut veriler temizleniyor...")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        tables_to_clear = [
            'people_professions',
            'professions',
            'principal_characters',
            'principals',
            'crew',
            'ratings',
            'akas',
            'episodes',
            'title_genres',
            'genres',
            'people',
            'titles'
        ]
        for table in tables_to_clear:
            cursor.execute(f"TRUNCATE TABLE {table}")
            print(f"  ✓ {table} temizlendi")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        connection.commit()
        print("✓ Tüm tablolar temizlendi\n")
        
        # 1. Titles (FULL YÜKLE - Eşleşmenin temeli burası)
        print("\n1. TITLES (FULL)")
        filename = download_dataset('title.basics', DATASETS['title.basics'])
        title_genres_data = []
        if filename:
            # LIMIT YOK (None)
            title_genres_data = load_titles(cursor, filename, limit=None)
        
        # 1a. Genres
        print("\n1a. GENRES")
        if title_genres_data:
            load_genres(cursor, title_genres_data)
        
        # 1b. Title-Genres İlişkileri
        print("\n1b. TITLE-GENRES")
        if title_genres_data:
            load_title_genres(cursor, title_genres_data)
        
        # 2. Ratings (FULL YÜKLE - İstatistikler için şart)
        print("\n2. RATINGS (FULL)")
        filename = download_dataset('title.ratings', DATASETS['title.ratings'])
        if filename:
            load_ratings(cursor, filename, limit=None)
        
        # 3. Crew (FULL YÜKLE - Yönetmenler önemli)
        print("\n3. CREW (FULL)")
        filename = download_dataset('title.crew', DATASETS['title.crew'])
        if filename:
            load_crew(cursor, filename, limit=None)
        
        # 4. People (LİMİTLİ - Çok ağır tablo)
        print(f"\n4. PEOPLE (LİMİTLİ: {HEAVY_TABLE_LIMIT})")
        filename = download_dataset('name.basics', DATASETS['name.basics'])
        professions_data = []
        people_professions_data = []
        if filename:
            professions_data, people_professions_data = load_people(cursor, filename, limit=HEAVY_TABLE_LIMIT)
        
        # 4a. Professions
        print("\n4a. PROFESSIONS")
        if professions_data:
            load_professions(cursor, professions_data)
        
        # 4b. People-Professions
        print("\n4b. PEOPLE-PROFESSIONS")
        if people_professions_data:
            load_people_professions(cursor, people_professions_data)
        
        # 5. Principals (LİMİTLİ - En ağır tablo)
        print(f"\n5. PRINCIPALS (LİMİTLİ: {HEAVY_TABLE_LIMIT})")
        filename = download_dataset('title.principals', DATASETS['title.principals'])
        characters_data = []
        if filename:
            characters_data = load_principals(cursor, filename, limit=HEAVY_TABLE_LIMIT)
        
        # 5a. Principal Characters
        print("\n5a. PRINCIPAL_CHARACTERS")
        if characters_data:
            load_principal_characters(cursor, characters_data)

        # 6. Akas (FULL YÜKLE - Yerelleştirme için şart)
        print("\n6. AKAS (FULL)")
        filename = download_dataset('title.akas', DATASETS['title.akas'])
        if filename:
            load_akas(cursor, filename, limit=None)
        
        print("\n" + "=" * 60)
        print("✓ Tüm veriler başarıyla yüklendi!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Hata oluştu: {e}")
        connection.rollback()
    finally:
        cursor.close()

# Dosyanın en sonuna bunu yapıştır:

if __name__ == "__main__":
    start_time = time.time()
    main()
    elapsed = time.time() - start_time
    print(f"\nToplam süre: {elapsed:.2f} saniye ({elapsed/60:.2f} dakika)")