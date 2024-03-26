import datetime
import unittest

from tickets_project import create_app
from tickets_project.models.reservation import Reservation
from tickets_project.models.trip import Trip
from tickets_project.trips import (DATETIME_FORMAT, filter_trips,
                                   validate_trip_input)


class TestTrips(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app()

    def test_trip_create_success(self):
        """
        Verify that creating a trip with valid data doesn't raise an error.
        """
        with self.app.app_context():
            try:
                Trip(
                    departure_city="Sofia",
                    arrival_city="Varna",
                    departure_datetime=datetime.datetime.now()
                    + datetime.timedelta(days=1),
                    arrival_datetime=datetime.datetime.now()
                    + datetime.timedelta(days=2),
                    available_seats=10,
                    base_ticket_price=12.5,
                    two_way_trip=False,
                )
            except ValueError as e:
                self.fail(e)

    def test_trip_create_invalid_datetimes(self):
        """
        Verify that passing invalid datetimes upon trip creation raise errrors.
        """
        with self.app.app_context():
            # 1. Departure datetime is in the past
            with self.assertRaises(ValueError):
                Trip(
                    departure_city="Sofia",
                    arrival_city="Varna",
                    departure_datetime=datetime.datetime.now()
                    - datetime.timedelta(days=1),
                    arrival_datetime=datetime.datetime.now()
                    + datetime.timedelta(days=1),
                    available_seats=10,
                    base_ticket_price=12.5,
                    two_way_trip=False,
                )

            # 2. Arrival datetime is before departure datetime
            # using the validate_trip_input
            departure_datetime = datetime.datetime.strftime(
                datetime.datetime.now() + datetime.timedelta(days=2), DATETIME_FORMAT
            )
            arrival_datetime = datetime.datetime.strftime(
                datetime.datetime.now() + datetime.timedelta(days=1), DATETIME_FORMAT
            )

            with self.assertRaises(ValueError):
                validate_trip_input(
                    {
                        "departure_datetime": departure_datetime,
                        "arrival_datetime": arrival_datetime,
                    }
                )

    def test_trip_create_invalid_input(self):
        """
        Verify that invalid inputs will raise an error.
        """
        with self.app.app_context():
            # 1. Available_seats and base_ticket_price cannot be negative
            with self.assertRaises(ValueError):
                Trip(
                    departure_city="Sofia",
                    arrival_city="Varna",
                    departure_datetime=datetime.datetime.now()
                    + datetime.timedelta(days=1),
                    arrival_datetime=datetime.datetime.now()
                    + datetime.timedelta(days=2),
                    available_seats=-5,
                    base_ticket_price=12.5,
                    two_way_trip=False,
                )

            with self.assertRaises(ValueError):
                Trip(
                    departure_city="Sofia",
                    arrival_city="Varna",
                    departure_datetime=datetime.datetime.now()
                    + datetime.timedelta(days=1),
                    arrival_datetime=datetime.datetime.now()
                    + datetime.timedelta(days=2),
                    available_seats=5,
                    base_ticket_price=-5,
                    two_way_trip=False,
                )

            # 2. Arrival and departure cities cannot be the same
            # (this really depends on customer requirements, but I decided to do it this way)
            invalid_combos = [
                {"departure_city": "Sofia", "arrival_city": "Sofia"},
                {"departure_city": "sofia", "arrival_city": "Sofia"},
                {"departure_city": "Sofia", "arrival_city": "sofia"},
                {"departure_city": "SofIA", "arrival_city": "sofia"},
            ]  # ...

            for combo in invalid_combos:
                with self.assertRaises(ValueError):
                    validate_trip_input(combo)

    def test_trip_filter(self):
        """
        Verify that trip filtering works.
        """
        with self.app.app_context():
            trip1 = Trip(
                departure_city="Sofia",
                arrival_city="Varna",
                departure_datetime=datetime.datetime.now() + datetime.timedelta(days=1),
                arrival_datetime=datetime.datetime.now() + datetime.timedelta(days=2),
                available_seats=5,
                base_ticket_price=12.5,
                two_way_trip=True,
            )
            trip2 = Trip(
                departure_city="Sofia",
                arrival_city="Pleven",
                departure_datetime=datetime.datetime.now() + datetime.timedelta(days=1),
                arrival_datetime=datetime.datetime.now() + datetime.timedelta(days=2),
                available_seats=5,
                base_ticket_price=12.5,
                two_way_trip=True,
            )
            trip3 = Trip(
                departure_city="Pleven",
                arrival_city="Varna",
                departure_datetime=datetime.datetime.now() + datetime.timedelta(days=1),
                arrival_datetime=datetime.datetime.now() + datetime.timedelta(days=2),
                available_seats=5,
                base_ticket_price=12.5,
                two_way_trip=False,
            )

            self.assertEqual(
                [trip1, trip2], filter_trips([trip1, trip2, trip3], "dep_city", "Sofia")
            )
            self.assertEqual(
                [trip1, trip3], filter_trips([trip1, trip2, trip3], "arr_city", "Varna")
            )
            self.assertEqual(
                [trip1, trip2], filter_trips([trip1, trip2, trip3], "two_way", "")
            )
            self.assertEqual(
                [trip3], filter_trips([trip1, trip2, trip3], "one_way", "")
            )
