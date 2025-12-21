from titles import Titles
from config import connection
import json
import pymysql

class Database:
    def __init__(self):
        self.titles = {}
        self._last_title_key = 0


    def add_title(self, title):
        self._last_title_key += 1
        self.titles[self._last_title_key] = title
        return self._last_title_key
    
    def del_title(self, title_key):
        if title_key in self.titles:
            del self.titles[title_key]

    def get_title(self, title_key):
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            # Handle connection failure if ping fails
            print("Failed to reconnect to the database.")
            
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM titles WHERE tconst = '{title_key}'")
            title = cursor.fetchone()

        if title is not None or "":
            return title
        else:
            print("Not found in database.")

        # if title_key in self.titles:
        #     return self.titles[title_key]
        # else:
        #     print("title not found in database.")


    def get_titles(self, limit=200, search_title=None):
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            # Handle connection failure if ping fails
            print("Failed to reconnect to the database.")

        with connection.cursor() as cursor:
            if search_title is None:
                cursor.execute(f"SELECT * FROM titles LIMIT {limit}")

            else:
                query = """
                    SELECT * FROM titles WHERE titles.primaryName LIKE '%%s%';
                """
                cursor.execute(query, (search_title))
            titles = cursor.fetchall()

        return titles
    

    def get_crew(self,title_id):
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            # Handle connection failure if ping fails
            print("Failed to reconnect to the database.")

        with connection.cursor() as cursor:
            #query = f"SELECT * FROM crew WHERE tconst = '{title_id}'" 

            query = f"""SELECT
                            c.tconst,

                            (
                                SELECT JSON_ARRAYAGG(
                                    JSON_OBJECT(
                                        'nconst', p.nconst,
                                        'primaryName', p.primaryName
                                    )
                                )
                                FROM people p
                                WHERE FIND_IN_SET(p.nconst, c.directors)
                            ) AS directors,

                            (
                                SELECT JSON_ARRAYAGG(
                                    JSON_OBJECT(
                                        'nconst', p.nconst,
                                        'primaryName', p.primaryName
                                    )
                                )
                                FROM people p
                                WHERE FIND_IN_SET(p.nconst, c.writers)
                            ) AS writers

                        FROM crew c LEFT JOIN titles t ON c.tconst = t.tconst
                        WHERE t.tconst = '{title_id}';
                        """
            
            cursor.execute(query)
            crew = cursor.fetchone()
            
            crew['directors'] = json.loads(crew['directors']) if crew['directors'] else []
            crew['writers'] = json.loads(crew['writers']) if crew['writers'] else []

            print(crew['directors'], crew['writers'])
        
        return crew
    
    def add_title(self, title_type, primaryTitle, originalTitle, isAdult, startYear, endYear, runtimeMinutes, genres ):
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            # Handle connection failure if ping fails
            print("Failed to reconnect to the database.")

        with connection.cursor() as cursor:
            cursor.execute("SELECT MAX(CAST(SUBSTRING(nconst, 3) AS UNSIGNED)) FROM people WHERE nconst LIKE 't%'")
            max_id = cursor.fetchone()
            new_id = f"t{int(max_id['MAX(CAST(SUBSTRING(nconst, 3) AS UNSIGNED))']) + 1 if max_id else 1:07d}"
            query = """
                INSERT INTO people (tconst, primaryTitle, originalTitle, isAdult, startYear, endYear, runtimeMinutes, genres)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (new_id, title_type, primaryTitle, originalTitle, isAdult, startYear, endYear, runtimeMinutes, genres))
            connection.commit()
        
        return new_id



    def get_principals(self):
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            # Handle connection failure if ping fails
            print("Failed to reconnect to the database.")

        with connection.cursor() as cursor:
            query = """
                SELECT 
                    p.principal_id,
                    p.tconst,
                    t.primaryTitle as title_name,
                    p.ordering,
                    p.nconst,
                    pe.primaryName as person_name,
                    p.category,
                    p.job,
                    p.characters
                FROM principals p
                LEFT JOIN titles t ON p.tconst = t.tconst
                LEFT JOIN people pe ON p.nconst = pe.nconst
                ORDER BY p.principal_id DESC
                LIMIT 200
            """
            cursor.execute(query)
            principals = cursor.fetchall()
        return principals
    
    def get_principal(self, principal_id):
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            # Handle connection failure if ping fails
            print("Failed to reconnect to the database.")

        with connection.cursor() as cursor:
            query = """
                SELECT 
                    p.principal_id,
                    p.tconst,
                    t.primaryTitle as title_name,
                    t.startYear as title_year,
                    p.ordering,
                    p.nconst,
                    pe.primaryName as person_name,
                    pe.birthYear as person_birth_year,
                    pe.primaryProfession as person_profession,
                    p.category,
                    p.job,
                    p.characters
                FROM principals p
                LEFT JOIN titles t ON p.tconst = t.tconst
                LEFT JOIN people pe ON p.nconst = pe.nconst
                WHERE p.principal_id = %s
            """
            cursor.execute(query, (principal_id,))
            principal = cursor.fetchone()
        
        if principal is not None:
            return principal
        else:
            print("Principal not found in database.")
            return None
    
    def add_principal(self, title_id, ordering, name_id, category, job, characters):
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            # Handle connection failure if ping fails
            print("Failed to reconnect to the database.")

        with connection.cursor() as cursor:
            query = """
                INSERT INTO principals (tconst, ordering, nconst, category, job, characters) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (title_id, ordering, name_id, category, job, characters))
            connection.commit()
        return True
    
    def update_principal(self, principal_id, title_id, ordering, name_id, category, job, characters):
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            print("Failed to reconnect to the database.")

        with connection.cursor() as cursor:
            query = """
                UPDATE principals 
                SET tconst = %s, ordering = %s, nconst = %s, category = %s, job = %s, characters = %s
                WHERE principal_id = %s
            """
            cursor.execute(query, (title_id, ordering, name_id, category, job, characters, principal_id))
            connection.commit()
        return True
    
    def delete_principal(self, principal_id):
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            print("Failed to reconnect to the database.")

        with connection.cursor() as cursor:
            query = "DELETE FROM principals WHERE principal_id = %s"
            cursor.execute(query, (principal_id,))
            connection.commit()
        return True
    
    def get_principals_statistics(self):
        """Complex query with nested query, 4+ table join, and GROUP BY for principals statistics"""
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            print("Failed to reconnect to the database.")

        with connection.cursor() as cursor:
            query = """
                SELECT 
                    p.category,
                    COUNT(DISTINCT p.principal_id) as total_principals,
                    COUNT(DISTINCT p.tconst) as total_titles,
                    COUNT(DISTINCT p.nconst) as total_people,
                    AVG(r.average_rating) as avg_title_rating,
                    GROUP_CONCAT(DISTINCT t.genres SEPARATOR ', ') as all_genres,
                    (
                        SELECT pe.primaryName 
                        FROM principals p2
                        JOIN people pe ON p2.nconst = pe.nconst
                        WHERE p2.category = p.category
                        GROUP BY pe.nconst, pe.primaryName
                        ORDER BY COUNT(p2.principal_id) DESC
                        LIMIT 1
                    ) as most_active_person
                FROM principals p
                LEFT JOIN titles t ON p.tconst = t.tconst
                LEFT JOIN ratings r ON p.tconst = r.tconst
                LEFT JOIN people pe ON p.nconst = pe.nconst
                WHERE p.category IS NOT NULL
                GROUP BY p.category
                HAVING COUNT(p.principal_id) > 0
                ORDER BY total_principals DESC
            """
            cursor.execute(query)
            stats = cursor.fetchall()
        return stats

    def get_people(self, search_query=None):
        """Optimized people listing with fast subquery approach"""
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            print("Failed to reconnect to the database.")

        with connection.cursor() as cursor:
            if search_query:
                # Search case: Filter first, then JOIN (faster!)
                query = """
                    SELECT 
                        p.nconst, p.primaryName, p.birthYear, p.deathYear,
                        p.primaryProfession, p.knownForTitles, p.most_known_title,
                        t.primaryTitle as most_known_title_name
                    FROM (
                        SELECT * FROM people 
                        WHERE primaryName LIKE %s 
                        ORDER BY most_known_title IS NULL, primaryName 
                        LIMIT 200
                    ) AS p
                    LEFT JOIN titles t ON p.most_known_title = t.tconst
                """
                search_param = f"%{search_query}%"
                cursor.execute(query, (search_param,))
            else:
                # No search: Get first 200 rows, then JOIN (fastest!)
                query = """
                    SELECT 
                        p.nconst, p.primaryName, p.birthYear, p.deathYear,
                        p.primaryProfession, p.knownForTitles, p.most_known_title,
                        t.primaryTitle as most_known_title_name
                    FROM (
                        SELECT * FROM people 
                        ORDER BY most_known_title IS NULL, primaryName 
                        LIMIT 200
                    ) AS p
                    LEFT JOIN titles t ON p.most_known_title = t.tconst
                """
                cursor.execute(query)
            
            people = cursor.fetchall()
        return people
    

    def get_person(self, person_id):
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            # Handle connection failure if ping fails
            print("Failed to reconnect to the database.")

        """Get a specific person by ID with their movies"""
        with connection.cursor() as cursor:
            # Get person details
            query = """
                SELECT 
                    p.*,
                    t.primaryTitle as most_known_title_name,
                    COUNT(pr.principal_id) as total_credits
                FROM people p
                LEFT JOIN titles t ON p.most_known_title = t.tconst
                LEFT JOIN principals pr ON p.nconst = pr.nconst
                WHERE p.nconst = %s
                GROUP BY p.nconst, t.primaryTitle
            """
            cursor.execute(query, (person_id,))
            person = cursor.fetchone()
        
        if person is None:
            print("Person not found in database.")
            return None
        
        # Get person's movies
        with connection.cursor() as cursor:
            query = """
                SELECT 
                    t.tconst,
                    t.primaryTitle,
                    t.startYear,
                    t.titleType,
                    pr.category,
                    pr.characters
                FROM principals pr
                JOIN titles t ON pr.tconst = t.tconst
                WHERE pr.nconst = %s
                ORDER BY t.startYear DESC
                LIMIT 20
            """
            cursor.execute(query, (person_id,))
            person['movies'] = cursor.fetchall()
        
        return person
    
    def add_person(self, name, birth_year, death_year, profession, known_for, most_known_title):
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            # Handle connection failure if ping fails
            print("Failed to reconnect to the database.")

        if (not most_known_title or str(most_known_title).strip() == "") and known_for:
        # Virgülle ayrılmış listenin ilk elemanını al (Örn: "tt01,tt02" -> "tt01")
            most_known_title = known_for.split(',')[0].strip()    

        """Add a new person to database"""
        with connection.cursor() as cursor:
            # Generate nconst - COALESCE ensures 0 if table is empty (null-safe)
            cursor.execute("SELECT COALESCE(MAX(CAST(SUBSTRING(nconst, 3) AS UNSIGNED)), 0) as max_num FROM people WHERE nconst LIKE 'nm%'")
            result = cursor.fetchone()
            max_val = result['max_num'] if isinstance(result, dict) else result[0]
            new_id = f"nm{int(max_val) + 1:07d}"
            
            query = """
                INSERT INTO people (nconst, primaryName, birthYear, deathYear, primaryProfession, knownForTitles, most_known_title)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (new_id, name, birth_year, death_year, profession, known_for, most_known_title))
            connection.commit()
        
        return new_id
    
    def update_person(self, person_id, name, birth_year, death_year, profession, known_for, most_known_title):
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            print("Failed to reconnect to the database.")

        if (not most_known_title or str(most_known_title).strip() == "") and known_for:
            most_known_title = known_for.split(',')[0].strip()    

        """Update an existing person in database"""
        with connection.cursor() as cursor:
            query = """
                UPDATE people 
                SET primaryName = %s, 
                    birthYear = %s, 
                    deathYear = %s, 
                    primaryProfession = %s, 
                    knownForTitles = %s,
                    most_known_title = %s
                WHERE nconst = %s
            """
            cursor.execute(query, (name, birth_year, death_year, profession, known_for, most_known_title, person_id))
            connection.commit()
        
        return True
    
    def delete_person(self, person_id):
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            print("Failed to reconnect to the database.")

        """Delete a person from database"""
        with connection.cursor() as cursor:
            query = "DELETE FROM people WHERE nconst = %s"
            cursor.execute(query, (person_id,))
            connection.commit()
        
        return True
    
    def get_people_performance_stats(self):
        """
        OPTIMIZED PEOPLE ANALYTICS (LIMITED PEOPLE SAMPLE)
        Sadece 1900 sonrası doğan ilk 100 kişiyle istatistikler hesaplanır.
        """
        try:
            connection.ping(reconnect=True)
        except Exception:
            pass

        with connection.cursor() as cursor:
            query = """
                SELECT 
                    p.primaryName,
                    p.primaryProfession,
                    COUNT(DISTINCT pr.tconst) as total_productions,
                    ROUND(AVG(r.average_rating), 2) as career_avg_rating,
                    COUNT(DISTINCT a.region) as worldwide_reach,
                    COALESCE(GROUP_CONCAT(DISTINCT t.genres SEPARATOR ', '), 'N/A') as expert_genres
                FROM (
                SELECT * FROM people 
                WHERE knownForTitles IS NOT NULL -- Verisi dolu olanları seç
                ORDER BY nconst ASC -- İndeks üzerinden hızlıca ilkleri çek
                LIMIT 200
                ) AS p
                LEFT JOIN principals pr ON p.nconst = pr.nconst
                LEFT JOIN titles t ON pr.tconst = t.tconst
                LEFT JOIN ratings r ON t.tconst = r.title_id
                LEFT JOIN akas a ON t.tconst = a.titleId
                GROUP BY p.nconst, p.primaryName, p.primaryProfession
                ORDER BY worldwide_reach DESC, career_avg_rating DESC
            """
            cursor.execute(query)
            stats = cursor.fetchall()
        return stats



# --- Add this method to the Database class in models/database.py ---
    def get_akas_list(self, search_query=None):
        try:
            connection.ping(reconnect=True)
        except Exception:
            pass

        with connection.cursor() as cursor:
            if search_query:
                # DURUM 1: Kullanıcı Arama Yaptıysa (Mecburen sıralayıp arayacağız)
                # İpucu: Az önceki 'CREATE INDEX' kodunu çalıştırdıysan burası da hızlı olur.
                query = (
                    "SELECT a.titleId, a.ordering, a.title, a.region, a.language, t.primaryTitle "
                    "FROM akas a "
                    "JOIN titles t ON a.titleId = t.tconst "
                    "WHERE a.region LIKE %s "
                    "LIMIT 200"
                )
                search_param = f"%{search_query}%"
                cursor.execute(query, (search_param,))
            else:
                # DURUM 2: Sayfa İlk Açılıyor (Arama Yok)
                # HIZ HİLESİ: 'ORDER BY' yok! Sadece ilk bulduğun 200 taneyi al ve çık.
                # Ayrıca önce 200 satırı 'akas'tan alıp SONRA 'titles' ile birleştiriyoruz.
                query = (
                    "SELECT sub_a.titleId, sub_a.ordering, sub_a.title, sub_a.region, sub_a.language, t.primaryTitle "
                    "FROM (SELECT * FROM akas LIMIT 200) sub_a "
                    "JOIN titles t ON sub_a.titleId = t.tconst"
                )
                cursor.execute(query)
            
            akas_list = cursor.fetchall()
        return akas_list

    def get_single_aka(self, title_id, ordering):
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            # Handle connection failure if ping fails
            print("Failed to reconnect to the database.")

        """Fetches a single, detailed AKA record."""
        with connection.cursor() as cursor:
            query = f"SELECT * FROM akas WHERE titleId = '{title_id}' AND ordering = {ordering}"
            cursor.execute(query)
            aka = cursor.fetchone()
        return aka
    
    def add_aka(self, title_id, ordering, title, region, language, types, attributes, is_original_title):
        with connection.cursor() as cursor:
            # NOT: titleId ve ordering primary key olduğu için, 
            # aynı kaydı tekrar eklemeye çalışmak hata (1062) verir.
            query = """
                INSERT INTO akas (titleId, ordering, title, region, language, types, attributes, is_original_title)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                title_id, 
                ordering, 
                title, 
                region if region else None, 
                language if language else None, 
                types if types else None, 
                attributes if attributes else None,
                is_original_title
            ))
            connection.commit()
    def update_aka(self, title_id, ordering, title, region, language, types, attributes, is_original_title):
        """Aka kaydını günceller"""
        with connection.cursor() as cursor:
            query = """
                UPDATE akas 
                SET title = %s, 
                    region = %s, 
                    language = %s, 
                    types = %s, 
                    attributes = %s, 
                    is_original_title = %s
                WHERE titleId = %s AND ordering = %s
            """
            cursor.execute(query, (
                title, 
                region if region else None, 
                language if language else None, 
                types if types else None, 
                attributes if attributes else None,
                is_original_title,
                title_id, 
                ordering
            ))
            connection.commit()

            
    def delete_aka(self, title_id, ordering):
        # Senin delete_principal fonksiyonundaki mantığın aynısı:
        try:
            connection.ping(reconnect=True)
        except Exception:
            pass # Hata olursa görmezden gel, devam et

        with connection.cursor() as cursor:
            # İki anahtarlı (titleId ve ordering) silme işlemi
            query = "DELETE FROM akas WHERE titleId = %s AND ordering = %s"
            cursor.execute(query, (title_id, ordering))
            connection.commit()
        return True
    def get_akas_statistics(self):
        """
        OPTIMIZED COMPLEX QUERY:
        - Uses a SUBQUERY (Derived Table) to limit the scan to 50,000 rows first.
        - Joins only this sample data with 'titles'.
        - Calculates Aggregations (Count, Avg, Sum).
        - Runs instantly instead of freezing.
        """
        try:
            connection.ping(reconnect=True)
        except Exception:
            pass

        with connection.cursor() as cursor:
            query = """
                SELECT 
                    sub_a.region,
                    COUNT(*) as total_entries,
                    COUNT(DISTINCT sub_a.language) as language_count,
                    ROUND(AVG(t.runtimeMinutes), 1) as avg_runtime,
                    SUM(t.isAdult) as adult_count
                FROM 
                    (SELECT * FROM akas WHERE region IS NOT NULL LIMIT 50000) as sub_a
                JOIN titles t ON sub_a.titleId = t.tconst
                GROUP BY sub_a.region
                ORDER BY total_entries DESC
                LIMIT 15
            """
            cursor.execute(query)
            stats = cursor.fetchall()
        return stats
    def get_ratings_list(self, min_rating=None):
        try:
            connection.ping(reconnect=True)
        except Exception:
            pass

        with connection.cursor() as cursor:
            # 1. Temel Sorgu (Henüz LIMIT veya WHERE yok)
            base_query = """
                SELECT 
                    r.rating_id,
                    r.title_id,
                    r.average_rating,
                    r.num_votes,
                    t.primaryTitle 
                FROM ratings r
                LEFT JOIN titles t ON r.title_id = t.tconst
            """
            
            # 2. Karar Anı: Filtre var mı?
            if min_rating is not None:
                # DİKKAT: SQL'de sıra şöyledir: WHERE -> ORDER BY -> LIMIT
                # O yüzden önce WHERE ekliyoruz, sonuna LIMIT yapıştırıyoruz.
                full_query = base_query + " WHERE r.average_rating >= %s ORDER BY r.num_votes DESC LIMIT 200"
                
                # Tek elemanlı tuple kuralı: (min_rating, ) virgül şart!
                cursor.execute(full_query, (min_rating,))
            else:
                # Filtre yoksa direkt LIMIT ekle
                full_query = base_query + " LIMIT 200"
                cursor.execute(full_query)
            
            ratings_list = cursor.fetchall()
        return ratings_list
    
    def get_single_rating(self, rating_id):
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            # Handle connection failure if ping fails
            print("Failed to reconnect to the database.")

        """Fetches a single, detailed Ratings record by its Primary Key."""
        with connection.cursor() as cursor:
            query = f"""
                SELECT 
                    r.rating_id,
                    r.title_id,
                    r.average_rating,
                    r.num_votes,
                    t.primaryTitle 
                FROM ratings r
                JOIN titles t ON r.title_id = t.tconst
                WHERE r.rating_id = {rating_id}
            """
            cursor.execute(query)
            rating = cursor.fetchone()
            print(rating)
        return rating
    
    def add_rating(self, title_id, average_rating, num_votes):
        with connection.cursor() as cursor:
            query = """
                INSERT INTO ratings (title_id, average_rating, num_votes)
                VALUES (%s, %s, %s)
            """
            cursor.execute(query, (title_id, average_rating, num_votes))
            connection.commit()

    def update_rating(self, rating_id, average_rating, num_votes):
        """Rating kaydını günceller"""
        with connection.cursor() as cursor:
            query = """
                UPDATE ratings 
                SET average_rating = %s, 
                    num_votes = %s
                WHERE rating_id = %s
            """
            cursor.execute(query, (average_rating, num_votes, rating_id))
            connection.commit()

    def delete_rating(self, rating_id):
        try:
            connection.ping(reconnect=True)
        except Exception:
            pass # Hata olursa görmezden gel, devam et

        with connection.cursor() as cursor:
            query = "DELETE FROM ratings WHERE rating_id = %s"
            cursor.execute(query, (rating_id))
            connection.commit()
        return True

    def get_ratings_statistics(self):
        """
        ULTIMATE 5-TABLE JOIN QUERY (Düzeltilmiş Versiyon)
        """
        try:
            connection.ping(reconnect=True)
        except Exception:
            pass

        with connection.cursor() as cursor:
            query = """
                SELECT 
                    t.primaryTitle,
                    r.average_rating,
                    r.num_votes,
                    COALESCE(pd.primaryName, 'Unknown') as directors,
                    COUNT(DISTINCT a.region) as global_reach,
                    GROUP_CONCAT(DISTINCT p.primaryName SEPARATOR ', ') as top_cast
                FROM 
                    (SELECT * FROM ratings LIMIT 200) r
                JOIN titles t ON r.title_id = t.tconst
                LEFT JOIN crew c ON t.tconst = c.tconst
                LEFT JOIN people pd ON SUBSTRING_INDEX(c.directors, ',', 1) = pd.nconst
                LEFT JOIN akas a ON t.tconst = a.titleId
                LEFT JOIN principals pr ON t.tconst = pr.tconst AND (pr.category LIKE 'act%')
                LEFT JOIN people p ON pr.nconst = p.nconst
                GROUP BY t.tconst, t.primaryTitle, r.average_rating, r.num_votes, pd.primaryName
                ORDER BY r.average_rating DESC
            """
            cursor.execute(query)
            stats = cursor.fetchall()
        return stats