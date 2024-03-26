import unittest

from tickets_project import create_app
from tickets_project.models.reservation import Reservation
from tickets_project.models.train_card import TrainCard
from tickets_project.models.user import User


class TestUsers(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app()

    def test_user_create_success(self):
        """
        Verify that creating a user with valid data doesn't raise an error.
        """
        with self.app.app_context():
            try:
                User(
                    email="valid@email.bg",
                    username="valid_username",
                    password="strongpass",
                    firstname="test",
                    lastname="test",
                    age=12,
                    is_admin=False,
                )
            except ValueError as e:
                self.fail(e)

    def test_user_create_invalid_email(self):
        """
        Verify that emails that are not valid (don't match the pattern)
        don't get registered
        """
        with self.app.app_context():
            with self.assertRaises(ValueError):
                User(
                    email="valid@email",
                    username="valid_username",
                    password="strongpass",
                    firstname="test",
                    lastname="test",
                    age=12,
                    is_admin=False,
                )

    def test_user_negative_age(self):
        """
        Verify that attempts to create a user with a negative age raise an error.
        """
        with self.app.app_context():
            with self.assertRaises(ValueError):
                User(
                    email="valid@email.com",
                    username="valid_username",
                    password="strongpass",
                    firstname="test",
                    lastname="test",
                    age=-5,
                    is_admin=False,
                )
