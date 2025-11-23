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

def principals_page():
    db = current_app.config["db"]
    principals = db.get_principals()
    return render_template('principals.html', principals=principals)

def principal_page(principal_id):
    db = current_app.config["db"]
    principal = db.get_principal(principal_id)
    if principal == None:
        abort(404)
    return render_template("principal.html", principal=principal)

def principal_add_page():
    if request.method == "GET":
        return render_template('principal_add.html')
    else:
        form_title_id = request.form["title_id"]
        form_ordering = request.form["ordering"]
        form_name_id = request.form["name_id"]
        form_category = request.form["category"]
        form_job = request.form.get("job", "")
        form_characters = request.form.get("characters", "")
        
        db = current_app.config["db"]
        db.add_principal(form_title_id, int(form_ordering), form_name_id, form_category, form_job, form_characters)
        
        return redirect(url_for('principals_page'))

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


# AKAS pages
def akas_page():
    db = current_app.config["db"]
    people = db.get_akas()
    return render_template('akas.html', akas=akas)


def title_page(title_id):
    if request.method == "GET":
        db = current_app.config["db"]
        person = db.get_title(title_id)
        
        if title == None:
            abort(404)
    
        return render_template("title.html", title=title)
