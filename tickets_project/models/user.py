import re

from flask_login import UserMixin
from sqlalchemy.orm import validates

from .. import db


class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), unique=True)
    firstname = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    train_card = db.relationship("TrainCard", backref="user", lazy=True, uselist=False)
    reservations = db.relationship("Reservation", backref="user", lazy=True)

    def __repr__(self):
        return "<ID: %s> %s %s (%s %s, aged %s), %s" % (
            self.id,
            ("Admin user" if self.is_admin else "User"),
            self.username,
            self.firstname,
            self.lastname,
            self.age,
            self.email,
        )

    @validates("email")
    def validate_email(self, key, email):
        if not email:
            raise ValueError("No email address provided")
        if User.query.filter_by(email=email).first():
            raise ValueError("Email address is already in use")
        if not re.fullmatch(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b", email
        ):
            raise ValueError("Please enter a valid email")

        return email

    @validates("username")
    def validate_username(self, key, username):
        if not username:
            raise ValueError("No username provided")
        if User.query.filter_by(username=username).first():
            raise ValueError("Username is already in use")

        return username

    @validates("password")
    def validate_password(self, key, password):
        if not password:
            raise ValueError("No password provided")

        return password

    @validates("firstname")
    def validate_firstname(self, key, firstname):
        if not firstname:
            raise ValueError("No first name provided")

        return firstname

    @validates("lastname")
    def validate_lastname(self, key, lastname):
        if not lastname:
            raise ValueError("No last name provided")

        return lastname

    @validates("age")
    def validate_age(self, key, age):
        if age is None:
            raise ValueError("No age provided")
        if age <= 0:
            raise ValueError("Age cannot be negative")

        return age
