from config import connection
import pymysql

def setup_database():
    # SQL scriptini bir string olarak tanımlıyoruz
    sql_script = """
    SET FOREIGN_KEY_CHECKS = 0;

    DROP TABLE IF EXISTS users, principal_characters, principals, crew_directors, 
                     crew_writers, crew, title_genres, genres, people_professions, 
                     professions, episodes, akas, ratings, people, titles;

    SET FOREIGN_KEY_CHECKS = 1;

    CREATE TABLE titles (
        tconst VARCHAR(20) PRIMARY KEY,
        titleType VARCHAR(50),
        primaryTitle VARCHAR(500),
        originalTitle VARCHAR(500),
        isAdult TINYINT(1),
        startYear INT,
        endYear INT,
        runtimeMinutes INT
    );

    CREATE TABLE people (
        nconst VARCHAR(20) PRIMARY KEY,
        primaryName VARCHAR(200),
        birthYear INT,
        deathYear INT,
        most_known_title VARCHAR(20),
        FOREIGN KEY (most_known_title) REFERENCES titles(tconst) ON DELETE SET NULL
    );

    CREATE TABLE genres (
        genre_id INT AUTO_INCREMENT PRIMARY KEY,
        genre_name VARCHAR(50) UNIQUE
    );

    CREATE TABLE title_genres (
        tconst VARCHAR(20),
        genre_id INT,
        PRIMARY KEY (tconst, genre_id),
        FOREIGN KEY (tconst) REFERENCES titles(tconst) ON DELETE CASCADE,
        FOREIGN KEY (genre_id) REFERENCES genres(genre_id) ON DELETE CASCADE
    );

    CREATE TABLE professions (
        profession_id INT AUTO_INCREMENT PRIMARY KEY,
        profession_name VARCHAR(100) UNIQUE
    );

    CREATE TABLE people_professions (
        nconst VARCHAR(20),
        profession_id INT,
        PRIMARY KEY (nconst, profession_id),
        FOREIGN KEY (nconst) REFERENCES people(nconst) ON DELETE CASCADE,
        FOREIGN KEY (profession_id) REFERENCES professions(profession_id) ON DELETE CASCADE
    );

    CREATE TABLE crew (
        tconst VARCHAR(20) PRIMARY KEY,
        FOREIGN KEY (tconst) REFERENCES titles(tconst) ON DELETE CASCADE
    );

    CREATE TABLE crew_directors (
        tconst VARCHAR(20),
        nconst VARCHAR(20),
        PRIMARY KEY (tconst, nconst),
        FOREIGN KEY (tconst) REFERENCES crew(tconst) ON DELETE CASCADE,
        FOREIGN KEY (nconst) REFERENCES people(nconst) ON DELETE CASCADE
    );

    CREATE TABLE crew_writers (
        tconst VARCHAR(20),
        nconst VARCHAR(20),
        PRIMARY KEY (tconst, nconst),
        FOREIGN KEY (tconst) REFERENCES crew(tconst) ON DELETE CASCADE,
        FOREIGN KEY (nconst) REFERENCES people(nconst) ON DELETE CASCADE
    );

    CREATE TABLE principals (
        principal_id INT AUTO_INCREMENT PRIMARY KEY,
        tconst VARCHAR(20),
        ordering INT,
        nconst VARCHAR(20),
        category VARCHAR(100),
        job TEXT,
        FOREIGN KEY (tconst) REFERENCES titles(tconst) ON DELETE CASCADE,
        FOREIGN KEY (nconst) REFERENCES people(nconst) ON DELETE CASCADE
    );

    CREATE TABLE principal_characters (
        character_id INT AUTO_INCREMENT PRIMARY KEY,
        principal_id INT,
        character_name VARCHAR(500),
        FOREIGN KEY (principal_id) REFERENCES principals(principal_id) ON DELETE CASCADE
    );

    CREATE TABLE ratings (
        rating_id INT AUTO_INCREMENT PRIMARY KEY,
        title_id VARCHAR(20),
        average_rating DECIMAL(3,1),
        num_votes INT,
        FOREIGN KEY (title_id) REFERENCES titles(tconst) ON DELETE CASCADE
    );

    CREATE TABLE akas (
        titleId VARCHAR(20),
        ordering INT,
        title VARCHAR(1000),
        region VARCHAR(10),
        language VARCHAR(10),
        types VARCHAR(100),
        attributes TEXT,
        isOriginalTitle TINYINT(1),
        PRIMARY KEY (titleId, ordering),
        FOREIGN KEY (titleId) REFERENCES titles(tconst) ON DELETE CASCADE
    );

    CREATE TABLE episodes (
        tconst VARCHAR(20) PRIMARY KEY,
        parentTconst VARCHAR(20),
        seasonNumber INT,
        episodeNumber INT,
        FOREIGN KEY (tconst) REFERENCES titles(tconst) ON DELETE CASCADE,
        FOREIGN KEY (parentTconst) REFERENCES titles(tconst) ON DELETE CASCADE
    );

    CREATE TABLE users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        is_admin TINYINT(1) DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    try:
        connection.ping(reconnect=True)
        with connection.cursor() as cursor:
            # SQL scriptini noktalı virgüllere göre bölüp sırayla çalıştırıyoruz
            statements = sql_script.split(';')
            for statement in statements:
                if statement.strip():
                    cursor.execute(statement)
            
            connection.commit()
            print("✅ Veri tabanı başarıyla sıfırlandı ve tüm tablolar oluşturuldu.")
            
    except pymysql.MySQLError as e:
        print(f"❌ Hata oluştu: {e}")
        connection.rollback()
    finally:
        # Bağlantıyı kapatmıyoruz çünkü diğer işlemler için gerekebilir 
        # ama istersen connection.close() ekleyebilirsin.
        pass

if __name__ == "__main__":
    setup_database()