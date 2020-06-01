from flask import Flask, redirect, url_for, render_template, request, session, flash
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.utils import secure_filename
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from brains import login_required, format_date, message
from os.path import join, basename, splitext
import sqlite3
import re

# The location to store the uploaded images
UPLOAD_FOLDER = r"D:\Coding\projects\the-art-gallery\static\uploads"
ALLOWED_EXTENSIONS = set(['PNG', 'JPG', 'JPEG'])

# Configure application
app = Flask(__name__, static_url_path='/static')

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# TO use basename and format_date filer in template using jinja
app.add_template_filter(basename)
app.add_template_filter(format_date)

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
    # clear session if any previous users
    session.clear()

    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return message("Please provide a username!")
        # Ensure password was submitted
        elif not request.form.get("password"):
            return message("Please provide a password!")
        with sqlite3.connect("gallery.db") as con:
            db = con.cursor()
            username = request.form.get("username")
            if username == " ":
                return message("Please provide a valid username")
            db.execute(
                f"SELECT * FROM users WHERE username='{username}'")
            rows = db.fetchall()
            if not rows:
                return message("User doesn't exist in the database!")
            if len(rows) != 1 or not check_password_hash(rows[0][2], request.form.get("password")):
                return message("Wrong username or password!")

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
        if request.form.get("username") == " ":
            return message("Please provide a name!")
        elif request.form.get("password") == " " or request.form.get("secPassword") == " ":
            return message("Please provide a valid password!")
        elif request.form.get("country") == " ":
            return message("Please provide a valid country name!")
        elif request.form.get("firstName") == " " or request.form.get("lastName") == " ":
            return message("Please prove valid first and last names!")
        else:
            username = request.form.get("username")
            password = request.form.get("password")
            secPass = request.form.get("secPassword")
            firstName = request.form.get("firstName")
            lastName = request.form.get("lastName")
            country = request.form.get("country")
            if password != secPass:
                return message("Passwords don't match!")
            else:
                hashed = generate_password_hash(
                    password, method='pbkdf2:sha256', salt_length=8)
                # Establish a connection with database and add data
                with sqlite3.connect("gallery.db") as con:
                    db = con.cursor()
                    db.execute(f"SELECT * FROM users WHERE username='{username}'")
                    rows = db.fetchall()
                    if not rows:
                        db.execute("INSERT INTO users (username, hashvalue, firstname, lastname, country) VALUES(?,?,?,?,?)", (
                            username, hashed, firstName, lastName, country))
                        con.commit()
                    else:
                        return message("This username is already exists. Please try another one!")
        return redirect("/login")


@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    if request.method == "GET":
        now = datetime.now()
        hour = int(now.strftime("%H"))
        greeting = "morning"
        if hour >= 12 and hour < 18:
            greeting = "afternoon"
        elif hour >=18 and hour < 5:
            greeting = "evening"
        with sqlite3.connect("gallery.db") as con:
            db = con.cursor()
            db.execute(
                f"SELECT cash, firstname FROM users WHERE id = {session['user_id']}")
            rows = db.fetchall()
        return render_template("dashboard.html", cash=rows[0][0], name=rows[0][1], greeting=greeting)


@app.route("/addCash", methods=["POST"])
@login_required
def addCash():
    if request.method == "POST":
        cash = int(request.form.get("moreCash"))
        # Establish a connection with database and update cash
        with sqlite3.connect("gallery.db") as con:
            db = con.cursor()
            db.execute(
                f"SELECT cash FROM users WHERE id = {session['user_id']}")
            rows = db.fetchall()
            cash = cash + rows[0][0]
            db.execute(
                f"UPDATE users SET cash = {cash} WHERE id = {session['user_id']}")
            con.commit()
        return redirect("/dashboard")
    else:
        return redirect("/dashboard")


@app.route("/changeUsername", methods=["POST"])
@login_required
def changeUsername():
    if request.method == "POST":
        username = request.form.get("newUsername")
        if username == " ":
            return message("Please provide a username!")            
        # Establish a connection with database and update username
        with sqlite3.connect("gallery.db") as con:
            db = con.cursor()
            db.execute(f"SELECT * FROM users WHERE username = '{username}'")
            rows = db.fetchall()
            if len(rows) > 0:
                return message("Username already exists")
            db.execute(
                f"UPDATE users SET username = '{username}' WHERE id = {session['user_id']}")
            db.execute(f"UPDATE paintings SET seller = '{username}' WHERE seller = '{session['user_name']}'")
            con.commit()
            session['user_name'] = username
            return redirect("/login")
    else:
        return redirect("/dashboard")


@app.route("/changePassword", methods=["POST"])
@login_required
def changePassword():
    if request.method == "POST":
        password = request.form.get("newPassword")
        hashed = generate_password_hash(
            password, method='pbkdf2:sha256', salt_length=8)
        # Establish a connection with database and update password
        with sqlite3.connect("gallery.db") as con:
            db = con.cursor()
            db.execute(
                f"UPDATE users SET hashvalue = '{hashed}' WHERE id = {session['user_id']}")
            con.commit()
        return redirect("/login")
    else:
        return redirect("/dashboard")


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
            if not rows:
                return render_template("buy.html", empty=True)
        return render_template("buy.html", rows=rows)
    else:
        return redirect("/")


@app.route("/addToCart", methods=["GET", "POST"])
@login_required
def addToCart():
    if request.method == "POST":
        paintingId = int(request.form.get("id"))
        if not paintingId:
            return message("No Painting Id")
        with sqlite3.connect("gallery.db") as con:
            db = con.cursor()
            db.execute(f"SELECT * FROM cart WHERE user_id = {session['user_id']}")
            rows = db.fetchall()
            for row in rows:
                if paintingId == row[2]:
                    return message("Item already in cart!")
            else:
                db.execute(
                    "INSERT INTO cart (user_id, painting_id) VALUES(?,?)", (session["user_id"], paintingId))
                con.commit()
        return redirect("/buy")
    else:
        return redirect("/buy")


@app.route("/removeFromCart", methods=["POST"])
@login_required
def removeFromCart():
    if request.method == "POST":
        paintingId = int(request.form.get("target"))
        if not paintingId:
            return message("Painting Id not found in cart!")
        with sqlite3.connect("gallery.db") as con:
            db = con.cursor()
            db.execute(f"DELETE FROM cart WHERE user_id = {session['user_id']} AND painting_id = {paintingId}")
            con.commit()
        return redirect("/cart")
    else:
        return redirect("/cart")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    if request.method == "GET":
        return render_template("sell.html")
    else:
        if request.files:
            image = request.files["artImage"]
            if image.filename == "":
                return message("Not a valid filename")
            if allowed_image(image.filename):
                now = datetime.now()
                formattedDate = now.strftime('%Y-%m-%d %H:%M:%S')
                filename = secure_filename(image.filename)
                # To make the filename unique
                extension = splitext(filename)[1]
                filename = splitext(filename)[0]
                filename = filename + \
                    re.sub('[^a-zA-Z0-9_]+', "", formattedDate) + extension
                address = join(app.config["UPLOAD_FOLDER"], filename)
                image.save(address)
                title = request.form.get("title")
                artist = request.form.get("artist")
                price = int(request.form.get("price"))
                if not title or not price or not artist:
                    return message("All the info was not provided")
                with sqlite3.connect("gallery.db") as con:
                    db = con.cursor()
                    db.execute(
                        "INSERT INTO paintings (title, artist, price, seller, imageAddress, additiondate) VALUES(?,?,?,?,?,?)", (title, artist, price, session["user_name"], address, formattedDate))
                    db.execute(f"SELECT * FROM users WHERE id={session['user_id']}")
                    rows = db.fetchall()
                    if not rows:
                        return message("Error in retrieving data from the database!")
                    cash = rows[0][6]
                    db.execute(f"UPDATE users SET cash={cash + price} where id={session['user_id']}")
                    con.commit()
                return redirect(url_for('sold'))
            else:
                return message("That file extension is not allowed")
        else:
            return message("Upload unsuccessful!")

@app.route("/sold", methods=["GET"])
@login_required
def sold():
    if request.method == "GET":
        return render_template("sold.html")
    return redirect("/")


@app.route("/cart", methods=["GET", "POST"])
@login_required
def cart():
    if request.method == "GET":
        with sqlite3.connect("gallery.db") as con:
            db = con.cursor()
            myQuery = f"SELECT * FROM paintings WHERE id IN (SELECT painting_id FROM cart WHERE user_id= {session['user_id']})"
            db.execute(myQuery)
            rows = db.fetchall()
            if not rows:
                return render_template("cart.html", empty=True)
            total = 0
            for row in rows:
                total = total + row[3]
        return render_template("cart.html", rows=rows, total=total)
    else:
        with sqlite3.connect("gallery.db") as con:
            db = con.cursor()
            db.execute(f"SELECT * FROM users WHERE id = {session['user_id']}")
            rows = db.fetchall()
            cash = rows[0][6]
            total = int(request.form.get("total"))
            if not total:
                return message("No value in total!")
            if total > cash:
                return message("You don't have enough funds for the puchase!")
            else:
                db.execute(f"UPDATE users SET cash = {cash - total} WHERE id = {session['user_id']}")
            db.execute(
                f"DELETE FROM paintings WHERE id IN (SELECT painting_id FROM cart WHERE user_id = {session['user_id']})")
            db.execute(
                f"DELETE FROM cart WHERE user_id = {session['user_id']}")
            con.commit()
        return redirect("/bought")


@app.route("/bought", methods=["GET"])
@login_required
def bought():
    if request.method == "GET":
        return render_template("bought.html")
    return redirect("/")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return message("Internal Server Error!")


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

if __name__ == "__main__":
    app.run(debug=True)
