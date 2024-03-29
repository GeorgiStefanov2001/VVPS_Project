from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from . import DATETIME_FORMAT, SUPPORTED_TRIP_FILTER_TYPES, db
from .models.trip import Trip

DATETIME_FORMAT = "%Y-%m-%dT%H:%M"

trips = Blueprint("trips", __name__)


@trips.route("/trips/")
@login_required
def list():
    trips = Trip.query.all()

    if not current_user.is_admin:
        trips = [trip for trip in trips if trip.departure_datetime >= datetime.now()]
    return render_template("/trips/trips.html", trips=trips)


@trips.route("/trips/filter", methods=["POST"])
@login_required
def filter():
    trips = Trip.query.all()
    try:
        trips = filter_trips(
            trips, request.form.get("filter_type"), request.form.get("filter_data")
        )
    except ValueError as e:
        flash(str(e), category="error")

    if not current_user.is_admin:
        trips = [trip for trip in trips if trip.departure_datetime >= datetime.now()]
    return render_template("/trips/trips.html", trips=trips)


def filter_trips(trips, filter_type, filter_data):
    if filter_type not in SUPPORTED_TRIP_FILTER_TYPES:
        raise ValueError("Filter type not supported!")
    if not filter_data and (
        filter_type == SUPPORTED_TRIP_FILTER_TYPES[0]
        or filter_type == SUPPORTED_TRIP_FILTER_TYPES[1]
    ):
        raise ValueError("Enter filter data")

    filtered_trips = []
    if filter_type == SUPPORTED_TRIP_FILTER_TYPES[0]:
        filtered_trips = [trip for trip in trips if trip.departure_city == filter_data]
    elif filter_type == SUPPORTED_TRIP_FILTER_TYPES[1]:
        filtered_trips = [trip for trip in trips if trip.arrival_city == filter_data]
    else:
        two_way_trip = (
            filter_type == False
            if filter_type == SUPPORTED_TRIP_FILTER_TYPES[2]
            else True
        )
        filtered_trips = [trip for trip in trips if trip.two_way_trip == two_way_trip]

    return filtered_trips


@trips.route("/trips/create")
@login_required
def create():
    if not current_user.is_admin:
        raise PermissionError("Cannot create trips as user is not admin")
    return render_template("/trips/create.html")


@trips.route("/trips/create", methods=["POST"])
@login_required
def create_post():
    if not current_user.is_admin:
        raise PermissionError("Cannot create trips as user is not admin")

    try:
        validate_trip_input(request.form)

        # create a new trip with the form data.
        new_trip = Trip(
            departure_city=request.form.get("departure_city"),
            arrival_city=request.form.get("arrival_city"),
            departure_datetime=datetime.strptime(
                request.form.get("departure_datetime"), DATETIME_FORMAT
            ),
            arrival_datetime=datetime.strptime(
                request.form.get("arrival_datetime"), DATETIME_FORMAT
            ),
            two_way_trip=True if request.form.get("two_way_trip") else False,
            available_seats=(
                int(request.form.get("available_seats"))
                if request.form.get("available_seats")
                else -1
            ),
            base_ticket_price=(
                float(request.form.get("base_ticket_price"))
                if request.form.get("base_ticket_price")
                else -1
            ),
        )

        # add the new trip to the database
        db.session.add(new_trip)
        db.session.commit()
    except ValueError as e:
        flash(str(e), category="error")
        return redirect(url_for("trips.create"))

    return redirect(url_for("trips.list"))


@trips.route("/trips/<int:id>")
@login_required
def edit(id):
    if not current_user.is_admin:
        raise PermissionError("Cannot edit trip as user is not admin")

    trip = Trip.query.filter_by(id=id).first()
    if not trip:
        flash(f"Trip with id {id} doesn't exist!", category="error")
        return redirect(url_for("trips.list"))

    return render_template("/trips/edit.html", trip=trip)


@trips.route("/trips/<int:id>", methods=["POST"])
@login_required
def edit_post(id):
    if not current_user.is_admin:
        raise PermissionError("Cannot edit trip as user is not admin")

    trip = Trip.query.filter_by(id=id).first()
    if not trip:
        flash(f"Trip with id {id} doesn't exist!", category="error")
        return redirect(url_for("trips.list"))

    try:
        validate_trip_input(request.form)
        # update trip

        trip.departure_city = str(request.form.get("departure_city"))
        trip.arrival_city = str(request.form.get("arrival_city"))
        trip.departure_datetime = datetime.strptime(
            request.form.get("departure_datetime"), DATETIME_FORMAT
        )
        trip.arrival_datetime = datetime.strptime(
            request.form.get("arrival_datetime"), DATETIME_FORMAT
        )
        trip.two_way_trip = True if request.form.get("two_way_trip") else False
        trip.available_seats = (
            int(request.form.get("available_seats"))
            if request.form.get("available_seats")
            else -1
        )
        trip.base_ticket_price = (
            float(request.form.get("base_ticket_price"))
            if request.form.get("base_ticket_price")
            else -1
        )

        # update the trip in the database
        db.session.commit()
    except ValueError as e:
        flash(str(e), category="error")
        return redirect(url_for("trips.edit", id=trip.id))

    flash("Trip successfully updated", category="info")
    return redirect(url_for("trips.edit", id=trip.id))


@trips.route("/trips/delete/<int:id>", methods=["POST"])
@login_required
def delete_post(id):
    if not current_user.is_admin:
        raise PermissionError("Cannot delete trip as user is not admin")

    trip = Trip.query.filter_by(id=id).first()
    if not trip:
        flash(f"Trip with id {id} doesn't exist!", category="error")
        return redirect(url_for("trips.list"))

    # remove the trip from the database
    db.session.delete(trip)
    db.session.commit()

    flash("Trip successfully removed", category="info")
    return redirect(url_for("trips.list"))


def validate_trip_input(inputs):
    departure_city = inputs.get("departure_city")
    arrival_city = inputs.get("arrival_city")
    departure_datetime = datetime.strptime(
        inputs.get("departure_datetime", ""), DATETIME_FORMAT
    )
    arrival_datetime = datetime.strptime(
        inputs.get("arrival_datetime", ""), DATETIME_FORMAT
    )

    # sanity checks
    if arrival_datetime <= departure_datetime:
        raise ValueError("Arrival time cannot be before departure time.")
    if departure_city.lower() == arrival_city.lower():
        raise ValueError("Trip departure and arrival cities cannot be the same.")
