from flask import session, redirect, render_template
from functools import wraps
from datetime import datetime

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def format_date(datetimeinput):
    """ Make the dates look more appealing """
    
    return datetime.strptime(datetimeinput, "%Y-%m-%d %H:%M:%S").strftime("%b %d, %Y.")

def message(message):
    return render_template("message.html", message=message)