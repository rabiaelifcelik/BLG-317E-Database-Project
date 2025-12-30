from config import connection
import json
import pymysql
from user import DictUser


class Database:
    def __init__(self):
        pass

    def create_user(self, username, hashed_password, is_admin=False):
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            # Handle connection failure if ping fails
            print("Failed to reconnect to the database.")

        
        with connection.cursor() as cursor:
            sql = f"""
                INSERT INTO users (username, password, is_admin)
                VALUES ('{username}', '{hashed_password}', {1 if is_admin else 0});
            """
            cursor.execute(sql)
            connection.commit() 
        return True
    
    def get_user(self, username, user_id = None):
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            # Handle connection failure if ping fails
            print("Failed to reconnect to the database.")

        with connection.cursor() as cursor:
            if user_id is not None:
                cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
            else:
                cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
            row = cursor.fetchone()
            if row:
                return DictUser(row)
            return None

    def get_title(self, title_key):
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            # Handle connection failure if ping fails
            print("Failed to reconnect to the database.")
            
        with connection.cursor() as cursor:
            # Fetch 10 movies for testing
            query = f"""SELECT  
                    t.tconst,
                    t.primaryTitle AS primaryTitle,
                    t.primaryTitle AS original_title,
                    t.titleType,
                    t.startYear,
                    t.endYear,
                    t.isAdult,
                    t.runtimeMinutes,
                    JSON_ARRAYAGG(g.genre_name) AS genres

                FROM titles t
                LEFT JOIN title_genres tg ON t.tconst = tg.tconst
                LEFT JOIN genres g ON tg.genre_id = g.genre_id

                WHERE t.tconst = "{title_key}"

                GROUP BY 
                    t.tconst,
                    t.primaryTitle,
                    t.titleType,
                    t.startYear,
                    t.endYear,
                    t.isAdult,
                    t.runtimeMinutes;

            """

            cursor.execute(query)
            title = cursor.fetchone()
            if title["genres"]:
                title["genres"] = json.loads(title["genres"])
            else:
                title["genres"] = []
            print(title)

        if title is not None or "":
            return title
        else:
            print("Not found in database.")

    def get_titles(self, limit=200, search_title=None, sort = 'default', group = None):
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            # Handle connection failure if ping fails
            print("Failed to reconnect to the database.")

        order_by_mapping = {
            'oldest': 'startYear ASC',
            'newest': 'startYear DESC',
            'content-name': 'primaryTitle ASC',
            'default': 'tconst ASC'  # default
        }
        order_by = order_by_mapping.get(sort, 'tconst ASC')

        query = f"""SELECT
                        t.tconst,
                        t.primaryTitle,
                        t.startYear,
                        t.endYear,
                        JSON_ARRAYAGG(g.genre_name) AS genres
                    FROM titles t
                    LEFT JOIN title_genres tg
                        ON t.tconst = tg.tconst
                    LEFT JOIN genres g
                        ON tg.genre_id = g.genre_id
                """

        with connection.cursor() as cursor:
            if search_title is None:
                query += f"""GROUP BY
                                t.tconst,
                                t.primaryTitle,
                                t.startYear,
                                t.endYear 
                            ORDER BY {order_by} LIMIT {limit};"""

            else:
                query += f""" WHERE t.primaryTitle LIKE '%{search_title}%' 
                              GROUP BY
                                t.tconst,
                                t.primaryTitle,
                                t.startYear,
                                t.endYear  
                              ORDER BY {order_by} LIMIT {limit};"""


            if group is not None:
                query = f"SELECT COUNT({group}) as count, {group} as value from titles group by {group} LIMIT {limit};"

                if group == "genres":
                    query = f"""
                                SELECT
                                    g.genre_name AS value,
                                    COUNT(*) AS count
                                FROM title_genres tg
                                JOIN genres g
                                    ON tg.genre_id = g.genre_id
                                GROUP BY g.genre_name
                                ORDER BY count DESC
                                LIMIT {limit};
                            """
                
            cursor.execute(query)
            titles = cursor.fetchall()

            for title in titles:
                if title["genres"]:
                    title["genres"] = json.loads(title["genres"])
                else:
                    title["genres"] = []

        return titles    

    def get_crew(self,title_id):
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            # Handle connection failure if ping fails
            print("Failed to reconnect to the database.")

        with connection.cursor() as cursor:
            #query = f"SELECT * FROM crew WHERE tconst = '{title_id}'" 

            query = f"""
                    SELECT
                        c.tconst,

                        (
                            SELECT JSON_ARRAYAGG(
                                JSON_OBJECT(
                                    'nconst', p.nconst,
                                    'primaryName', p.primaryName
                                )
                            )
                            FROM crew_directors cd
                            JOIN people p ON p.nconst = cd.nconst
                            WHERE cd.tconst = c.tconst
                        ) AS directors,

                        (
                            SELECT JSON_ARRAYAGG(
                                JSON_OBJECT(
                                    'nconst', p.nconst,
                                    'primaryName', p.primaryName
                                )
                            )
                            FROM crew_writers cw
                            JOIN people p ON p.nconst = cw.nconst
                            WHERE cw.tconst = c.tconst
                        ) AS writers

                    FROM crew c
                    WHERE c.tconst = '{title_id}';
                    """
            
            cursor.execute(query)
            crew = cursor.fetchone()

        crew['directors'] = json.loads(crew['directors']) if crew['directors'] else []
        crew['writers'] = json.loads(crew['writers']) if crew['writers'] else []

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
    
    def delete_title(self, title_id):
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            print("Failed to reconnect to the database.")

        with connection.cursor() as cursor:
            query = """
                DELETE FROM titles
                WHERE tconst = %s
            """
            cursor.execute(query, (title_id))
            connection.commit()
        return True
    
    def update_title(self, titleId, primaryTitle, originalTitle, titleType, isAdult, startYear, endYear, runtimeMinutes, genres):
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            print("Failed to reconnect to the database.")

        with connection.cursor() as cursor:
            query = """
                UPDATE titles 
                SET  primaryTitle = %s, originalTitle = %s, titleType = %s, isAdult = %s, startYear = %s, endYear = %s, runtimeMinutes = %s, genres = %s
                WHERE tconst = %s
            """
            cursor.execute(query, (primaryTitle, originalTitle, titleType, isAdult, startYear, endYear, runtimeMinutes, genres, titleId))
            connection.commit()
        return True



    def get_principals(self, search_query=None, page=1, per_page=50):
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            # Handle connection failure if ping fails
            print("Failed to reconnect to the database.")

        offset = (page - 1) * per_page

        with connection.cursor() as cursor:
            # First, get the total count
            if search_query:
                count_query = """
                    SELECT COUNT(*) as total
                    FROM principals p
                    LEFT JOIN titles t ON p.tconst = t.tconst
                    LEFT JOIN people pe ON p.nconst = pe.nconst
                    WHERE pe.primaryName LIKE %s 
                       OR t.primaryTitle LIKE %s
                       OR p.category LIKE %s
                       OR p.job LIKE %s
                """
                search_param = f"%{search_query}%"
                cursor.execute(count_query, (search_param, search_param, search_param, search_param))
            else:
                count_query = "SELECT COUNT(*) as total FROM principals"
                cursor.execute(count_query)
            
            total_count = cursor.fetchone()['total']

            # Then get the paginated data
            if search_query:
                # Search in person name, title name, category, or job
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
                        GROUP_CONCAT(pc.character_name SEPARATOR ', ') as characters
                    FROM principals p
                    LEFT JOIN titles t ON p.tconst = t.tconst
                    LEFT JOIN people pe ON p.nconst = pe.nconst
                    LEFT JOIN principal_characters pc ON p.principal_id = pc.principal_id
                    WHERE pe.primaryName LIKE %s 
                       OR t.primaryTitle LIKE %s
                       OR p.category LIKE %s
                       OR p.job LIKE %s
                    GROUP BY p.principal_id, p.tconst, t.primaryTitle, p.ordering, p.nconst, pe.primaryName, p.category, p.job
                    ORDER BY p.principal_id DESC
                    LIMIT %s OFFSET %s
                """
                search_param = f"%{search_query}%"
                cursor.execute(query, (search_param, search_param, search_param, search_param, per_page, offset))
            else:
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
                        GROUP_CONCAT(pc.character_name SEPARATOR ', ') as characters
                    FROM principals p
                    LEFT JOIN titles t ON p.tconst = t.tconst
                    LEFT JOIN people pe ON p.nconst = pe.nconst
                    LEFT JOIN principal_characters pc ON p.principal_id = pc.principal_id
                    GROUP BY p.principal_id, p.tconst, t.primaryTitle, p.ordering, p.nconst, pe.primaryName, p.category, p.job
                    ORDER BY p.principal_id DESC
                    LIMIT %s OFFSET %s
                """
                cursor.execute(query, (per_page, offset))
            principals = cursor.fetchall()
        return principals, total_count
    
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
                    GROUP_CONCAT(DISTINCT prof.profession_name SEPARATOR ', ') as person_profession,
                    p.category,
                    p.job,
                    GROUP_CONCAT(DISTINCT pc.character_name SEPARATOR ', ') as characters
                FROM principals p
                LEFT JOIN titles t ON p.tconst = t.tconst
                LEFT JOIN people pe ON p.nconst = pe.nconst
                LEFT JOIN people_professions pp ON pe.nconst = pp.nconst
                LEFT JOIN professions prof ON pp.profession_id = prof.profession_id
                LEFT JOIN principal_characters pc ON p.principal_id = pc.principal_id
                WHERE p.principal_id = %s
                GROUP BY p.principal_id, p.tconst, t.primaryTitle, t.startYear, p.ordering, p.nconst, pe.primaryName, pe.birthYear, p.category, p.job
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
            # Insert principal without characters
            query = """
                INSERT INTO principals (tconst, ordering, nconst, category, job) 
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (title_id, ordering, name_id, category, job))
            principal_id = cursor.lastrowid
            
            # Insert characters separately if provided
            if characters:
                import json
                try:
                    # Try to parse as JSON array
                    char_list = json.loads(characters) if isinstance(characters, str) else characters
                    if isinstance(char_list, list):
                        for char_name in char_list:
                            if char_name and char_name.strip():
                                cursor.execute(
                                    "INSERT INTO principal_characters (principal_id, character_name) VALUES (%s, %s)",
                                    (principal_id, char_name.strip())
                                )
                except:
                    # If not JSON, treat as single character or comma-separated
                    char_names = characters.split(',') if ',' in characters else [characters]
                    for char_name in char_names:
                        if char_name and char_name.strip():
                            cursor.execute(
                                "INSERT INTO principal_characters (principal_id, character_name) VALUES (%s, %s)",
                                (principal_id, char_name.strip())
                            )
            
            connection.commit()
        return True
    
    def update_principal(self, principal_id, title_id, ordering, name_id, category, job, characters):
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            print("Failed to reconnect to the database.")

        with connection.cursor() as cursor:
            # Update principal without characters
            query = """
                UPDATE principals 
                SET tconst = %s, ordering = %s, nconst = %s, category = %s, job = %s
                WHERE principal_id = %s
            """
            cursor.execute(query, (title_id, ordering, name_id, category, job, principal_id))
            
            # Delete existing characters
            cursor.execute("DELETE FROM principal_characters WHERE principal_id = %s", (principal_id,))
            
            # Insert new characters if provided
            if characters:
                import json
                try:
                    # Try to parse as JSON array
                    char_list = json.loads(characters) if isinstance(characters, str) else characters
                    if isinstance(char_list, list):
                        for char_name in char_list:
                            if char_name and char_name.strip():
                                cursor.execute(
                                    "INSERT INTO principal_characters (principal_id, character_name) VALUES (%s, %s)",
                                    (principal_id, char_name.strip())
                                )
                except:
                    # If not JSON, treat as single character or comma-separated
                    char_names = characters.split(',') if ',' in characters else [characters]
                    for char_name in char_names:
                        if char_name and char_name.strip():
                            cursor.execute(
                                "INSERT INTO principal_characters (principal_id, character_name) VALUES (%s, %s)",
                                (principal_id, char_name.strip())
                            )
            
            connection.commit()
        return True
    
    def delete_principal(self, principal_id):
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            print("Failed to reconnect to the database.")

        with connection.cursor() as cursor:
            # CASCADE will automatically delete related characters
            query = "DELETE FROM principals WHERE principal_id = %s"
            cursor.execute(query, (principal_id,))
            connection.commit()
        return True
    
    def get_principal_characters(self, principal_id):
        """Get all characters for a principal (3NF helper function)"""
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            print("Failed to reconnect to the database.")

        with connection.cursor() as cursor:
            query = """
                SELECT character_id, character_name 
                FROM principal_characters 
                WHERE principal_id = %s
                ORDER BY character_id
            """
            cursor.execute(query, (principal_id,))
            characters = cursor.fetchall()
        return characters
    
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
                LEFT JOIN ratings r ON p.tconst = r.title_id
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
        """Optimized people listing with fast subquery approach and NULL safety"""
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            print("Failed to reconnect to the database.")

        with connection.cursor() as cursor:
            if search_query:
                # Arama Durumu: WHERE ve ORDER BY sırası düzeltildi
                query = """
                    SELECT 
                        p.nconst, p.primaryName, 
                        COALESCE(p.birthYear, 0) as birthYear,
                        COALESCE(p.deathYear, 0) as deathYear, 
                        p.most_known_title,
                        t.primaryTitle as most_known_title_name,
                        GROUP_CONCAT(DISTINCT prof.profession_name SEPARATOR ', ') as professions
                    FROM (
                        SELECT * FROM people 
                        WHERE primaryName LIKE %s 
                        ORDER BY nconst ASC
                        LIMIT 200
                    ) AS p
                    LEFT JOIN titles t ON p.most_known_title = t.tconst
                    LEFT JOIN people_professions pp ON p.nconst = pp.nconst
                    LEFT JOIN professions prof ON pp.profession_id = prof.profession_id
                    GROUP BY p.nconst, p.primaryName, p.birthYear, p.deathYear, p.most_known_title, t.primaryTitle
                """
                search_param = f"{search_query}%"
                cursor.execute(query, (search_param,))
            else:
                # Genel Liste: En hızlı hali
                query = """
                    SELECT 
                        p.nconst, p.primaryName, 
                        COALESCE(p.birthYear, 0) as birthYear,
                        COALESCE(p.deathYear, 0) as deathYear,
                        p.most_known_title,
                        t.primaryTitle as most_known_title_name,
                        GROUP_CONCAT(DISTINCT prof.profession_name SEPARATOR ', ') as professions
                    FROM (
                        SELECT * FROM people 
                        ORDER BY nconst ASC
                        LIMIT 200
                    ) AS p
                    LEFT JOIN titles t ON p.most_known_title = t.tconst
                    LEFT JOIN people_professions pp ON p.nconst = pp.nconst
                    LEFT JOIN professions prof ON pp.profession_id = prof.profession_id
                    GROUP BY p.nconst, p.primaryName, p.birthYear, p.deathYear, p.most_known_title, t.primaryTitle
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
                    COUNT(DISTINCT pr.principal_id) as total_credits,
                    GROUP_CONCAT(DISTINCT prof.profession_name SEPARATOR ', ') as professions
                FROM people p
                LEFT JOIN titles t ON p.most_known_title = t.tconst
                LEFT JOIN principals pr ON p.nconst = pr.nconst
                LEFT JOIN people_professions pp ON p.nconst = pp.nconst
                LEFT JOIN professions prof ON pp.profession_id = prof.profession_id
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
                    GROUP_CONCAT(pc.character_name SEPARATOR ', ') as characters
                FROM principals pr
                JOIN titles t ON pr.tconst = t.tconst
                LEFT JOIN principal_characters pc ON pr.principal_id = pc.principal_id
                WHERE pr.nconst = %s
                GROUP BY pr.principal_id, t.tconst, t.primaryTitle, t.startYear, t.titleType, pr.category
                ORDER BY t.startYear DESC
                LIMIT 20
            """
            cursor.execute(query, (person_id,))
            person['movies'] = cursor.fetchall()
        
        return person
    
    def add_person(self, name, birth_year, death_year, professions_list, most_known_title):
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            print("Failed to reconnect to the database.")

        """Add a new person to database"""
        with connection.cursor() as cursor:
            # Generate nconst
            cursor.execute("SELECT COALESCE(MAX(CAST(SUBSTRING(nconst, 3) AS UNSIGNED)), 0) as max_num FROM people WHERE nconst LIKE 'nm%'")
            result = cursor.fetchone()
            max_val = result['max_num'] if isinstance(result, dict) else result[0]
            new_id = f"nm{int(max_val) + 1:07d}"
            
            # Insert person
            query = """
                INSERT INTO people (nconst, primaryName, birthYear, deathYear, most_known_title)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (new_id, name, birth_year, death_year, most_known_title))
            
            # Add professions if provided
            if professions_list:
                for profession in professions_list:
                    profession = profession.strip()
                    if profession:
                        # Insert profession if not exists
                        cursor.execute(
                            "INSERT IGNORE INTO professions (profession_name) VALUES (%s)",
                            (profession,)
                        )
                        # Get profession_id
                        cursor.execute(
                            "SELECT profession_id FROM professions WHERE profession_name = %s",
                            (profession,)
                        )
                        prof_result = cursor.fetchone()
                        if prof_result:
                            prof_id = prof_result['profession_id'] if isinstance(prof_result, dict) else prof_result[0]
                            # Link person to profession
                            cursor.execute(
                                "INSERT IGNORE INTO people_professions (nconst, profession_id) VALUES (%s, %s)",
                                (new_id, prof_id)
                            )
            
            connection.commit()
        
        return new_id
    
    def update_person(self, person_id, name, birth_year, death_year, professions_list, most_known_title):
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            print("Failed to reconnect to the database.")

        with connection.cursor() as cursor:
            # Update person basic info
            query = """
                UPDATE people 
                SET primaryName = %s, 
                    birthYear = %s, 
                    deathYear = %s, 
                    most_known_title = %s
                WHERE nconst = %s
            """
            cursor.execute(query, (name, birth_year, death_year, most_known_title, person_id))
            
            # Delete existing professions
            cursor.execute("DELETE FROM people_professions WHERE nconst = %s", (person_id,))
            
            # Add new professions
            if professions_list:
                for profession in professions_list:
                    profession = profession.strip()
                    if profession:
                        # Insert profession if not exists
                        cursor.execute(
                            "INSERT IGNORE INTO professions (profession_name) VALUES (%s)",
                            (profession,)
                        )
                        # Get profession_id
                        cursor.execute(
                            "SELECT profession_id FROM professions WHERE profession_name = %s",
                            (profession,)
                        )
                        prof_result = cursor.fetchone()
                        if prof_result:
                            prof_id = prof_result['profession_id'] if isinstance(prof_result, dict) else prof_result[0]
                            # Link person to profession
                            cursor.execute(
                                "INSERT IGNORE INTO people_professions (nconst, profession_id) VALUES (%s, %s)",
                                (person_id, prof_id)
                            )
            
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
        ULTIMATE PEOPLE ANALYTICS (5-Table Join & Subquery)
        Complex query analyzing artists' career performance with:
        - Subquery for efficient data sampling
        - 5-table JOIN (people, principals, titles, ratings, akas)
        - Aggregate functions (COUNT, AVG)
        - GROUP BY and HAVING clauses
        - Multiple sorting criteria
        
        Returns: Top 100 artists ranked by worldwide reach and average ratings
        """
        try:
            connection.ping(reconnect=True)
        except Exception:
            pass

        with connection.cursor() as cursor:
            query = """
                SELECT 
                    p.primaryName,
                    GROUP_CONCAT(DISTINCT prof.profession_name SEPARATOR ', ') as professions,
                    COUNT(DISTINCT pr.tconst) as total_productions,
                    ROUND(AVG(r.average_rating), 2) as career_avg_rating,
                    COUNT(DISTINCT a.region) as worldwide_reach
                FROM people p
                LEFT JOIN people_professions pp ON p.nconst = pp.nconst
                LEFT JOIN professions prof ON pp.profession_id = prof.profession_id
                LEFT JOIN principals pr ON p.nconst = pr.nconst
                LEFT JOIN titles t ON pr.tconst = t.tconst
                LEFT JOIN ratings r ON t.tconst = r.title_id
                LEFT JOIN akas a ON t.tconst = a.titleId
                WHERE p.birthYear IS NOT NULL
                GROUP BY p.nconst, p.primaryName
                HAVING total_productions > 0
                ORDER BY worldwide_reach DESC, career_avg_rating DESC
                LIMIT 200
            """
            cursor.execute(query)
            stats = cursor.fetchall()
        return stats



    def get_akas_list(self, search_query=None):
        try:
            connection.ping(reconnect=True)
        except Exception:
            pass

        with connection.cursor() as cursor:
            if search_query:
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
            
            if min_rating is not None:
                full_query = base_query + " WHERE r.average_rating >= %s ORDER BY r.num_votes DESC LIMIT 200"
                
                cursor.execute(full_query, (min_rating,))
            else:
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
        ULTIMATE 5-TABLE JOIN QUERY
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
    
    # ========== EPISODE FUNCTIONS ==========
    
    def get_episodes(self, parent_tconst=None, search_query=None, limit=200):
        """
        Get episodes, optionally filtered by parent series or search query
        
        Args:
            parent_tconst: Filter episodes by parent series ID
            search_query: Search in episode or parent title names
            limit: Maximum number of results
        """
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            print("Failed to reconnect to the database.")

        with connection.cursor() as cursor:
            if parent_tconst:
                # Get all episodes of a specific series
                query = """
                    SELECT 
                        e.tconst,
                        e.parentTconst,
                        e.seasonNumber,
                        e.episodeNumber,
                        t.primaryTitle as episode_title,
                        t.startYear as episode_year,
                        pt.primaryTitle as parent_title
                    FROM episodes e
                    JOIN titles t ON e.tconst = t.tconst
                    LEFT JOIN titles pt ON e.parentTconst = pt.tconst
                    WHERE e.parentTconst = %s
                    ORDER BY e.seasonNumber ASC, e.episodeNumber ASC
                    LIMIT %s
                """
                cursor.execute(query, (parent_tconst, limit))
            elif search_query:
                # Search in episode or parent titles
                query = """
                    SELECT 
                        e.tconst,
                        e.parentTconst,
                        e.seasonNumber,
                        e.episodeNumber,
                        t.primaryTitle as episode_title,
                        t.startYear as episode_year,
                        pt.primaryTitle as parent_title
                    FROM episodes e
                    JOIN titles t ON e.tconst = t.tconst
                    LEFT JOIN titles pt ON e.parentTconst = pt.tconst
                    WHERE t.primaryTitle LIKE %s 
                       OR pt.primaryTitle LIKE %s
                    ORDER BY e.seasonNumber ASC, e.episodeNumber ASC
                    LIMIT %s
                """
                search_param = f"%{search_query}%"
                cursor.execute(query, (search_param, search_param, limit))
            else:
                # Get all episodes
                query = """
                    SELECT 
                        e.tconst,
                        e.parentTconst,
                        e.seasonNumber,
                        e.episodeNumber,
                        t.primaryTitle as episode_title,
                        t.startYear as episode_year,
                        pt.primaryTitle as parent_title
                    FROM episodes e
                    JOIN titles t ON e.tconst = t.tconst
                    LEFT JOIN titles pt ON e.parentTconst = pt.tconst
                    ORDER BY e.tconst DESC
                    LIMIT %s
                """
                cursor.execute(query, (limit,))
            
            episodes = cursor.fetchall()
        return episodes
    
    def get_episode(self, episode_tconst):
        """Get a single episode with full details"""
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            print("Failed to reconnect to the database.")

        with connection.cursor() as cursor:
            query = """
                SELECT 
                    e.tconst,
                    e.parentTconst,
                    e.seasonNumber,
                    e.episodeNumber,
                    t.primaryTitle as episode_title,
                    t.titleType,
                    t.startYear as episode_year,
                    t.runtimeMinutes,
                    t.genres,
                    pt.primaryTitle as parent_title,
                    pt.startYear as parent_year
                FROM episodes e
                JOIN titles t ON e.tconst = t.tconst
                LEFT JOIN titles pt ON e.parentTconst = pt.tconst
                WHERE e.tconst = %s
            """
            cursor.execute(query, (episode_tconst,))
            episode = cursor.fetchone()
        
        if episode is not None:
            return episode
        else:
            print("Episode not found in database.")
            return None
    
    def add_episode(self, episode_tconst, parent_tconst, season_number, episode_number):
        """
        Add a new episode record
        Note: The episode must already exist in titles table
        """
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            print("Failed to reconnect to the database.")

        with connection.cursor() as cursor:
            query = """
                INSERT INTO episodes (tconst, parentTconst, seasonNumber, episodeNumber) 
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (episode_tconst, parent_tconst, season_number, episode_number))
            connection.commit()
        return True
    
    def update_episode(self, episode_tconst, parent_tconst, season_number, episode_number):
        """Update an existing episode record"""
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            print("Failed to reconnect to the database.")

        with connection.cursor() as cursor:
            query = """
                UPDATE episodes 
                SET parentTconst = %s, seasonNumber = %s, episodeNumber = %s
                WHERE tconst = %s
            """
            cursor.execute(query, (parent_tconst, season_number, episode_number, episode_tconst))
            connection.commit()
        return True
    
    def delete_episode(self, episode_tconst):
        """
        Delete an episode record
        Note: This only removes the episode relationship, not the title itself
        """
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            print("Failed to reconnect to the database.")

        with connection.cursor() as cursor:
            query = "DELETE FROM episodes WHERE tconst = %s"
            cursor.execute(query, (episode_tconst,))
            connection.commit()
        return True
    
    def get_series_seasons(self, parent_tconst):
        """Get season statistics for a series"""
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            print("Failed to reconnect to the database.")

        with connection.cursor() as cursor:
            query = """
                SELECT 
                    e.seasonNumber,
                    COUNT(*) as episode_count,
                    MIN(t.startYear) as first_aired,
                    MAX(t.startYear) as last_aired,
                    AVG(t.runtimeMinutes) as avg_runtime
                FROM episodes e
                JOIN titles t ON e.tconst = t.tconst
                WHERE e.parentTconst = %s AND e.seasonNumber IS NOT NULL
                GROUP BY e.seasonNumber
                ORDER BY e.seasonNumber ASC
            """
            cursor.execute(query, (parent_tconst,))
            seasons = cursor.fetchall()
        return seasons
    
    def get_episode_statistics(self):
        """Get comprehensive episode statistics with complex query"""
        try:
            connection.ping(reconnect=True)
        except pymysql.OperationalError:
            print("Failed to reconnect to the database.")

        with connection.cursor() as cursor:
            query = """
                SELECT 
                    pt.primaryTitle as series_name,
                    COUNT(DISTINCT e.tconst) as total_episodes,
                    COUNT(DISTINCT e.seasonNumber) as total_seasons,
                    MIN(t.startYear) as first_aired,
                    MAX(t.startYear) as last_aired,
                    AVG(r.average_rating) as avg_rating,
                    SUM(r.num_votes) as total_votes
                FROM episodes e
                JOIN titles t ON e.tconst = t.tconst
                JOIN titles pt ON e.parentTconst = pt.tconst
                LEFT JOIN ratings r ON t.tconst = r.title_id
                GROUP BY e.parentTconst, pt.primaryTitle
                HAVING total_episodes > 5
                ORDER BY total_episodes DESC
                LIMIT 100
            """
            cursor.execute(query)
            stats = cursor.fetchall()
        return stats
