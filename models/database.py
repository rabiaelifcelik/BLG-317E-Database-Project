from titles import Titles
from config import connection

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

        with connection.cursor() as cursor:
            # Fetch 10 movies for testing
            cursor.execute(f"SELECT * FROM titles WHERE tconst = '{title_key}';")
            title = cursor.fetchone()

        if title is not None or "":
            return title
        else:
            print("Not found in database.")

        # if title_key in self.titles:
        #     return self.titles[title_key]
        # else:
        #     print("title not found in database.")


    def get_titles(self, limit):
        # From real database
        with connection.cursor() as cursor:
            # Fetch 10 movies for testing

            cursor.execute(f"SELECT tconst, primaryTitle, startYear, genres FROM titles LIMIT {limit} ;")
            titles = cursor.fetchall()

        # From sample database
        # titles = []
        # for title_id, title in self.titles.items():
        #     title_= Titles(title.title_id, title.primary_title, title.original_title, title.is_adult, title.start_year, title.end_year, title.runtime_mins, title.genres)
        #     titles.append((title_id, title_))

        return titles
    

    def get_crew(self,title_id):
        with connection.cursor() as cursor:
            query = f"SELECT * FROM crew WHERE tconst = '{title_id}'"
            cursor.execute(query)
            crew = cursor.fetchone()

            # Fetch Directors
            directors_list = [f"{name}" for name in crew["directors"].split(",")]
            director_str = ",".join(["%s"] * len(directors_list))
            query_directors = f"SELECT nconst, primaryName FROM people WHERE nconst IN ({director_str})"
            cursor.execute(query_directors, directors_list)
            directors = cursor.fetchall()
            print("directors:", directors)
            crew["directors"] = directors

            # Fetch Writers
            if crew["writers"] is not None:
                writers_list = [f"{name}" for name in crew["writers"].split(",")]
                writers_placeholder = ",".join(["%s"] * len(writers_list))
                query_writers = f"SELECT nconst, primaryName FROM people WHERE nconst IN ({writers_placeholder})"
                cursor.execute(query_writers, writers_list)
                writers = directors = cursor.fetchall()
                crew["writers"] = writers

        
        return crew
    
    def get_principals(self):
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
        with connection.cursor() as cursor:
            query = """
                INSERT INTO principals (tconst, ordering, nconst, category, job, characters) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (title_id, ordering, name_id, category, job, characters))
            connection.commit()
        return True

    def get_people(self):
        """Get all people from database"""
        with connection.cursor() as cursor:
            # Fetch people with their basic info
            cursor.execute("SELECT nconst, primaryName, birthYear, deathYear, primaryProfession FROM people LIMIT 200;")
            people = cursor.fetchall()
        
        return people
    

    def get_person(self, person_id):
        """Get a specific person by ID"""
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM people WHERE nconst = '{person_id}';")
            person = cursor.fetchone()
        
        if person is not None:
            return person
        else:
            print("Person not found in database.")
            return None



# --- Add this method to the Database class in models/database.py ---

    def get_akas_list(self):
        """Fetches a limited list of Akas for the main list page."""
        with connection.cursor() as cursor:
            # Join with titles to show the primary title for context
            query = """
                SELECT a.titleId, a.ordering, a.title, a.region, t.primaryTitle 
                FROM akas a
                JOIN titles t ON a.titleId = t.tconst
                LIMIT 200;
            """
            cursor.execute(query)
            akas_list = cursor.fetchall()
        return akas_list

    def get_single_aka(self, title_id, ordering):
        """Fetches a single, detailed AKA record."""
        with connection.cursor() as cursor:
            query = f"""
                SELECT * FROM akas 
                WHERE titleId = '{title_id}' AND ordering = {ordering};
            """
            cursor.execute(query)
            aka = cursor.fetchone()
        return aka

