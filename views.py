from flask import render_template, current_app, abort, request, redirect, url_for
import sys

sys.path.append("models")
from models.database import Database

def home_page():
    return render_template('home.html') 

def titles_page():
    db = current_app.config["db"]
    titles = db.get_titles()
    return render_template('titles.html', titles=titles)

    # This lines is for psoudo-databases
    # db = current_app.config["db"] # To connect the page with database, this is a must
    # titles = db.get_titles()
    # return render_template("titles.html", titles=sorted(titles))

def title_page(title_id):
    if request.method == "GET":
        db = current_app.config["db"]
        title = db.get_title(title_id)
        crew = db.get_crew(title_id)
        if title == None:
            abort(404)
    
        return render_template("title.html", title=title, crew=crew)
    
    else:
        form_title = request.form["title"]
        form_year = request.form["year"]

        db = current_app.config["db"]

        title = db.get_title(title_id)
        title.title = form_title
        title.year = int(form_year) if form_year else None

        return render_template("title_edit.html", title = title)

def cast_page():
    return render_template('cast.html')


# People pages - Your section
def people_page():
    """Your people list page"""
    db = current_app.config["db"]
    people = db.get_people()
    return render_template('people.html', people=people)


def person_page(person_id):
    """Your person detail page"""
    if request.method == "GET":
        db = current_app.config["db"]
        person = db.get_person(person_id)
        
        if person == None:
            abort(404)
    
        return render_template("person.html", person=person)