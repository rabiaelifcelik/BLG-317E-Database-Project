# BLG-317E-Database-Project -- Fall 2025
## 🎬 Cache Me If You Can
A movie website connected to a local database. Browse, search, filter, and like movies — or log in as an admin to manage which movies stay in the database.

## ✨ Features
### For Users
- Browse movies — view the full list of available movies
- Filter & search — find movies by genre, year, rating, and more
- Like movies — save your favorites for quick access later
- User-friendly interface — clean, responsive design
### For Admin
- **Movie management** — review and approve or remove movies from the database
- **Content moderation** — ensure only quality, relevant entries stay in the system

## 🛠️ Tech Stack
- **Frontend:** HTML, CSS
- **Backend:** Flask
- **Database:** MySQL

## 📦 Setup & Installation
- Clone the project
~~~
git clone https://github.com/<your-username>/BLG-317E-Database-Project.git
~~~

- Download MySQL and create database
  You can use click [here](https://dev.mysql.com/doc/mysql-getting-started/en/) to install MySQL

- Load the dataset 
~~~
python load_imdb_data.py
~~~

- Prepare tables
~~~
python create_tables.py
~~~

- Run the project
~~~
python app.py
~~~
 

