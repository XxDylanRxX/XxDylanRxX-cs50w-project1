import os

from flask import Flask, session, render_template, request, redirect, url_for, jsonify
from flask_session import Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv
from datetime import datetime
import requests

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route('/')
def layout():
    return render_template('layout.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")

        query = text("SELECT * FROM users WHERE name = :username ")
        resultado = db.execute(query, {"username": username}).fetchall()
        if len(resultado) >= 1:
            return "USUARIO YA EXISTENTE"
        if not username:
            return "INGRESE UN USUARIO"
        if not password:
            return "INGRESE UNA CONTRASEÑA"
        if not email:
            return "INGRESA NUEVAMENTE LA CONTRASEÑA"

        password_hash = generate_password_hash(password)

        query = text(
            "INSERT INTO users (name, email, password) VALUES (:name, :email, :password)")
        user = db.execute(
            query, {"name": username, "email": email, "password": password_hash})
        db.commit()
        return render_template("login.html")
    else:
        return render_template("registro.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    session.clear()
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username:
            return "usuario requerido"
        elif not password:
            return "contraseña requerida"

        query = text("SELECT * FROM users WHERE name = :username ")
        resultado = db.execute(query, {"username": username}).fetchall()
        print(resultado)
        print(resultado[0][3])

        if len(resultado) != 1 or not check_password_hash(resultado[0][3], password):
            return "contraseña invalida"

        else:
            session['user_id'] = resultado[0]
            return render_template("busqueda.html")
    else:
        return render_template("login.html")


@app.route("/cerrarSession")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/Buscarlibro", methods=['GET', 'POST'])
def Buscarlibro():
    if request.method == 'POST':
        search = request.form['search']
        if not search:
            return 'error.html'
        search = f'%{search.lower()}%'
        query = text(
            "SELECT * FROM books WHERE LOWER(author) LIKE :search OR LOWER(title) LIKE :search OR isbn LIKE :search")
        resultado = db.execute(query, {"search": search})
        return render_template('busqueda.html', resultado=resultado)

    else:
        return render_template("busqueda.html")

@app.route("/PaginaLibro/<string:libro_isbn>/<string:libro_id>", methods=['GET', 'POST'])
def PaginaLibro(libro_isbn, libro_id):
    query = text("SELECT * FROM books WHERE  isbn= :libro_isbn ")
    resultado = db.execute(query, {"libro_isbn": libro_isbn}).fetchall()
    id_user = session['user_id'][0]
    # query2 = text("SELECT * FROM reseñas WHERE id_books = :libro_id")
    # resultado2 = db.execute(query2, {"libro_id": libro_id}).fetchall()
    query2 = text("""
    SELECT reseñas.*, users.name
    FROM reseñas
    JOIN users ON reseñas.id_user = users.id
    WHERE reseñas.id_books = :libro_id
    """)
    resultado2 = db.execute(query2, {"libro_id": libro_id}).fetchall()

    isbn = libro_isbn
    response = requests.get(
        "https://www.googleapis.com/books/v1/volumes?q=isbn:"+isbn).json()
    if "items" in response and response["items"]:
        if "ratingsCount" in response["items"][0]["volumeInfo"]:
            ratings_count = response["items"][0]["volumeInfo"]["ratingsCount"]
        else:
            ratings_count = None

        if "averageRating" in response["items"][0]["volumeInfo"]:
            average_rating = response["items"][0]["volumeInfo"]["averageRating"]
        else:
            average_rating = None
        if 'description' in response["items"][0]["volumeInfo"]:
            descripcion = response["items"][0]["volumeInfo"]["description"]
        else:
            descripcion = None
        if 'imageLinks' in response["items"][0]["volumeInfo"]:
            image_url = response["items"][0]["volumeInfo"]["imageLinks"]["thumbnail"]
        else:
            image_url = None
    else:
        ratings_count = None
        average_rating = None
        descripcion = None
        image_url = None

    if request.method == 'POST':
        reseña = request.form.get('reseña')
        rating = request.form.get('rating')
        fecha_reseña = datetime.now()
        id_user = session['user_id'][0]

        if  reseña and rating:
            query = text(
                "SELECT 1 FROM reseñas WHERE id_books = :libro_id AND id_user = :id_user")
            if db.execute(query, {"id_user": id_user, "libro_id": libro_id}).fetchone() is not None:
                return "Ya has publicado una reseña para este libro"
            query = text("INSERT INTO reseñas (id_books, id_user, reseña, rating, fecha_reseña) "
                         "SELECT :id_books, :id_user, :reseña, :rating, :fecha_reseña "
                         "WHERE NOT EXISTS (SELECT 1 FROM reseñas WHERE id_books = :id_books AND id_user = :id_user)")
            db.execute(query, {"id_books": libro_id, "id_user": id_user, "reseña": reseña,
                               "rating": rating, "fecha_reseña": fecha_reseña})
            db.commit()
            query2 = text("""
            SELECT reseñas.*, users.name
            FROM reseñas
            JOIN users ON reseñas.id_user = users.id
            WHERE reseñas.id_books = :libro_id
            """)
            resultado2 = db.execute(query2, {"libro_id": libro_id}).fetchall()

            print(resultado2)
            return render_template("infolibro.html", resultado=resultado, resultado2=resultado2, ratings_count=ratings_count, average_rating=average_rating, descripcion=descripcion, image_url=image_url)
        else:
            return "Agrega una reseña y una puntuación"

    return render_template("infolibro.html", resultado=resultado, resultado2=resultado2, ratings_count=ratings_count, average_rating=average_rating, descripcion=descripcion, image_url=image_url)


@app.route("/api/<string:libro_isbn>")
def books_api(libro_isbn):
    if libro_isbn is None:
        return jsonify({"error": "Invalid ISBN"}), 422
    query = text("SELECT * FROM books WHERE  isbn= :libro_isbn ")
    resultado = db.execute(query, {"libro_isbn": libro_isbn}).fetchall()
    isbn = libro_isbn
    response = requests.get(
        "https://www.googleapis.com/books/v1/volumes?q=isbn:"+isbn).json()
    if 'ratingsCount' in response["items"][0]["volumeInfo"]:
        ratings_count = response["items"][0]["volumeInfo"]["ratingsCount"]
    else:
        ratings_count = None

    if 'averageRating' in response["items"][0]["volumeInfo"]:
        average_rating = response["items"][0]["volumeInfo"]["averageRating"]
    else:
        average_rating = None

    for result in resultado:
        namebook = result.title
        authorbook = result.author
        yearbook = result.year

    return jsonify({
        "title": namebook,
        "author": authorbook,
        "year": yearbook,
        "isbn": libro_isbn,
        "ratings_count": ratings_count,
        "average_rating": average_rating
    })


if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
