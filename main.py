from flask import Flask, redirect, url_for, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from brains import login_required
import sqlite3

# Configure application
app = Flask(__name__, static_url_path='/static')

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Establish a connection with the database
db = sqlite3.connect('gallery.db')
if conn:
    print("Database connected successfully")
else:
    print("Couldn't open the database!")

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
        rows = db.execute("SELECT * FROM users WHERE username = :username", username = request.form.get("username"))

        if rows != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password"))
            return "<h1>Wrong username or password!</h1>"
        
        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
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
        
        return redirect("/")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/buy", methods=["GET", "POST"])
def buy():
    if request.method == "GET":
        return render_template("buy.html")
    else:
        return redirect("/")

@app.route("/sell", methods=["GET", "POST"])
def sell():
    if request.method == "GET":
        return render_template("sell.html")
    else:
        return redirect("/")

@app.route("/cart", methods=["GET", "POST"])
def cart():
    if request.method == "GET":
        return render_template("cart.html")
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
