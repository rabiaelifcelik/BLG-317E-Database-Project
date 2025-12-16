from flask import render_template, current_app, abort, request, redirect, url_for
import sys

sys.path.append("models")
from models.database import Database

def home_page():
    return render_template('home.html') 

def titles_page(limit = 200):
    db = current_app.config["db"]
    titles = db.get_titles(limit)
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
    
def title_add_page():
    if request.method == "GET":
        return render_template('title_add.html')
    else:
        form_primary_title = request.form["primary_title"]
        form_original_title = request.form["original_title"]
        form_isAdult = request.form["isAdult"]
        form_start_year = request.form["start_year"]
        form_end_year = request.form.get("end_year", None)
        form_runtime_minutes = request.form.get("runtime_minutes", None)
        form_genres = request.form.get("genres", None)
        
        db = current_app.config["db"]
        db.add_title(form_primary_title, form_original_title, int(form_isAdult), form_start_year, form_end_year, form_runtime_minutes, form_genres)
        
        return redirect(url_for('titles_page'))

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

def principal_edit_page(principal_id):
    db = current_app.config["db"]
    
    if request.method == "GET":
        principal = db.get_principal(principal_id)
        if principal == None:
            abort(404)
        return render_template("principal_edit.html", principal=principal)
    else:
        form_title_id = request.form["title_id"]
        form_ordering = request.form["ordering"]
        form_name_id = request.form["name_id"]
        form_category = request.form["category"]
        form_job = request.form.get("job", "")
        form_characters = request.form.get("characters", "")
        
        db.update_principal(principal_id, form_title_id, int(form_ordering), form_name_id, form_category, form_job, form_characters)
        
        return redirect(url_for('principal_page', principal_id=principal_id))

def principal_delete_page(principal_id):
    db = current_app.config["db"]
    db.delete_principal(principal_id)
    return redirect(url_for('principals_page'))

def principals_statistics_page():
    db = current_app.config["db"]
    stats = db.get_principals_statistics()
    return render_template("principals_statistics.html", stats=stats)

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
    search_query = request.args.get('search', '').strip()
    people = db.get_people(search_query if search_query else None)
    return render_template('people.html', people=people, search_query=search_query)


def person_page(person_id):
    """Your person detail page"""
    db = current_app.config["db"]
    person = db.get_person(person_id)
    
    if person == None:
        abort(404)

    return render_template("person.html", person=person)


def person_add_page():
    """Add new person page"""
    if request.method == "GET":
        return render_template('person_add.html')
    else:
        form_name = request.form["name"]
        form_birth = request.form.get("birth_year", None)
        form_death = request.form.get("death_year", None)
        form_profession = request.form.get("profession", "")
        form_known_for = request.form.get("known_for", "")
        
        db = current_app.config["db"]
        new_id = db.add_person(form_name, form_birth, form_death, form_profession, form_known_for)
        
        return redirect(url_for('person_page', person_id=new_id))


def akas_list_page():
    db = current_app.config["db"]
    akas = db.get_akas_list() # Use the new list method
    
    return render_template(
        "akas_list.html",
        akas=akas
    )

# NEW VIEW FUNCTION: akas_details_page (For the details of a single alternate title)
def akas_details_page(title_id, ordering):
    db = current_app.config["db"]
    
    # Note: 'ordering' must be converted to an integer if it came from the URL as a string
    try:
        ordering = int(ordering)
    except ValueError:
        abort(400) # Bad Request if ordering is not a number

    # Fetch the single AKA record
    aka = db.get_single_aka(title_id, ordering) 

    if aka is None:
        abort(404) # Not Found

    return render_template(
        "akas_details.html",
        aka=aka
    )

def aka_add_page():
    db = current_app.config["db"]
    
    if request.method == "GET":
        return render_template("akas_add.html")
    
    elif request.method == "POST":
        # Formdan verileri al
        title_id = request.form.get("title_id")
        ordering = request.form.get("ordering")
        title = request.form.get("title")
        region = request.form.get("region")
        language = request.form.get("language")
        types = request.form.get("types")
        attributes = request.form.get("attributes")
        is_original_title = request.form.get("is_original_title")
        
        # Tip dönüşümü: ordering'i int yap
        try:
            ordering = int(ordering)
            is_original_title = int(is_original_title)
        except ValueError:
            # Hata mesajı gösterebilirsiniz
            return "Hata: Ordering veya Is Original Title geçerli sayı değil.", 400

        try:
            db.add_aka(
                title_id, 
                ordering, 
                title, 
                region, 
                language, 
                types, 
                attributes, 
                is_original_title
            )
            # Başarılı olursa listeye yönlendir
            return redirect(url_for("akas_list_page"))
        except Exception as e:
            # Foreign Key veya Primary Key hatası durumunda
            return f"Error adding Alternate Title. Ensure Title ID exists and the Ordering ID is unique for that Title. Error: {str(e)}", 500
def aka_edit_page(title_id, ordering):
    db = current_app.config["db"]

    if request.method == "GET":
        # Mevcut veriyi çek ve forma gönder
        aka = db.get_single_aka(title_id, ordering)
        if not aka:
            return "Aka record not found", 404
        return render_template("akas_edit.html", aka=aka)

    elif request.method == "POST":
        # Form verilerini al
        title = request.form.get("title")
        region = request.form.get("region")
        language = request.form.get("language")
        types = request.form.get("types")
        attributes = request.form.get("attributes")
        is_original_title = request.form.get("is_original_title")

        # Güncelleme işlemini yap
        try:
            db.update_aka(
                title_id, 
                ordering, 
                title, 
                region, 
                language, 
                types, 
                attributes, 
                int(is_original_title)
            )
            # Detay sayfasına geri yönlendir
            return redirect(url_for('akas_details_page', title_id=title_id, ordering=ordering))
        except Exception as e:
            return f"Error updating record: {str(e)}", 500
# NEW VIEW FUNCTION: ratings_list_page (For the list of all ratings)
def ratings_list_page():
    db = current_app.config["db"]
    ratings = db.get_ratings_list() # Use the new list method
    
    return render_template(
        "ratings_list.html",
        ratings=ratings
    )

# NEW VIEW FUNCTION: ratings_details_page (For the details of a single rating entry)
def ratings_details_page(rating_id):
    db = current_app.config["db"]
    
    try:
        rating_id = int(rating_id)
    except ValueError:
        abort(400) # Bad Request if ID is not a number

    # Fetch the single Ratings record
    rating = db.get_single_rating(rating_id) 

    if rating is None:
        abort(404) # Not Found

    return render_template(
        "ratings_details.html",
        rating=rating
    )

def rating_add_page():
    if request.method == "GET":
        return render_template("ratings_add.html")
    
    # If method is POST (User submitted form)
    elif request.method == "POST":
        title_id = request.form.get("title_id")
        average_rating = request.form.get("average_rating")
        num_votes = request.form.get("num_votes")
        
        db = current_app.config["db"]
        
        try:
            db.add_rating(title_id, average_rating, num_votes)
            # Redirect to the list page on success
            return redirect(url_for("ratings_list_page"))
        except Exception as e:
            # In a real app, you would flash an error message here
            return f"Error adding rating. Ensure Title ID {title_id} exists. Error: {str(e)}"
        
def rating_edit_page(rating_id):
    db = current_app.config["db"]

    if request.method == "GET":
        # Veriyi çek ve forma gönder
        rating = db.get_single_rating(rating_id)
        if not rating:
            return "Rating record not found", 404
        return render_template("ratings_edit.html", rating=rating)

    elif request.method == "POST":
        # Form verilerini al
        average_rating = request.form.get("average_rating")
        num_votes = request.form.get("num_votes")

        try:
            db.update_rating(rating_id, average_rating, num_votes)
            # Detay sayfasına geri yönlendir
            return redirect(url_for('ratings_details_page', rating_id=rating_id))
        except Exception as e:
            return f"Error updating rating: {str(e)}", 500