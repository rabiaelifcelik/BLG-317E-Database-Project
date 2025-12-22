-- IMDb Database Schema
-- Bu script tüm tabloları oluşturur

-- Veritabanını seç (config.py'deki veritabanı adını kullanın)
-- USE your_database_name;

-- Mevcut tabloları temizle (dikkatli kullanın!)
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS people_professions;
DROP TABLE IF EXISTS professions;
DROP TABLE IF EXISTS principal_characters;
DROP TABLE IF EXISTS principals;
DROP TABLE IF EXISTS crew;
DROP TABLE IF EXISTS ratings;
DROP TABLE IF EXISTS akas;
DROP TABLE IF EXISTS episodes;
DROP TABLE IF EXISTS title_genres;
DROP TABLE IF EXISTS genres;
DROP TABLE IF EXISTS people;
DROP TABLE IF EXISTS titles;
DROP TABLE IF EXISTS users;

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================
-- 1. USERS TABLE (Kullanıcı Yönetimi)
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 2. TITLES TABLE (Ana Film/Dizi Tablosu)
-- ============================================
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 3. GENRES TABLE (Normalized Genre Table)
-- ============================================
CREATE TABLE IF NOT EXISTS genres (
    genre_id INT NOT NULL AUTO_INCREMENT,
    genre_name VARCHAR(50) NOT NULL,
    PRIMARY KEY (genre_id),
    UNIQUE KEY idx_genre_name (genre_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 4. TITLE_GENRES TABLE (Many-to-Many Junction)
-- ============================================
CREATE TABLE IF NOT EXISTS title_genres (
    tconst VARCHAR(20) NOT NULL,
    genre_id INT NOT NULL,
    PRIMARY KEY (tconst, genre_id),
    CONSTRAINT fk_tg_title FOREIGN KEY (tconst) REFERENCES titles (tconst) ON DELETE CASCADE,
    CONSTRAINT fk_tg_genre FOREIGN KEY (genre_id) REFERENCES genres (genre_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 5. RATINGS TABLE (Film Puanları)
-- ============================================
CREATE TABLE IF NOT EXISTS ratings (
    title_id VARCHAR(20) NOT NULL,
    average_rating DECIMAL(3,1) DEFAULT NULL,
    num_votes INT DEFAULT NULL,
    PRIMARY KEY (title_id),
    CONSTRAINT fk_ratings_title FOREIGN KEY (title_id) REFERENCES titles (tconst) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 6. CREW TABLE (Yönetmen ve Senarist Bilgileri)
-- ============================================
CREATE TABLE IF NOT EXISTS crew (
    tconst VARCHAR(20) NOT NULL,
    directors TEXT,
    writers TEXT,
    PRIMARY KEY (tconst),
    CONSTRAINT fk_crew_title FOREIGN KEY (tconst) REFERENCES titles (tconst) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 7. PEOPLE TABLE (Kişiler - Oyuncu, Yönetmen, vs.)
-- ============================================
CREATE TABLE IF NOT EXISTS people (
    nconst VARCHAR(20) NOT NULL,
    primaryName VARCHAR(200) DEFAULT NULL,
    birthYear INT DEFAULT NULL,
    deathYear INT DEFAULT NULL,
    most_known_title VARCHAR(20) DEFAULT NULL,
    PRIMARY KEY (nconst),
    KEY idx_name (primaryName(100)),
    CONSTRAINT fk_people_most_known_title FOREIGN KEY (most_known_title) REFERENCES titles (tconst) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 8. PROFESSIONS TABLE (Normalized Professions)
-- ============================================
CREATE TABLE IF NOT EXISTS professions (
    profession_id INT NOT NULL AUTO_INCREMENT,
    profession_name VARCHAR(100) NOT NULL,
    PRIMARY KEY (profession_id),
    UNIQUE KEY idx_prof_name (profession_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 9. PEOPLE_PROFESSIONS TABLE (Many-to-Many Junction)
-- ============================================
CREATE TABLE IF NOT EXISTS people_professions (
    nconst VARCHAR(20) NOT NULL,
    profession_id INT NOT NULL,
    PRIMARY KEY (nconst, profession_id),
    CONSTRAINT fk_pp_person FOREIGN KEY (nconst) REFERENCES people (nconst) ON DELETE CASCADE,
    CONSTRAINT fk_pp_profession FOREIGN KEY (profession_id) REFERENCES professions (profession_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 10. PRINCIPALS TABLE (Oyuncu-Film İlişkisi)
-- ============================================
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 11. PRINCIPAL_CHARACTERS TABLE (Karakter İsimleri)
-- ============================================
CREATE TABLE IF NOT EXISTS principal_characters (
    character_id INT AUTO_INCREMENT,
    principal_id INT NOT NULL,
    character_name VARCHAR(500) DEFAULT NULL,
    PRIMARY KEY (character_id),
    KEY idx_principal (principal_id),
    CONSTRAINT fk_pc_principal FOREIGN KEY (principal_id) REFERENCES principals (principal_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 12. AKAS TABLE (Alternatif Başlıklar)
-- ============================================
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 13. EPISODES TABLE (Dizi Bölümleri)
-- ============================================
CREATE TABLE IF NOT EXISTS episodes (
    tconst VARCHAR(20) NOT NULL,
    parentTconst VARCHAR(20) NOT NULL,
    seasonNumber INT DEFAULT NULL,
    episodeNumber INT DEFAULT NULL,
    PRIMARY KEY (tconst),
    KEY idx_parent (parentTconst),
    CONSTRAINT fk_episodes_title FOREIGN KEY (tconst) REFERENCES titles (tconst) ON DELETE CASCADE,
    CONSTRAINT fk_episodes_parent FOREIGN KEY (parentTconst) REFERENCES titles (tconst) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- İlk Admin Kullanıcısını Oluştur (Opsiyonel)
-- ============================================
-- Şifre: admin123 (Güvenlik için değiştirin!)
-- INSERT INTO users (username, password, is_admin) 
-- VALUES ('admin', 'scrypt:32768:8:1$YOUR_HASHED_PASSWORD', TRUE);

-- ============================================
-- Tablo Oluşturma Tamamlandı
-- ============================================
SELECT 'Tüm tablolar başarıyla oluşturuldu!' AS Status;
