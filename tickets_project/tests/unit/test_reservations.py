import os
import unittest
from datetime import date, datetime
from unittest import mock as mock

from tickets_project import create_app
from tickets_project.models.reservation import Reservation
from tickets_project.models.train_card import SUPPORTED_CARD_TYPES, TrainCard
from tickets_project.models.trip import Trip
from tickets_project.reservations import (calculate_discount,
                                          validate_available_tickets)
from tickets_project.trips import DATETIME_FORMAT


class TestReservations(unittest.TestCase):
    @mock.patch.dict(
        os.environ, {"APP_SECRET": "UNIT_TEST", "FLASK_APP": "tickets_project"}
    )
    def setUp(self) -> None:
        self.app = create_app()

    def test_reservation_create_success(self):
        """
        Verify that creating a reservation with valid data doesn't raise an error.
        After it has been created, verify it is not paid.
        """
        with self.app.app_context():
            try:
                res = Reservation(ticket_numbers=5, sum_price=125.5, has_child=False)
            except ValueError as e:
                self.fail(e)

            # validate that after it has been created,
            # the reservation is not paid for
            self.assertFalse(res.is_paid_for)

    def test_reservation_number_of_tickets(self):
        """
        Verify that creating a reservation with different number of tickets behave as expected.
        1. Negative number of tickets should raise an error.
        2. For the number of tickets between 1 and the available seats for the trip, the reservation should be successful.
        3. For number of tickets > available seats, an error should be raised.
        """
        with self.app.app_context():
            # Valid scenario - 2.
            try:
                Reservation(ticket_numbers=5, sum_price=125.5, has_child=False)
            except ValueError as e:
                self.fail(e)

            # Invalid scenarios - 1. and 3.
            with self.assertRaises(ValueError):
                Reservation(ticket_numbers=-2, sum_price=125.5, has_child=False)

            with self.assertRaises(ValueError):
                res = Reservation(ticket_numbers=22, sum_price=125.5, has_child=False)
                validate_available_tickets(
                    num_of_tickets=res.ticket_numbers, available_seats=20
                )

    def create_test_trips_for_discounts(self, mock_dt, base_ticket_price=10):
        """
        Create test trips to use when calculating discounts.
        """
        dep_datetime = date.strftime(date(2024, 3, 25), "%Y-%m-%d") + "T8:00"
        arr_datetime = date.strftime(date(2024, 3, 25), "%Y-%m-%d") + "T8:30"

        rush_hour_trip = Trip(
            departure_city="Sofia",
            arrival_city="Varna",
            departure_datetime=datetime.strptime(dep_datetime, DATETIME_FORMAT),
            arrival_datetime=datetime.strptime(arr_datetime, DATETIME_FORMAT),
            available_seats=100,
            base_ticket_price=base_ticket_price,
            two_way_trip=False,
        )

        dep_datetime = date.strftime(date(2024, 3, 25), "%Y-%m-%d") + "T15:15"
        arr_datetime = date.strftime(date(2024, 3, 25), "%Y-%m-%d") + "T15:45"

        non_rush_hour_trip = Trip(
            departure_city="Sofia",
            arrival_city="Varna",
            departure_datetime=datetime.strptime(dep_datetime, DATETIME_FORMAT),
            arrival_datetime=datetime.strptime(arr_datetime, DATETIME_FORMAT),
            available_seats=100,
            base_ticket_price=base_ticket_price,
            two_way_trip=False,
        )

        return (rush_hour_trip, non_rush_hour_trip)

    @mock.patch("tickets_project.models.trip.datetime")
    def test_reservation_time_discount(self, mock_dt):
        """
        Test that discounts based on the time (rush hour or not) work.
        """
        mock_dt.now = mock.Mock(return_value=datetime(2024, 3, 25))
        rush_hour_trip, non_rush_hour_trip = self.create_test_trips_for_discounts(
            mock_dt
        )

        self.assertEqual(
            50,
            calculate_discount(
                rush_hour_trip, card=None, num_of_tickets=5, has_child=False
            ),
        )
        self.assertEqual(
            50,
            calculate_discount(
                rush_hour_trip, card=None, num_of_tickets=5, has_child=True
            ),
        )
        self.assertEqual(
            47.5,
            calculate_discount(
                non_rush_hour_trip, card=None, num_of_tickets=5, has_child=True
            ),
        )

    @mock.patch("tickets_project.models.trip.datetime")
    def test_reservation_age_card_discount(self, mock_dt):
        """
        Test that discounts based on the "age" type of train card work.
        """
        mock_dt.now = mock.Mock(return_value=datetime(2024, 3, 25))
        rush_hour_trip, non_rush_hour_trip = self.create_test_trips_for_discounts(
            mock_dt
        )

        self.assertEqual(
            46.6,
            calculate_discount(
                rush_hour_trip,
                card=TrainCard(card_type=SUPPORTED_CARD_TYPES[0]),
                num_of_tickets=5,
                has_child=False,
            ),
        )
        self.assertEqual(
            46.6,
            calculate_discount(
                rush_hour_trip,
                card=TrainCard(card_type=SUPPORTED_CARD_TYPES[0]),
                num_of_tickets=5,
                has_child=True,
            ),
        )
        self.assertEqual(
            44.6,
            calculate_discount(
                non_rush_hour_trip,
                card=TrainCard(card_type=SUPPORTED_CARD_TYPES[0]),
                num_of_tickets=5,
                has_child=False,
            ),
        )

    @mock.patch("tickets_project.models.trip.datetime")
    def test_reservation_family_card_discount(self, mock_dt):
        """
        Test that discounts based on the "family" type of train card work.
        """
        mock_dt.now = mock.Mock(return_value=datetime(2024, 3, 25))
        rush_hour_trip, non_rush_hour_trip = self.create_test_trips_for_discounts(
            mock_dt
        )

        self.assertEqual(
            45,
            calculate_discount(
                rush_hour_trip,
                card=TrainCard(card_type=SUPPORTED_CARD_TYPES[1]),
                num_of_tickets=5,
                has_child=False,
            ),
        )
        self.assertEqual(
            25,
            calculate_discount(
                rush_hour_trip,
                card=TrainCard(card_type=SUPPORTED_CARD_TYPES[1]),
                num_of_tickets=5,
                has_child=True,
            ),
        )

        # Since we have enabled discount stacking in the logic
        # (ambigious based on the project description, so I decided to do it:) )
        # we also test for non-rush hour trips where we have an added 5% bonus
        self.assertEqual(
            42.5,
            calculate_discount(
                non_rush_hour_trip,
                card=TrainCard(card_type=SUPPORTED_CARD_TYPES[1]),
                num_of_tickets=5,
                has_child=False,
            ),
        )
        self.assertEqual(
            22.5,
            calculate_discount(
                non_rush_hour_trip,
                card=TrainCard(card_type=SUPPORTED_CARD_TYPES[1]),
                num_of_tickets=5,
                has_child=True,
            ),
        )
