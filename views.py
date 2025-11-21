from flask import render_template, current_app
from config import connection

def home_page():
    return render_template('home.html') 

def titles_page():
    with connection.cursor() as cursor:
        # Fetch 10 movies for testing
        cursor.execute("SELECT tconst, primaryTitle, startYear, genres FROM titles LIMIT 10;")
        titles = cursor.fetchall()
    return render_template('titles.html', titles=titles)
    # db = current_app.config["db"] # To connect the page with database, this is a must
    # titles = db.get_titles()
    # return render_template("titles.html", titles=sorted(titles))

def cast_page():
    return render_template('cast.html')