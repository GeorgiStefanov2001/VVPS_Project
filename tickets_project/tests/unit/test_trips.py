import os
import unittest
from datetime import datetime, timedelta
from unittest import mock as mock

from tickets_project import create_app
from tickets_project.models.reservation import Reservation
from tickets_project.models.trip import Trip
from tickets_project.trips import (DATETIME_FORMAT, filter_trips,
                                   validate_trip_input)


class TestTrips(unittest.TestCase):
    @mock.patch.dict(
        os.environ, {"APP_SECRET": "UNIT_TEST", "FLASK_APP": "tickets_project"}
    )
    def setUp(self) -> None:
        self.app = create_app()

    @mock.patch("tickets_project.models.trip.datetime")
    def test_trip_create_success(self, mock_dt):
        """
        Verify that creating a trip with valid data doesn't raise an error.
        """
        mock_dt.now = mock.Mock(return_value=datetime(2024, 3, 25))
        with self.app.app_context():
            try:
                Trip(
                    departure_city="Sofia",
                    arrival_city="Varna",
                    departure_datetime=datetime(2024, 3, 25) + timedelta(days=1),
                    arrival_datetime=datetime(2024, 3, 25) + timedelta(days=2),
                    available_seats=10,
                    base_ticket_price=12.5,
                    two_way_trip=False,
                )
            except ValueError as e:
                self.fail(e)

    @mock.patch("tickets_project.models.trip.datetime")
    def test_trip_create_departure_datetime_in_past(self, mock_dt):
        """
        Verify that departure datetimes in the past raise errors.
        """
        mock_dt.now = mock.Mock(return_value=datetime(2024, 3, 25))
        with self.app.app_context():
            with self.assertRaises(ValueError):
                Trip(
                    departure_city="Sofia",
                    arrival_city="Varna",
                    departure_datetime=datetime(2024, 3, 24),
                    arrival_datetime=datetime(2024, 3, 25),
                    available_seats=10,
                    base_ticket_price=12.5,
                    two_way_trip=False,
                )

    @mock.patch("tickets_project.trips.datetime")
    def test_trip_creation_arrival_before_departure(self, mock_dt):
        """
        Verify that when arrival datetime is before departure datetime, errors are raised.
        """
        mock_dt.now = mock.Mock(return_value=datetime(2024, 3, 25))
        mock_dt.strptime = datetime.strptime
        with self.app.app_context():
            departure_datetime = datetime.strftime(
                datetime(2024, 3, 25) + timedelta(days=2), DATETIME_FORMAT
            )
            arrival_datetime = datetime.strftime(
                datetime(2024, 3, 25) + timedelta(days=1), DATETIME_FORMAT
            )

            with self.assertRaises(ValueError):
                validate_trip_input(
                    {
                        "departure_datetime": departure_datetime,
                        "arrival_datetime": arrival_datetime,
                    }
                )

    @mock.patch("tickets_project.models.trip.datetime")
    def test_trip_create_negative_numeric_fields(self, mock_dt):
        """
        Verify that negative numberic inputs will raise an error.
        Available_seats and base_ticket_price cannot be negative.
        """
        mock_dt.now = mock.Mock(return_value=datetime(2024, 3, 25))
        with self.app.app_context():
            # 1. Negative available seats
            with self.assertRaises(ValueError):
                Trip(
                    departure_city="Sofia",
                    arrival_city="Varna",
                    departure_datetime=datetime(2024, 3, 25) + timedelta(days=1),
                    arrival_datetime=datetime(2024, 3, 25) + timedelta(days=2),
                    available_seats=-5,
                    base_ticket_price=12.5,
                    two_way_trip=False,
                )

            # 2. Negative base ticket price
            with self.assertRaises(ValueError):
                Trip(
                    departure_city="Sofia",
                    arrival_city="Varna",
                    departure_datetime=datetime(2024, 3, 25) + timedelta(days=1),
                    arrival_datetime=datetime(2024, 3, 25) + timedelta(days=2),
                    available_seats=5,
                    base_ticket_price=-5,
                    two_way_trip=False,
                )

    def test_trip_create_same_departure_arrival_cities(self):
        """
        Verify that when the arrival and departure cities are the same, an error would be raised.
        (this really depends on customer requirements, but I decided to do it this way)
        """

        with self.app.app_context():
            # testing different capitalizations
            invalid_combos = [
                {"departure_city": "Sofia", "arrival_city": "Sofia"},
                {"departure_city": "sofia", "arrival_city": "Sofia"},
                {"departure_city": "Sofia", "arrival_city": "sofia"},
                {"departure_city": "SofIA", "arrival_city": "sofia"},
            ]  # ...

            for combo in invalid_combos:
                with self.assertRaises(ValueError):
                    validate_trip_input(combo)

    @mock.patch("tickets_project.models.trip.datetime")
    def create_test_trips(self, mock_dt):
        """
        Creating test trips for filtering tests.
        """
        mock_dt.now = mock.Mock(return_value=datetime(2024, 3, 25))
        with self.app.app_context():
            trip1 = Trip(
                departure_city="Sofia",
                arrival_city="Varna",
                departure_datetime=datetime(2024, 3, 25) + timedelta(days=1),
                arrival_datetime=datetime(2024, 3, 25) + timedelta(days=2),
                available_seats=5,
                base_ticket_price=12.5,
                two_way_trip=True,
            )
            trip2 = Trip(
                departure_city="Sofia",
                arrival_city="Pleven",
                departure_datetime=datetime(2024, 3, 25) + timedelta(days=1),
                arrival_datetime=datetime(2024, 3, 25) + timedelta(days=2),
                available_seats=5,
                base_ticket_price=12.5,
                two_way_trip=True,
            )
            trip3 = Trip(
                departure_city="Pleven",
                arrival_city="Varna",
                departure_datetime=datetime(2024, 3, 25) + timedelta(days=1),
                arrival_datetime=datetime(2024, 3, 25) + timedelta(days=2),
                available_seats=5,
                base_ticket_price=12.5,
                two_way_trip=False,
            )

            return [trip1, trip2, trip3]

    def test_trip_filter_by_cities(self):
        """
        Verify that trip filtering by destination/arrival cities works.
        """
        trips = self.create_test_trips()
        self.assertEqual([trips[0], trips[1]], filter_trips(trips, "dep_city", "Sofia"))
        self.assertEqual([trips[0], trips[2]], filter_trips(trips, "arr_city", "Varna"))

    def test_trip_filter_by_bidirectionality(self):
        """
        Verify that trip filtering by whether they are one-way or two-way works.
        """
        trips = self.create_test_trips()
        self.assertEqual([trips[0], trips[1]], filter_trips(trips, "two_way", ""))
        self.assertEqual([trips[2]], filter_trips(trips, "one_way", ""))
