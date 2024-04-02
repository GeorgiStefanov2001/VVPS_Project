import os

from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

db = SQLAlchemy()
basedir = os.path.abspath(os.path.dirname(__file__))

DATETIME_FORMAT = "%Y-%m-%dT%H:%M"
SUPPORTED_TRIP_FILTER_TYPES = ["dep_city", "arr_city", "one_way", "two_way"]


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.environ.get("APP_SECRET")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
        basedir, "database.db"
    )

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "users.login"
    login_manager.init_app(app)

    from .models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        db.create_all()

    # blueprints
    from .cards import cards as cards_blueprint
    from .main import main as main_blueprint
    from .reservations import reservations as reservations_blueprint
    from .trips import trips as trips_blueprint
    from .users import users as users_blueprint

    app.register_blueprint(main_blueprint)
    app.register_blueprint(users_blueprint)
    app.register_blueprint(trips_blueprint)
    app.register_blueprint(reservations_blueprint)
    app.register_blueprint(cards_blueprint)

    return app
