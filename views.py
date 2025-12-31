from flask import render_template, current_app, abort, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, current_user, login_required
from passlib.hash import pbkdf2_sha256 as hasher
import sys

sys.path.append("models")
from models.database import Database
from forms import LoginForm, SignupForm

def home_page():
    return render_template('home.html') 

def signup_page():
    form = SignupForm()

    session.pop('_flashes', None)
    if form.validate_on_submit():
        db = current_app.config["db"]
        username = form.username.data
        password = form.password.data

        # Check if the user exists
        if db.get_user(username) is not None:
            flash("Username already taken. Please choose another.", "warning")
            return render_template("signup.html", form=form)

        # Create new user
        hashed_password = hasher.hash(password)
        db = current_app.config["db"]
        if db.create_user(username=username, hashed_password=hashed_password):
            user = db.get_user(username)

            # Login the new user
            login_user(user)
            flash("Account created successfully. You are now logged in.", "success")
            return redirect(url_for("login_page"))
        
        else:
            flash("Encountered an error while signing up, please try later.")

    return render_template("signup.html", form=form)

def login_page():
    form = LoginForm()
    db = current_app.config["db"]

    session.pop('_flashes', None)
    if form.validate_on_submit():
        username = form.data["username"]
        user = db.get_user(username)
        if user is not None:
            password = form.data["password"]
            if hasher.verify(password, user.password):
                login_user(user)
                flash("You have logged in.")
                next_page = request.args.get("next", url_for("home_page"))
                return redirect(next_page)
        flash("Invalid credentials.")
    return render_template("login.html", form=form)

def logout_page():
    logout_user()
    flash("You have logged out.")
    return redirect(url_for("home_page"))

def titles_page(limit = 200):
    db = current_app.config["db"]
    sort = "default"
    
    if request.method == "GET":
        search_query = request.args.get('search', '').strip()
        sort = request.args.get('order-by', 'default')
        print(request.args)
    titles = db.get_titles(limit, search_query if search_query else None, sort)
    return render_template('titles.html', titles=titles, current_sort=sort)

def titles_statistics_page():
    db = current_app.config["db"]
    stats = db.get_title_statistics()

    return render_template("title_statistics.html", stats=stats)

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
    if not current_user.is_admin:
        abort(401)

    if request.method == "GET":
        return render_template('title_add.html')
    else:
        # 1. Checkbox kontrolü (Boolean -> 1/0)
        is_adult_raw = request.form.get("isAdult")
        form_isAdult = 1 if is_adult_raw else 0
        
        # 2. Sayısal alanların güvenli dönüşümü (Boşsa None/NULL yap)
        def to_int(val):
            if val and str(val).strip():
                try:
                    return int(val)
                except ValueError:
                    return None
            return None

        # Formdan gelen verileri temizleyerek alıyoruz
        form_title_type = request.form.get("title_type", "movie")
        form_primary_title = request.form.get("primary_title")
        form_original_title = request.form.get("original_title")
        
        # Sayısal alanlar için to_int fonksiyonunu kullanıyoruz
        form_start_year = to_int(request.form.get("start_year"))
        form_end_year = to_int(request.form.get("end_year"))
        form_runtime_minutes = to_int(request.form.get("runtime_minutes"))
        
        # Tür listesi (3NF için getlist kullanımı)
        form_genres = request.form.getlist("genres")
        
        db = current_app.config["db"]
        
        # Database metodunu güvenli verilerle çağırıyoruz
        db.add_title(
            form_title_type, 
            form_primary_title, 
            form_original_title, 
            form_isAdult, 
            form_start_year, 
            form_end_year, 
            form_runtime_minutes, 
            form_genres
        )
        
        return redirect(url_for('titles_page'))

@login_required
def title_edit_page(title_id):
    # Yetkilendirme kontrolü
    if not current_user.is_admin:
        abort(401)

    db = current_app.config["db"]
    
    if request.method == "GET":
        title = db.get_title(title_id)
        if title is None:
            abort(404)
        return render_template("title_edit.html", title=title)
    else:
        # 1. Yardımcı fonksiyon: Sayısal hataları (DataError 1366) önlemek için
        def to_int(val):
            if val is not None and str(val).strip() != "":
                try:
                    return int(val)
                except ValueError:
                    return None
            return None

        # 2. Form verilerini güvenli şekilde alıyoruz
        form_primary_title = request.form.get("primary_title")
        form_original_title = request.form.get("original_title")
        form_title_type = request.form.get("title_type")
        
        # Checkbox kontrolü: Seçiliyse 1, değilse 0
        form_is_adult = 1 if request.form.get('is_adult') else 0
        
        # Sayısal alanları to_int ile temizliyoruz (Boş string yerine None gönderir)
        form_start_year = to_int(request.form.get("start_year"))
        form_end_year = to_int(request.form.get("end_year"))
        form_runtime_minutes = to_int(request.form.get("runtime_minutes"))
        
        # 3. 3NF UYUMLU TÜR LİSTESİ: Birden fazla seçimi desteklemek için getlist kullanılır
        form_genres = request.form.getlist("genres")

        # 4. Veritabanını güncelle
        db.update_title(
            title_id, 
            form_primary_title, 
            form_original_title, 
            form_title_type, 
            form_is_adult, 
            form_start_year, 
            form_end_year, 
            form_runtime_minutes, 
            form_genres
        )
        
        # Başarılı güncelleme sonrası detay sayfasına yönlendir
        return redirect(url_for('title_page', title_id=title_id))
    
def title_delete_page(title_id):
    # Abort the page if the user is not admin
    if not current_user.is_admin:
        abort(401)

    db = current_app.config["db"]
    db.delete_title(title_id)
    return redirect(url_for('titles_page'))
    
def cast_page():
    return render_template('cast.html')

def principals_page():
    db = current_app.config["db"]
    search_query = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    principals, total_count = db.get_principals(search_query if search_query else None, page, per_page)
    
    total_pages = (total_count + per_page - 1) // per_page  # Ceiling division
    
    return render_template('principals.html', 
                         principals=principals, 
                         search_query=search_query,
                         page=page,
                         total_pages=total_pages,
                         total_count=total_count,
                         per_page=per_page)

def principal_page(principal_id):
    db = current_app.config["db"]
    principal = db.get_principal(principal_id)
    if principal == None:
        abort(404)
    return render_template("principal.html", principal=principal)

@login_required
def principal_edit_page(principal_id):
    # Abort the page if the user is not admin
    if not current_user.is_admin:
        abort(401)

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
    # Abort the page if the user is not admin
    if not current_user.is_admin:
        abort(401)

    db = current_app.config["db"]
    db.delete_principal(principal_id)
    return redirect(url_for('principals_page'))

def principals_statistics_page():
    db = current_app.config["db"]
    stats = db.get_principals_statistics()
    return render_template("principals_statistics.html", stats=stats)

def principal_add_page():
    # Abort the page if the user is not admin
    if not current_user.is_admin:
        abort(401)

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
    # Abort the page if the user is not admin
    if not current_user.is_admin:
        abort(401)

    """Add new person page"""
    if request.method == "GET":
        return render_template('person_add.html')
    else:
        form_name = request.form["name"]
        form_birth = request.form.get("birth_year", None)
        form_death = request.form.get("death_year", None)
        form_profession = request.form.get("profession", "")
        form_most_known_title = request.form.get("most_known_title", None)
        
        # Convert profession string to list
        professions_list = [p.strip() for p in form_profession.split(',')] if form_profession else []
        
        db = current_app.config["db"]
        new_id = db.add_person(form_name, form_birth, form_death, professions_list, form_most_known_title)
        return redirect(url_for('person_page', person_id=new_id))

@login_required
def person_edit_page(person_id):
    # Abort the page if the user is not admin

    """Edit person page"""
    db = current_app.config["db"]
    
    if request.method == "GET":
        person = db.get_person(person_id)
        if person == None:
            abort(404)
        return render_template('person_edit.html', person=person)
    else:
        form_name = request.form["name"]
        form_birth = request.form.get("birth_year", None)
        form_death = request.form.get("death_year", None)
        form_profession = request.form.get("profession", "")
        form_most_known_title = request.form.get("most_known_title", None)
        
        # Convert profession string to list
        professions_list = [p.strip() for p in form_profession.split(',')] if form_profession else []
        
        db.update_person(person_id, form_name, form_birth, form_death, professions_list, form_most_known_title)
        return redirect(url_for('person_page', person_id=person_id))


def person_delete_page(person_id):
    # Abort the page if the user is not admin
    if not current_user.is_admin:
        abort(401)

    """Delete person"""
    db = current_app.config["db"]
    db.delete_person(person_id)
    return redirect(url_for('people_page'))


def people_statistics_page():
    """People performance statistics page - Complex analytics"""
    db = current_app.config["db"]
    stats = db.get_people_performance_stats()
    return render_template('people_statistics.html', stats=stats)


def akas_list_page():

    search_query = request.args.get("q")

    db = current_app.config["db"]
    akas = db.get_akas_list(search_query=search_query) 
    
    return render_template(
        "akas_list.html",
        akas=akas,
        search_query=search_query
    )

def akas_details_page(title_id, ordering):
    db = current_app.config["db"]
    
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
    # Abort the page if the user is not admin
    if not current_user.is_admin:
        abort(401)

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
        
        
        try:
            ordering = int(ordering)
            is_original_title = int(is_original_title)
        except ValueError:
            
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

@login_required       
def aka_edit_page(title_id, ordering):
    # Abort the page if the user is not admin

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
        
def delete_aka_page(title_id, ordering):
    # Abort the page if the user is not admin
    if not current_user.is_admin:
        abort(401)

    # Veritabanı bağlantısını al
    db = current_app.config["db"]
    
    # Silme fonksiyonunu çağır
    try:
        db.delete_aka(title_id, ordering)
        return redirect(url_for("akas_list_page"))
    except Exception as e:
        return f"Silinirken hata oluştu: {e}"
    
def akas_stats_page():
    db = current_app.config["db"]
    stats = db.get_akas_statistics()
    return render_template("akas_statistics.html", stats=stats)

def ratings_list_page():
    min_val = request.args.get("min")
    
    if min_val and min_val.strip() != "":
        try:
            min_val = float(min_val)
        except ValueError:
            min_val = None
    else:
        min_val = None

    db = current_app.config["db"]
    ratings = db.get_ratings_list(min_rating=min_val) 
    
    return render_template(
        "ratings_list.html",
        ratings=ratings,
        current_min=min_val
    )

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
    # Abort the page if the user is not admin
    if not current_user.is_admin:
        abort(401)

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
            return f"Error adding rating. Ensure Title ID {title_id} exists. Error: {str(e)}"

@login_required     
def rating_edit_page(rating_id):
    # Abort the page if the user is not admin

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
        
def delete_rating_page(rating_id):
    # Abort the page if the user is not admin
    if not current_user.is_admin:
        abort(401)

    # Veritabanı bağlantısını al
    db = current_app.config["db"]
    
    # Silme fonksiyonunu çağır
    try:
        db.delete_rating(rating_id)
        return redirect(url_for("ratings_list_page"))
    except Exception as e:
        return f"Silinirken hata oluştu: {e}"
    
def ratings_stats_page():
    # Veritabanı bağlantısını al
    db = current_app.config["db"]
    
    
    stats = db.get_ratings_statistics()
    
    # HTML sayfasına gönder
    return render_template("ratings_statistics.html", stats=stats)