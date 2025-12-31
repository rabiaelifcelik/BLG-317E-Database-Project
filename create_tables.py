from config import connection
import pymysql

def setup_database():
    # 1215 hatasını önlemek için ENGINE ve CHARSET'i her tabloda sabitliyoruz
    table_options = "ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"

    sql_statements = [
        "SET FOREIGN_KEY_CHECKS = 0;",
        
        # Tabloları tek tek silmek daha güvenlidir
        "DROP TABLE IF EXISTS principal_characters;",
        "DROP TABLE IF EXISTS principals;",
        "DROP TABLE IF EXISTS crew_directors;",
        "DROP TABLE IF EXISTS crew_writers;",
        "DROP TABLE IF EXISTS crew;",
        "DROP TABLE IF EXISTS title_genres;",
        "DROP TABLE IF EXISTS genres;",
        "DROP TABLE IF EXISTS people_professions;",
        "DROP TABLE IF EXISTS professions;",
        "DROP TABLE IF EXISTS episodes;",
        "DROP TABLE IF EXISTS akas;",
        "DROP TABLE IF EXISTS ratings;",
        "DROP TABLE IF EXISTS people;",
        "DROP TABLE IF EXISTS titles;",
        "DROP TABLE IF EXISTS users;",

        # 1. TITLES
        f"""CREATE TABLE titles (
            tconst VARCHAR(20) PRIMARY KEY,
            titleType VARCHAR(50),
            primaryTitle VARCHAR(500),
            originalTitle VARCHAR(500),
            isAdult TINYINT(1),
            startYear INT,
            endYear INT,
            runtimeMinutes INT
        ) {table_options};""",

        # 2. PEOPLE
        f"""CREATE TABLE people (
            nconst VARCHAR(20) PRIMARY KEY,
            primaryName VARCHAR(200),
            birthYear INT,
            deathYear INT,
            most_known_title VARCHAR(20),
            FOREIGN KEY (most_known_title) REFERENCES titles(tconst) ON DELETE SET NULL
        ) {table_options};""",

        # 3. GENRES & TITLE_GENRES
        f"CREATE TABLE genres (genre_id INT AUTO_INCREMENT PRIMARY KEY, genre_name VARCHAR(50) UNIQUE) {table_options};",
        f"""CREATE TABLE title_genres (
            tconst VARCHAR(20),
            genre_id INT,
            PRIMARY KEY (tconst, genre_id),
            FOREIGN KEY (tconst) REFERENCES titles(tconst) ON DELETE CASCADE,
            FOREIGN KEY (genre_id) REFERENCES genres(genre_id) ON DELETE CASCADE
        ) {table_options};""",

        # 4. PROFESSIONS & PEOPLE_PROFESSIONS
        f"CREATE TABLE professions (profession_id INT AUTO_INCREMENT PRIMARY KEY, profession_name VARCHAR(100) UNIQUE) {table_options};",
        f"""CREATE TABLE people_professions (
            nconst VARCHAR(20),
            profession_id INT,
            PRIMARY KEY (nconst, profession_id),
            FOREIGN KEY (nconst) REFERENCES people(nconst) ON DELETE CASCADE,
            FOREIGN KEY (profession_id) REFERENCES professions(profession_id) ON DELETE CASCADE
        ) {table_options};""",

        # 5. CREW & SUB-TABLES
        f"CREATE TABLE crew (tconst VARCHAR(20) PRIMARY KEY, FOREIGN KEY (tconst) REFERENCES titles(tconst) ON DELETE CASCADE) {table_options};",
        f"""CREATE TABLE crew_directors (
            tconst VARCHAR(20),
            nconst VARCHAR(20),
            PRIMARY KEY (tconst, nconst),
            FOREIGN KEY (tconst) REFERENCES crew(tconst) ON DELETE CASCADE,
            FOREIGN KEY (nconst) REFERENCES people(nconst) ON DELETE CASCADE
        ) {table_options};""",
        f"""CREATE TABLE crew_writers (
            tconst VARCHAR(20),
            nconst VARCHAR(20),
            PRIMARY KEY (tconst, nconst),
            FOREIGN KEY (tconst) REFERENCES crew(tconst) ON DELETE CASCADE,
            FOREIGN KEY (nconst) REFERENCES people(nconst) ON DELETE CASCADE
        ) {table_options};""",

        # 6. PRINCIPALS & CHARACTERS
        f"""CREATE TABLE principals (
            principal_id INT AUTO_INCREMENT PRIMARY KEY,
            tconst VARCHAR(20),
            ordering INT,
            nconst VARCHAR(20),
            category VARCHAR(100),
            job TEXT,
            FOREIGN KEY (tconst) REFERENCES titles(tconst) ON DELETE CASCADE,
            FOREIGN KEY (nconst) REFERENCES people(nconst) ON DELETE CASCADE
        ) {table_options};""",
        f"""CREATE TABLE principal_characters (
            character_id INT AUTO_INCREMENT PRIMARY KEY,
            principal_id INT,
            character_name VARCHAR(500),
            FOREIGN KEY (principal_id) REFERENCES principals(principal_id) ON DELETE CASCADE
        ) {table_options};""",

        # 7. RATINGS, AKAS, EPISODES
        f"""CREATE TABLE ratings (
            rating_id INT AUTO_INCREMENT PRIMARY KEY,
            title_id VARCHAR(20),
            average_rating DECIMAL(3,1),
            num_votes INT,
            FOREIGN KEY (title_id) REFERENCES titles(tconst) ON DELETE CASCADE
        ) {table_options};""",
        f"""CREATE TABLE akas (
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
        ) {table_options};""",
        f"""CREATE TABLE episodes (
            tconst VARCHAR(20) PRIMARY KEY,
            parentTconst VARCHAR(20),
            seasonNumber INT,
            episodeNumber INT,
            FOREIGN KEY (tconst) REFERENCES titles(tconst) ON DELETE CASCADE,
            FOREIGN KEY (parentTconst) REFERENCES titles(tconst) ON DELETE CASCADE
        ) {table_options};""",

        # 8. USERS
        f"""CREATE TABLE users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            is_admin TINYINT(1) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) {table_options};""",

        "SET FOREIGN_KEY_CHECKS = 1;"
    ]

    try:
        connection.ping(reconnect=True)
        with connection.cursor() as cursor:
            for statement in sql_statements:
                cursor.execute(statement)
            connection.commit()
            print("✅ Veri tabanı şeması hatasız şekilde oluşturuldu.")
    except Exception as e:
        print(f"❌ Kritik Hata: {e}")
        connection.rollback()

if __name__ == "__main__":
    setup_database()