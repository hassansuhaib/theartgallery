from flask import Flask, redirect, url_for, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.utils import secure_filename
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from brains import login_required, convert_to_binary
from os.path import join, basename
from base64 import b64encode
from datetime import datetime
import sqlite3

# The location to store the uploaded images
UPLOAD_FOLDER = r"D:\Coding\projects\the-art-gallery\static\uploads"
ALLOWED_EXTENSIONS = set(['PNG', 'JPG', 'JPEG'])

# Configure application
app = Flask(__name__, static_url_path='/static')

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# TO use basenmae filer in template using jinja 
app.add_template_filter(basename)

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure upload folder for images
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["ALLOWED_IMAGE_EXTENSIONS"] = ALLOWED_EXTENSIONS
# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


def allowed_image(filename):

    # We only want files with a . in the filename
    if not "." in filename:
        return False

    # Split the extension from the filename
    ext = filename.rsplit(".", 1)[1]

    # Check if the extension is in ALLOWED_IMAGE_EXTENSIONS
    if ext.upper() in app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        return True
    else:
        return False


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    #clear session if any previous users
    session.clear()

    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return "<h1>Please provide a username!</h1>"
        # Ensure password was submitted
        elif not request.form.get("password"):
            return "<h1>Please provide a password!</h1>"
        with sqlite3.connect("gallery.db") as con:
            db = con.cursor()
            username = request.form.get("username")
            db.execute(
                "SELECT * FROM users WHERE username= ?",  (username,))
            rows = db.fetchall()
        if len(rows) != 1 or not check_password_hash(rows[0][2], request.form.get("password")):
            return "<h1>Wrong username or password!</h1>"
        
        # Remember which user has logged in
        session["user_id"] = rows[0][0]
        session["user_name"] = rows[0][1]

        # Redirect to the homepage
        return redirect("/")
    else:
        return render_template("login.html")

    # Remember which user has logged in
    # session["user_id"] = rows[0]["id"]

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register a new user"""
    session.clear()

    if request.method == "GET":
        return render_template("register.html")
    else:
        if not request.form.get("name"):
            return "<h1>must provide a name</h1>"
        elif not request.form.get("password"):
            return "<h1>must provide a password</h1>"
        elif not request.form.get("secPassword"):
            return "<h1>must provide the password again!</h1>"
        else:
            name = request.form.get("name")
            password = request.form.get("password")
            secPass = request.form.get("secPassword")
            if password != secPass:
                return "<h1>Passwords don't match!</h1>"
            else:
                hashed = generate_password_hash(
                    password, method='pbkdf2:sha256', salt_length=8)
                # Establish a connection with database and add data
                with sqlite3.connect("gallery.db") as con:
                    db = con.cursor()
                    db.execute("INSERT INTO users (username, hashvalue) VALUES(?,?)",(name, hashed))
                    con.commit()
        return redirect("/login")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "GET":
        with sqlite3.connect("gallery.db") as con:
            db = con.cursor()
            db.execute(
                "SELECT * FROM paintings ORDER BY id")
            rows = db.fetchall()
        return render_template("buy.html", rows=rows)
    else:
        return redirect("/")

@app.route("/addToCart", methods=["GET", "POST"])
@login_required
def addToCart():
    if request.method == "POST":
        paintingId = request.form.get("id")
        if not paintingId:
            return "<h1>No Painting Id</h1>"
        if session.get("cart") is None:
            print("No cart in session")
            session["cart"] = []
        # Adding an empty array as a cart for the user
        print("Session cart new call function", session["cart"])
        myCart = session["cart"]
        myCart.append(paintingId)
        print("The cart is:", myCart)
        session["cart"] = myCart
        session.modified = True
        print("Painting with id", paintingId, "added to cart!")
        print("Here in add to cart:", session["cart"])
        return redirect("/buy")
    else:
       return redirect("/buy")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    if request.method == "GET":
        return render_template("sell.html")
    else:
        if request.files:
            image = request.files["artImage"]
            if image.filename =="":
                return "<h1>Not a proper filename</h1>"
            if allowed_image(image.filename):
                filename = secure_filename(image.filename)
                address = join(app.config["UPLOAD_FOLDER"], filename)
                image.save(address)
                title = request.form.get("title")
                artist = request.form.get("artist")
                price = request.form.get("price")
                now = datetime.now()
                formattedDate = now.strftime('%Y-%m-%d %H:%M:%S')
                if not title or not price or not artist:
                    return "<h1>All the info was not provided</h1>"
                with sqlite3.connect("gallery.db") as con:
                    db = con.cursor()
                    db.execute(
                        "INSERT INTO paintings (title, artist, price, imageAddress, additiondate) VALUES(?,?,?,?,?)", (title, artist, price, address, formattedDate))
                    con.commit()
                return redirect("/")
            else:
                return "<h1>That file extension is not allowed</h1>"
        else:
            return "<h1>Upload unsuccessful!</h1>"

@app.route("/cart", methods=["GET", "POST"])
@login_required
def cart():
    if request.method == "GET":
        with sqlite3.connect("gallery.db") as con:
            db = con.cursor()
            print("The items in cart are: ", session["cart"])
            sql_query = "select * from paintings where id in (" + ",".join(
                (str(n) for n in session["cart"])) + ")"
            db.execute(sql_query)
            print("query executed")
            rows = db.fetchall
            print("The value of rows is: ", rows)
            total = 0
            for row in rows:
                total = total + row[3]
        return render_template("cart.html", rows = rows, total = total)
    else:
        return redirect("/")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return "<h1>Internal Server Error!</h1>"


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

if __name__ == "__main__":
    app.run(debug=True)
