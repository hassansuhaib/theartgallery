from flask import session, redirect
from functools import wraps

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

def convert_to_binary(filename):
    # Convert the images into binary to store in Database
    with open(filename, 'rb') as file:
        blobData = file.read()
    return blobData



