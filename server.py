"""
Authentication microservice for Atlassian Crowd

@author Jerry Chong
"""

import crowd
import argparse
from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.exceptions import Unauthorized

CROWD_URL = "your crowd URL"
CROWD_USER = "abc"
CROWD_PASS = "abc"
CROWD_SERVER = crowd.CrowdServer(CROWD_URL, CROWD_USER, CROWD_PASS)
app = Flask(__name__)
app.config.update(
    SECRET_KEY="your crowd secret",
    SESSION_COOKIE_DOMAIN="your root domain"
)


@app.route("/auth")
def authenticate():
    # verify if crowd token is valid, otherwise redirect
    token = session.get("token")
    user = session.get("crowd_user")
    if token and CROWD_SERVER.validate_session(token):
        if user:
            return ('', {"X-CROWD-USER": user})
        else:
            return ''  # = 200 OK
    else:
        raise Unauthorized  # = 401 unauthorized


# Deprecated: define HTTP redirects on the web server directly!
@app.route("/auth/redirect")
def authenticate_begin():
    # initiate login session
    host = request.headers["Host"]
    callback = request.headers["X-Callback"]
    app.logger.info("New login from host: %s callback: %s", host, callback)
    return redirect(url_for("login", next=callback))


@app.route("/login", methods=["GET", "POST"])
def login():
    # if get, render a login page, else verify
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        callback = request.form["next"]
        if isinstance(callback, str) and len(callback.strip()) == 0:
            callback = None

        crowd_session = CROWD_SERVER.get_session(username, password)
        if crowd_session:
            # logged in successfully, merge crowd JSON into session
            session.update(crowd_session)
            session["crowd_user"] = crowd_session["user"]["name"]
            app.logger.debug("User %s <%s> logged in.",
                             crowd_session["user"]["display-name"],
                             crowd_session["user"]["email"])
            return redirect(callback or url_for("index"))
        else:
            # failed
            app.logger.info("User %s unauthorized.", username)
            session["error"] = "Username or password incorrect!"
            return redirect(url_for("login", next=callback))
    else:
        # render a login page
        return render_template("login.html",
                               error=session.pop("error", ""),
                               next=request.args.get("next", ""))


@app.route("/logout")
def logout():
    app.logger.debug("User logged out.")
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
def index():
    # plain index page
    return redirect(url_for("login"))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", "-p", default=9000)
    p.add_argument("--debug", "-d", action="store_true", default=False)
    args = p.parse_args()

    # debug mode will allow use of localhost in sessions
    if args.debug:
        app.config.update(DEBUG=True, SESSION_COOKIE_DOMAIN=None)

    app.run(host=args.host, port=args.port, threaded=True)
