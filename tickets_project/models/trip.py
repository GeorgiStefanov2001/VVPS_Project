import datetime

from sqlalchemy.orm import validates

from .. import db


class Trip(db.Model):
    __tablename__ = "trip"

    id = db.Column(db.Integer, primary_key=True)
    departure_datetime = db.Column(db.DateTime, nullable=False)
    arrival_datetime = db.Column(db.DateTime, nullable=False)
    departure_city = db.Column(db.String(100), nullable=False)
    arrival_city = db.Column(db.String(100), nullable=False)
    two_way_trip = db.Column(db.Boolean, nullable=False, default=False)
    available_seats = db.Column(db.Integer, nullable=False)
    base_ticket_price = db.Column(db.Float, nullable=False)
    reservations = db.relationship("Reservation", backref="trip", lazy=True)

    def __repr__(self):
        return (
            "%s trip from %s (%s) to %s (%s). Available seats: %s, Base ticket price: %s"
            % (
                ("Two-way" if self.two_way_trip else "One-way"),
                self.departure_city,
                self.departure_datetime,
                self.arrival_city,
                self.arrival_datetime,
                self.available_seats,
                self.base_ticket_price,
            )
        )

    @validates("departure_datetime")
    def validate_departure_datetime(self, key, departure_datetime):
        if not departure_datetime:
            raise ValueError("No departure datetime provided")
        if departure_datetime < datetime.datetime.now():
            raise ValueError("Departure time cannot be in the past")
        return departure_datetime

    @validates("arrival_datetime")
    def validate_arrival_datetime(self, key, arrival_datetime):
        if not arrival_datetime:
            raise ValueError("No arrival datetime provided")
        return arrival_datetime

    @validates("departure_city")
    def validate_departure_city(self, key, departure_city):
        if not departure_city:
            raise ValueError("No departure city provided")
        return departure_city

    @validates("arrival_city")
    def validate_arrival_city(self, key, arrival_city):
        if not arrival_city:
            raise ValueError("No arrival city provided")
        return arrival_city

    @validates("available_seats")
    def validate_available_seats(self, key, available_seats):
        if available_seats is None:
            raise ValueError("No available seats provided")
        if available_seats < 0:
            raise ValueError("Available seats cannot be negative")

        return available_seats

    @validates("base_ticket_price")
    def validate_base_ticket_price(self, key, base_ticket_price):
        if base_ticket_price is None:
            raise ValueError("No base ticket price provided")
        if base_ticket_price <= 0:
            raise ValueError("Base ticket price must be a positive number")

        return base_ticket_price
