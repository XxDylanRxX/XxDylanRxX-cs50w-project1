import os

from flask import Flask, session, render_template ,request , redirect, url_for
from flask_session import Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv
from datetime import datetime
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

 
         if not username:
             return "INGRESE UN USUARIO"
         if not password:
             return "INGRESE UNA CONTRASEÑA"
         if not email:
            return "INGRESA NUEVAMENTE LA CONTRASEÑA"
       

         password_hash = generate_password_hash(password)

         query = text("INSERT INTO users (name, email, password) VALUES (:name, :email, :password)")
         user = db.execute(query,{"name": username, "email": email, "password": password_hash})
         db.commit()
         return render_template("layout.html")
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
            return "invalido"
    
        else:
            session['user_id'] = resultado[0]
            return render_template("layout.html")
    else:
        return render_template("login.html")

@app.route("/cerrarSession")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/Buscarlibro", methods=['GET', 'POST'] )
def Buscarlibro():
     if request.method == 'POST':
        search = request.form['search']
        if not search:
            return render_template('error.html')
        query = text("SELECT * FROM books WHERE author LIKE :search OR title LIKE :search OR isbn LIKE :search")
        search = f'%{search}%'
        resultado = db.execute(query, {"search": search})
        return render_template('busqueda.html', resultado=resultado)
        
     else:
        return render_template("busqueda.html")
        
@app.route("/PaginaLibro/<string:libro_isbn>/<string:libro_id>", methods=['GET', 'POST'])
def PaginaLibro(libro_isbn, libro_id):
    query = text("SELECT * FROM books WHERE  isbn= :libro_isbn ")
    resultado = db.execute(query, {"libro_isbn": libro_isbn}).fetchall()
    print(resultado)
    if request.method == 'POST':
        reseña = request.form.get('reseña') 
        rating = request.form.get('rating')
        fecha_reseña = datetime.now() 
        id_user = session['user_id'][0]
        if reseña is not None:
            query = text("SELECT * FROM reseñas WHERE id_user = :id_user AND id_books = id_books")
            resultado2 = db.execute(query, {"id_user": id_user, "id_books": libro_id}).fetchall()
            print(len(resultado2))
            if len(resultado2) >= 2 :
                return "Ya has publicado una reseña"
            else:
                query = text("INSERT INTO reseñas (id_books, id_user,reseña, rating, fecha_reseña  ) VALUES (:id_books, :id_user, :reseña, :rating, :fecha_reseña )")
                resultado3= db.execute(query,{"id_books": libro_id, "id_user":id_user,"reseña":reseña, "rating":rating, "fecha_reseña": fecha_reseña })
                db.commit()
                query2 = text("SELECT * FROM reseñas WHERE id_user = :id_user")
                resultado2 = db.execute(query2, {"id_user": id_user}).fetchall()
                return render_template("infolibro.html", resultado3 = resultado3)
        else:
            return "agrega una reseña"
    return render_template("infolibro.html", resultado = resultado)


if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)

