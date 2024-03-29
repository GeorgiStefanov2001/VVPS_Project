import unittest

from tickets_project import create_app
from tickets_project.models.train_card import SUPPORTED_CARD_TYPES, TrainCard


class TestCards(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app()

    def test_card_create_success(self):
        """
        Verify that creating a card with valid data doesn't raise an error.
        """
        with self.app.app_context():
            try:
                for type in SUPPORTED_CARD_TYPES:
                    TrainCard(card_type=type)
            except ValueError as e:
                self.fail(e)

    def test_card_invalid_type(self):
        """
        Verify that creating a card with an unsupported type raises an error.
        """
        with self.app.app_context():
            with self.assertRaises(ValueError):
                TrainCard(card_type="not_supported")
