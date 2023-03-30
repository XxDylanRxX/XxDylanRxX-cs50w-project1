import os

from flask import Flask, session, render_template ,request , redirect, url_for
from flask_session import Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv
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
        isbn = request.form.get('isbn')

        query = text("SELECT * FROM books WHERE isbn = :isbn ")
        resultado = db.execute(query, {"isbn": isbn}).fetchall()
        print(resultado)
        return render_template("busqueda.html", resultado = resultado)
     else:
        return render_template("busqueda.html")
        
        
if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)

