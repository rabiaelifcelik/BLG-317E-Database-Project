"""
IMDb Veritabanı Tablo Oluşturma Scripti
Bu script tüm tabloları otomatik olarak oluşturur
"""

import pymysql
from config import connection

def create_all_tables():
    """Tüm tabloları oluştur"""
    print("=" * 60)
    print("IMDb Veritabanı Tablo Oluşturma")
    print("=" * 60)
    
    try:
        cursor = connection.cursor()
        
        # Foreign key kontrolünü devre dışı bırak
        print("\n→ Foreign key kontrolü devre dışı bırakılıyor...")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        # Mevcut tabloları sil (dikkatli!)
        print("→ Eski tablolar siliniyor...")
        tables = [
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
            'titles',
            'users'
        ]
        
        for table in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            print(f"  ✓ {table} silindi")
        
        # Foreign key kontrolünü aktif et
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        print("→ Foreign key kontrolü aktif edildi\n")
        
        # 1. USERS TABLE
        print("1. USERS tablosu oluşturuluyor...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("  ✓ Users tablosu oluşturuldu")
        
        # 2. TITLES TABLE
        print("\n2. TITLES tablosu oluşturuluyor...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS titles (
                tconst VARCHAR(20) NOT NULL,
                titleType VARCHAR(50) DEFAULT NULL,
                primaryTitle VARCHAR(500) DEFAULT NULL,
                originalTitle VARCHAR(500) DEFAULT NULL,
                isAdult TINYINT(1) DEFAULT 0,
                startYear INT DEFAULT NULL,
                endYear INT DEFAULT NULL,
                runtimeMinutes INT DEFAULT NULL,
                PRIMARY KEY (tconst),
                KEY idx_title (primaryTitle(100)),
                KEY idx_year (startYear),
                KEY idx_type (titleType)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("  ✓ Titles tablosu oluşturuldu")
        
        # 3. GENRES TABLE
        print("\n3. GENRES tablosu oluşturuluyor...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS genres (
                genre_id INT NOT NULL AUTO_INCREMENT,
                genre_name VARCHAR(50) NOT NULL,
                PRIMARY KEY (genre_id),
                UNIQUE KEY idx_genre_name (genre_name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("  ✓ Genres tablosu oluşturuldu")
        
        # 4. TITLE_GENRES TABLE
        print("\n4. TITLE_GENRES tablosu oluşturuluyor...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS title_genres (
                tconst VARCHAR(20) NOT NULL,
                genre_id INT NOT NULL,
                PRIMARY KEY (tconst, genre_id),
                CONSTRAINT fk_tg_title FOREIGN KEY (tconst) REFERENCES titles (tconst) ON DELETE CASCADE,
                CONSTRAINT fk_tg_genre FOREIGN KEY (genre_id) REFERENCES genres (genre_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("  ✓ Title_Genres tablosu oluşturuldu")
        
        # 5. RATINGS TABLE
        print("\n5. RATINGS tablosu oluşturuluyor...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ratings (
                title_id VARCHAR(20) NOT NULL,
                average_rating DECIMAL(3,1) DEFAULT NULL,
                num_votes INT DEFAULT NULL,
                PRIMARY KEY (title_id),
                CONSTRAINT fk_ratings_title FOREIGN KEY (title_id) REFERENCES titles (tconst) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("  ✓ Ratings tablosu oluşturuldu")
        
        # 6. CREW TABLE
        print("\n6. CREW tablosu oluşturuluyor...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crew (
                tconst VARCHAR(20) NOT NULL,
                directors TEXT,
                writers TEXT,
                PRIMARY KEY (tconst),
                CONSTRAINT fk_crew_title FOREIGN KEY (tconst) REFERENCES titles (tconst) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("  ✓ Crew tablosu oluşturuldu")
        
        # 7. PEOPLE TABLE
        print("\n7. PEOPLE tablosu oluşturuluyor...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS people (
                nconst VARCHAR(20) NOT NULL,
                primaryName VARCHAR(200) DEFAULT NULL,
                birthYear INT DEFAULT NULL,
                deathYear INT DEFAULT NULL,
                most_known_title VARCHAR(20) DEFAULT NULL,
                PRIMARY KEY (nconst),
                KEY idx_name (primaryName(100)),
                CONSTRAINT fk_people_most_known_title FOREIGN KEY (most_known_title) REFERENCES titles (tconst) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("  ✓ People tablosu oluşturuldu")
        
        # 8. PROFESSIONS TABLE
        print("\n8. PROFESSIONS tablosu oluşturuluyor...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS professions (
                profession_id INT NOT NULL AUTO_INCREMENT,
                profession_name VARCHAR(100) NOT NULL,
                PRIMARY KEY (profession_id),
                UNIQUE KEY idx_prof_name (profession_name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("  ✓ Professions tablosu oluşturuldu")
        
        # 9. PEOPLE_PROFESSIONS TABLE
        print("\n9. PEOPLE_PROFESSIONS tablosu oluşturuluyor...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS people_professions (
                nconst VARCHAR(20) NOT NULL,
                profession_id INT NOT NULL,
                PRIMARY KEY (nconst, profession_id),
                CONSTRAINT fk_pp_person FOREIGN KEY (nconst) REFERENCES people (nconst) ON DELETE CASCADE,
                CONSTRAINT fk_pp_profession FOREIGN KEY (profession_id) REFERENCES professions (profession_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("  ✓ People_Professions tablosu oluşturuldu")
        
        # 10. PRINCIPALS TABLE
        print("\n10. PRINCIPALS tablosu oluşturuluyor...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS principals (
                principal_id INT AUTO_INCREMENT,
                tconst VARCHAR(20) NOT NULL,
                ordering INT DEFAULT NULL,
                nconst VARCHAR(20) NOT NULL,
                category VARCHAR(100) DEFAULT NULL,
                job TEXT,
                PRIMARY KEY (principal_id),
                KEY idx_tconst (tconst),
                KEY idx_nconst (nconst),
                CONSTRAINT fk_principals_title FOREIGN KEY (tconst) REFERENCES titles (tconst) ON DELETE CASCADE,
                CONSTRAINT fk_principals_person FOREIGN KEY (nconst) REFERENCES people (nconst) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("  ✓ Principals tablosu oluşturuldu")
        
        # 11. PRINCIPAL_CHARACTERS TABLE
        print("\n11. PRINCIPAL_CHARACTERS tablosu oluşturuluyor...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS principal_characters (
                character_id INT AUTO_INCREMENT,
                principal_id INT NOT NULL,
                character_name VARCHAR(500) DEFAULT NULL,
                PRIMARY KEY (character_id),
                KEY idx_principal (principal_id),
                CONSTRAINT fk_pc_principal FOREIGN KEY (principal_id) REFERENCES principals (principal_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("  ✓ Principal_Characters tablosu oluşturuldu")
        
        # 12. AKAS TABLE
        print("\n12. AKAS tablosu oluşturuluyor...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS akas (
                aka_id INT AUTO_INCREMENT,
                titleId VARCHAR(20) NOT NULL,
                ordering INT DEFAULT NULL,
                title VARCHAR(1000) DEFAULT NULL,
                region VARCHAR(10) DEFAULT NULL,
                language VARCHAR(10) DEFAULT NULL,
                types VARCHAR(100) DEFAULT NULL,
                attributes TEXT,
                isOriginalTitle TINYINT(1) DEFAULT 0,
                PRIMARY KEY (aka_id),
                KEY idx_titleId (titleId),
                KEY idx_region (region),
                CONSTRAINT fk_akas_title FOREIGN KEY (titleId) REFERENCES titles (tconst) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("  ✓ Akas tablosu oluşturuldu")
        
        # 13. EPISODES TABLE
        print("\n13. EPISODES tablosu oluşturuluyor...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS episodes (
                tconst VARCHAR(20) NOT NULL,
                parentTconst VARCHAR(20) NOT NULL,
                seasonNumber INT DEFAULT NULL,
                episodeNumber INT DEFAULT NULL,
                PRIMARY KEY (tconst),
                KEY idx_parent (parentTconst),
                CONSTRAINT fk_episodes_title FOREIGN KEY (tconst) REFERENCES titles (tconst) ON DELETE CASCADE,
                CONSTRAINT fk_episodes_parent FOREIGN KEY (parentTconst) REFERENCES titles (tconst) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("  ✓ Episodes tablosu oluşturuldu")
        
        connection.commit()
        
        print("\n" + "=" * 60)
        print("✓ TÜM TABLOLAR BAŞARIYLA OLUŞTURULDU!")
        print("=" * 60)
        
        # Tablo sayısını kontrol et
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"\nToplam {len(tables)} tablo oluşturuldu:")
        for table in tables:
            table_name = list(table.values())[0]
            print(f"  ✓ {table_name}")
        
        print("\n" + "=" * 60)
        print("Şimdi 'python load_imdb_data.py' komutuyla verileri yükleyebilirsiniz")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ HATA: {e}")
        connection.rollback()
    finally:
        cursor.close()

if __name__ == "__main__":
    create_all_tables()
