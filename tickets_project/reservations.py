import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from . import db
from .models.reservation import Reservation
from .models.train_card import SUPPORTED_CARD_TYPES, TrainCard
from .models.trip import Trip

reservations = Blueprint("reservations", __name__)


@reservations.route("/reservations/")
@login_required
def list():
    if current_user.is_admin:
        reservations = Reservation.query.all()
    else:
        reservations = Reservation.query.filter_by(user_id=current_user.id)

    paid_reservations = []
    for reservation in reservations:
        if not reservation.is_paid_for and (
            (datetime.datetime.now() - reservation.created_at).days > 7
        ):
            # it is unpaid for for longer than a week, delete it :)
            db.session.delete(reservation)
            continue

        paid_reservations.append(reservation)

    return render_template("/reservations/list.html", reservations=paid_reservations)


@reservations.route("/reservations/<int:id>/pay", methods=["POST"])
@login_required
def pay(id):
    reservation = Reservation.query.filter_by(id=id).first()
    if not reservation:
        flash(f"Reservation with id {id} doesn't exist!", category="error")
        return redirect(url_for("reservations.list"))
    reservation.is_paid_for = True

    db.session.commit()
    return redirect(url_for("reservations.list"))


@reservations.route("/trips/<int:trip_id>/reserve")
@login_required
def create(trip_id):
    trip = Trip.query.filter_by(id=trip_id).first()
    if not trip:
        flash(f"Trip with id {id} doesn't exist!", category="error")
        return redirect(url_for("trips.list"))
    return render_template("/reservations/create.html", trip=trip)


@reservations.route("/trips/<int:trip_id>/reserve", methods=["POST"])
@login_required
def create_post(trip_id):
    trip = Trip.query.filter_by(id=trip_id).first()
    if not trip:
        flash(f"Trip with id {id} doesn't exist!", category="error")
        return redirect(url_for("trips.list"))

    try:
        # calculate discount
        num_of_tickets = (
            int(request.form.get("ticket_numbers"))
            if request.form.get("ticket_numbers")
            else -1
        )
        validate_available_tickets(num_of_tickets, trip.available_seats)

        has_child = bool(request.form.get("has_child"))

        card = TrainCard.query.filter_by(user_id=current_user.id).first()
        final_price = calculate_discount(trip, card, num_of_tickets, has_child)

        # create a new trip with the form data.
        new_reservation = Reservation(
            ticket_numbers=num_of_tickets,
            sum_price=final_price,
            has_child=has_child,
            is_paid_for=False,
            trip_id=trip_id,
            user_id=current_user.id,
        )
        trip.available_seats -= num_of_tickets

        # add the new trip to the database
        db.session.add(new_reservation)
        db.session.commit()
    except ValueError as e:
        flash(str(e), category="error")
        return redirect(url_for("reservations.create", trip_id=trip.id))

    return redirect(url_for("reservations.list"))


@reservations.route("/reservations/<int:id>")
@login_required
def edit(id):
    reservation = Reservation.query.filter_by(id=id).first()
    if not reservation:
        flash(f"Reservation with id {id} doesn't exist!", category="error")
        return redirect(url_for("reservations.list"))

    trip = Trip.query.filter_by(id=reservation.trip_id).first()
    return render_template(
        "/reservations/edit.html", reservation=reservation, trip=trip
    )


@reservations.route("/reservations/<int:id>", methods=["POST"])
@login_required
def edit_post(id):
    reservation = Reservation.query.filter_by(id=id).first()
    if not reservation:
        flash(f"Reservation with id {id} doesn't exist!", category="error")
        return redirect(url_for("reservations.list"))

    trip = Trip.query.filter_by(id=reservation.trip_id).first()

    try:
        num_of_tickets = (
            int(request.form.get("ticket_numbers"))
            if request.form.get("ticket_numbers")
            else -1
        )
        validate_available_tickets(
            num_of_tickets, (trip.available_seats + reservation.ticket_numbers)
        )

        has_child = bool(request.form.get("has_child"))
        card = TrainCard.query.filter_by(user_id=current_user.id).first()
        final_price = calculate_discount(trip, card, num_of_tickets, has_child)

        # update reservation
        trip.available_seats += reservation.ticket_numbers
        reservation.ticket_numbers = num_of_tickets
        reservation.has_child = has_child
        reservation.sum_price = final_price

        # update trip available seats
        trip.available_seats -= num_of_tickets

        # update the reservation in the database
        db.session.commit()
    except ValueError as e:
        flash(str(e), category="error")
        return redirect(url_for("reservations.edit", id=reservation.id, trip=trip))

    flash("Reservation successfully updated", category="info")
    return redirect(url_for("reservations.edit", id=reservation.id, trip=trip))


@reservations.route("/reservations/<int:id>/delete", methods=["POST"])
@login_required
def delete(id):
    reservation = Reservation.query.filter_by(id=id).first()
    if not reservation:
        flash(f"Reservation with id {id} doesn't exist!", category="error")
        return redirect(url_for("reservations.list"))

    trip = Trip.query.filter_by(id=reservation.trip_id).first()
    trip.available_seats += reservation.ticket_numbers

    db.session.delete(reservation)
    db.session.commit()
    return redirect(url_for("reservations.list"))


def calculate_discount(trip, card, num_of_tickets, has_child):
    total_discount = 0
    result_sum = 0
    has_old_aged_card = False

    # Time-based discounts
    if (
        trip.departure_datetime.time() >= datetime.time(9, 30, 0)
        and trip.arrival_datetime.time() <= datetime.time(16, 0, 0)
    ) or trip.departure_datetime.time() >= datetime.time(19, 30, 0):
        total_discount += 0.05

    # Card-based discounts
    if card:
        if card.card_type == SUPPORTED_CARD_TYPES[0]:
            # card for old aged people
            # discount only on the ticket of the user (who is old)
            has_old_aged_card = True
        elif card.card_type == SUPPORTED_CARD_TYPES[1]:
            # family card -> discount on all tickets
            discount = 0.5 if has_child else 0.1
            total_discount += discount

    if has_old_aged_card:
        result_sum = (trip.base_ticket_price - (trip.base_ticket_price * 0.34)) + (
            (num_of_tickets - 1)
            * (trip.base_ticket_price - (trip.base_ticket_price * total_discount))
        )
    else:
        result_sum = (
            trip.base_ticket_price - (trip.base_ticket_price * total_discount)
        ) * num_of_tickets

    return result_sum


def validate_available_tickets(num_of_tickets, available_seats):
    if num_of_tickets > available_seats:
        raise ValueError(
            f"Not enough available seats on the train - only {available_seats} available."
        )
