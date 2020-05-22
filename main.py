from flask import Flask, redirect, url_for, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

# Configure application
app = Flask(__name__, static_url_path='/static')

# Ensure templates are auto-reloaded
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/buy", methods=["GET", "POST"])
def buy():
    if request.method == "GET":
        return render_template("buy.html")
    else:
        return redirect("/")

if __name__ == "__main__":
    app.run()
