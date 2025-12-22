from flask import render_template, current_app, abort, request, redirect, url_for, Flask
from flask_login import LoginManager
from models.user import get_user
from config import connection
import sys
import views

sys.path.append("models")
from models.database import Database

app = Flask(__name__)
lm = LoginManager()

# Initialize database
app.config.from_object("settings")
app.config["db"] = Database()

@lm.user_loader
def load_user(user_id):
    return get_user(user_id)


if __name__ == '__main__':
    # Initialize database
    db = Database()
    app.config["db"] = db
    
    # Add app url rules
    app.add_url_rule("/", view_func=views.home_page)

    # Authorization routes
    app.add_url_rule("/login", view_func=views.login_page, methods=["GET", "POST"])
    app.add_url_rule("/logout", view_func=views.logout_page)
    app.add_url_rule("/signup", view_func= views.signup_page, methods=["GET", "POST"])

    app.add_url_rule("/titles", view_func=views.titles_page)
    app.add_url_rule("/titles/<title_id>", view_func=views.title_page)
    app.add_url_rule("/titles/add", view_func=views.title_add_page)
    app.add_url_rule("/titles/<title_id>/edit", view_func=views.title_edit_page, methods=["GET", "POST"])
    app.add_url_rule("/titles/<title_id>/delete", view_func=views.title_delete_page, methods=["POST"])
    app.add_url_rule("/titles/stats", view_func=views.titles_statistics_page)

    app.add_url_rule("/principals", view_func=views.principals_page)
    app.add_url_rule("/principals/add", view_func=views.principal_add_page, methods=["GET", "POST"])
    app.add_url_rule("/principals/<principal_id>", view_func=views.principal_page)
    app.add_url_rule("/principals/<principal_id>/edit", view_func=views.principal_edit_page, methods=["GET", "POST"])
    app.add_url_rule("/principals/<principal_id>/delete", view_func=views.principal_delete_page, methods=["POST"])
    app.add_url_rule("/principals/statistics", view_func=views.principals_statistics_page)
    
    # People pages (Your section)
    app.add_url_rule("/people", view_func=views.people_page)
    app.add_url_rule("/people/add", view_func=views.person_add_page, methods=["GET", "POST"])
    app.add_url_rule("/people/<person_id>", view_func=views.person_page)
    app.add_url_rule("/people/<person_id>/edit", view_func=views.person_edit_page, methods=["GET", "POST"])
    app.add_url_rule("/people/<person_id>/delete", view_func=views.person_delete_page, methods=["POST"])
    app.add_url_rule("/people/statistics", view_func=views.people_statistics_page)

    # akas table
    app.add_url_rule("/akaslist", view_func=views.akas_list_page)                 
    app.add_url_rule("/akaslist/<title_id>/<ordering>", view_func=views.akas_details_page)
    app.add_url_rule("/akas/add", view_func=views.aka_add_page, methods=["GET", "POST"])
    app.add_url_rule("/akas/edit/<title_id>/<int:ordering>", view_func=views.aka_edit_page, methods=["GET", "POST"])
    app.add_url_rule("/akas/delete/<title_id>/<int:ordering>", view_func=views.delete_aka_page, methods=["POST"])
    app.add_url_rule("/akas/stats", view_func=views.akas_stats_page)

    #ratings
    app.add_url_rule("/ratingslist", view_func=views.ratings_list_page)                    
    app.add_url_rule("/ratingslist/<rating_id>", view_func=views.ratings_details_page)
    app.add_url_rule("/ratings/add", view_func=views.rating_add_page, methods=["GET", "POST"])
    app.add_url_rule("/ratings/edit/<int:rating_id>", view_func=views.rating_edit_page, methods=["GET", "POST"])
    app.add_url_rule("/akas/delete/<rating_id>", view_func=views.delete_rating_page, methods=["POST"])
    app.add_url_rule("/ratings/stats", view_func=views.ratings_stats_page)
    
    lm.init_app(app)
    lm.login_view = "login_page"

    app.run(debug=True, port=5000)