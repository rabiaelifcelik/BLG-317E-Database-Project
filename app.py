from flask import render_template, current_app, abort, request, redirect, url_for, Flask
from config import connection
import sys
import views

sys.path.append("models")
from models.database import Database
from models.titles import Titles

app = Flask(__name__)

# Initialize database
app.config["db"] = Database()


if __name__ == '__main__':
    # Initialize database
    db = Database()
    app.config["db"] = db
    
    # Add app url rules
    app.add_url_rule("/", view_func=views.home_page)
    app.add_url_rule("/titles", view_func=views.titles_page)
    app.add_url_rule("/titles/<title_id>", view_func=views.title_page)
    app.add_url_rule("/cast", view_func=views.cast_page)
    app.add_url_rule("/principals", view_func=views.principals_page)
    app.add_url_rule("/principals/add", view_func=views.principal_add_page, methods=["GET", "POST"])
    app.add_url_rule("/principals/<principal_id>", view_func=views.principal_page)
    
    # People pages (Your section)
    app.add_url_rule("/people", view_func=views.people_page)
    app.add_url_rule("/people/<person_id>", view_func=views.person_page)

    # akas table

    
    app.add_url_rule("/akaslist", view_func=views.akas_list_page)                 
    app.add_url_rule("/akaslist/<title_id>/<ordering>", view_func=views.akas_details_page)


    #ratings
    app.add_url_rule("/ratingslist", view_func=views.ratings_list_page)                     # <--- NEW RATINGS LIST PAGE
    app.add_url_rule("/ratingslist/<rating_id>", view_func=views.ratings_details_page)

    # ... rest of your routes ...

    app.run(debug=True, port=5000)
