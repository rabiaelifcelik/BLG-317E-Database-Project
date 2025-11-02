from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html') 

@app.route('/cast')
def cast_page():
    return render_template('cast.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
