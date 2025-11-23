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


    def get_titles(self):
        # From real database
        with connection.cursor() as cursor:
            # Fetch 10 movies for testing
            cursor.execute("SELECT tconst, primaryTitle, startYear, genres FROM titles LIMIT 200 ;")
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

        
        return crew
    
    def get_principals(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM principals LIMIT 200;")
            principals = cursor.fetchall()
        return principals
    
    def get_principal(self, principal_id):
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM principals WHERE principal_id = '{principal_id}';")
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

    def get_akas(self, title_id):
        with connection.cursor() as cursor:
            query = f"SELECT title, region, language, types FROM akas WHERE title_id = '{title_id}';"
            cursor.execute(query)
            akas_data = cursor.fetchall()
        return akas_data

    def get_ratings(self, title_id):
        with connection.cursor() as cursor:
            query = f"SELECT averageRating, numVotes FROM ratings WHERE tconst = '{title_id}';"
            cursor.execute(query)
            rating_data = cursor.fetchone()
        return rating_data
