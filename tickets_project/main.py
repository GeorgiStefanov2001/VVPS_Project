from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required

from . import db

main = Blueprint("main", __name__)


@main.route("/")
def index():
    return redirect(url_for("trips.list"))


@main.route("/profile")
@login_required
def profile():
    return render_template("profile.html", firstname=current_user.firstname)
