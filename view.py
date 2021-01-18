from flask import render_template, current_app, abort, request, redirect, url_for
from app import session


def home_page():
    return render_template("home.html", session=session)


def login_page():
    return render_template("login.html")


def sign_up_page():
    return render_template("sign_up.html")







