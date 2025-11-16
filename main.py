from flask import render_template, current_app, abort, request, redirect, url_for, Flask
import sys

sys.path.append("Data_classes")
from Data_classes.database import Database
from Data_classes.titles import Titles

app = Flask(__name__)

@app.route('/')
def home_page():
    return render_template('home.html') 

@app.route('/titles')
def titles_page():
    db = current_app.config["db"] # To connect the page with database, this is a must
    titles = db.get_titles()
    return render_template("titles.html", titles=sorted(titles))

@app.route('/cast')
def cast_page():
    return render_template('cast.html')

if __name__ == '__main__':
    db = Database()
    title_1 = Titles("tt0000001", "Carmencita", "Carmencita", 0, "1894", end_year=None, runtime_mins=1, genres="Documentary")
    db.add_title(title_1)
    
    app.config["db"] = db
    app.run(debug=True, port=5000)
