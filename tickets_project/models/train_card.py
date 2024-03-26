from flask_login import current_user
from sqlalchemy.orm import validates

from .. import db

SUPPORTED_CARD_TYPES = ["aged", "family"]


class TrainCard(db.Model):
    __tablename__ = "train_card"

    id = db.Column(db.Integer, primary_key=True)
    card_type = db.Column(db.String(100), nullable=False)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True
    )

    @validates("card_type")
    def validate_card_type(self, key, card_type):
        if card_type not in SUPPORTED_CARD_TYPES:
            raise ValueError(f"Card type {card_type} not supported")
        return card_type
