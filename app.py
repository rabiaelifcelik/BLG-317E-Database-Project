from flask import render_template, current_app, abort, request, redirect, url_for, Flask
from config import connection
import sys
import views

sys.path.append("models")
from models.database import Database
from models.titles import Titles

app = Flask(__name__)



if __name__ == '__main__':
    # Add app url rules
    app.add_url_rule("/", view_func=views.home_page)
    app.add_url_rule("/titles", view_func=views.titles_page)
    app.add_url_rule("/cast", view_func=views.cast_page)

    app.run(debug=True, port=5000)
