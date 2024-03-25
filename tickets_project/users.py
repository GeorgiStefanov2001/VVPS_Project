import os

import bcrypt
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from . import db
from .models.user import User

users = Blueprint("users", __name__)


@users.route("/users/")
@login_required
def list():
    if not current_user.is_admin:
        raise PermissionError("Cannot manage users as current user is not admin")

    users = User.query.all()
    return render_template("/users/list.html", users=users)


@users.route("/login")
def login():
    return render_template("users/login.html")


@users.route("/login", methods=["POST"])
def login_post():
    username = request.form.get("username")
    password = request.form.get("password")

    try:
        validate_login(username, password)
    except ValueError as e:
        flash(str(e), category="error")
        return redirect(url_for("users.login"))

    # credentials are correct - log user in
    user = User.query.filter_by(username=username).first()
    login_user(user, remember=(True if request.form.get("remember") else False))
    return redirect(url_for("trips.list"))


def validate_login(username, password):
    user = User.query.filter_by(username=username).first()
    if not user:
        raise ValueError("Invalid username - user doesn't exist.")
    else:
        # check if password is correct
        hashed_pass = user.password
        password_correct = (
            bcrypt.hashpw(bytes(password, "utf-8"), hashed_pass) == hashed_pass
        )

        if not password_correct:
            raise ValueError("Incorrect password.")


@users.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))


@users.route("/signup")
def signup():
    return render_template(
        "users/signup.html", dev_mode=os.environ.get("DEV_MODE_ENABLED")
    )


@users.route("/signup", methods=["POST"])
def signup_post():
    try:
        # create a new user with the form data. Hash the password so the plaintext version isn't saved.
        new_user = User(
            email=request.form.get("email"),
            username=request.form.get("username"),
            password=bcrypt.hashpw(
                bytes(request.form.get("password"), "utf-8"), bcrypt.gensalt()
            ),
            firstname=request.form.get("firstname"),
            lastname=request.form.get("lastname"),
            age=(int(request.form.get("age")) if request.form.get("age") else -1),
            is_admin=(True if request.form.get("is_admin") else False),
        )
        # add the new user to the database
        db.session.add(new_user)
        db.session.commit()
    except ValueError as e:
        flash(str(e), category="error")
        return redirect(url_for("users.signup"))

    return redirect(url_for("users.login"))


@users.route("/users/<int:id>")
@login_required
def edit(id):
    if not current_user.is_admin:
        raise PermissionError("Cannot edit user as current user is not admin")

    user = User.query.filter_by(id=id).first()
    if not user:
        flash(f"User with id {id} doesn't exist!", category="error")
        return redirect(url_for("users.list"))

    return render_template("/users/edit.html", user=user)


@users.route("/users/<int:id>", methods=["POST"])
@login_required
def edit_post(id):
    if not current_user.is_admin:
        raise PermissionError("Cannot edit user as current user is not admin")

    user = User.query.filter_by(id=id).first()
    if not user:
        flash(f"User with id {id} doesn't exist!", category="error")
        return redirect(url_for("users.list"))

    try:
        # update user
        if not request.form.get("email") == user.email:
            user.email = request.form.get("email")
        if not request.form.get("username") == user.username:
            user.username = request.form.get("username")
        user.firstname = request.form.get("firstname")
        user.lastname = request.form.get("lastname")
        user.age = int(request.form.get("age")) if request.form.get("age") else -1
        user.is_admin = True if request.form.get("is_admin") else False

        # update the user in the database
        db.session.commit()
    except ValueError as e:
        flash(str(e), category="error")
        return redirect(url_for("users.edit", id=user.id))

    flash("User successfully updated", category="info")
    return redirect(url_for("users.edit", id=user.id))
