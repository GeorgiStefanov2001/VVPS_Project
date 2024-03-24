import datetime

from sqlalchemy.orm import validates

from .. import db
from .trip import Trip


class Reservation(db.Model):
    __tablename__ = "reservation"

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now())
    ticket_numbers = db.Column(db.Integer, nullable=False)
    sum_price = db.Column(db.Float, nullable=False)
    has_child = db.Column(db.Boolean, nullable=False, default=False)
    is_paid_for = db.Column(db.Boolean, nullable=False, default=False)
    trip_id = db.Column(db.Integer, db.ForeignKey("trip.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    def __repr__(self):
        return "Reservation #%s for %s tickets for trip %s%s. Sum: %s. Paid: %s" % (
            self.id,
            self.ticket_numbers,
            self.trip_id,
            (" with child onboard" if self.has_child else ""),
            self.sum_price,
            self.is_paid_for,
        )

    @validates("created_at")
    def validate_created_at(self, key, created_at):
        if not created_at:
            raise ValueError("No created at datetime provided")
        return created_at

    @validates("ticket_numbers")
    def validate_ticket_numbers(self, key, ticket_numbers):
        if ticket_numbers is None:
            raise ValueError("No number of tickets provided")
        if ticket_numbers <= 0:
            raise ValueError("Number of tickets should be positive")
        return ticket_numbers

    @validates("sum_price")
    def validate_sum_price(self, key, sum_price):
        if sum_price is None:
            raise ValueError("No sum price of tickets provided")
        if sum_price <= 0:
            raise ValueError("Sum price of tickets should be positive")
        return sum_price
