from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from . import db
from .models.train_card import TrainCard

cards = Blueprint("cards", __name__)


@cards.route("/cards/")
@login_required
def manage():
    card = TrainCard.query.filter_by(user_id=current_user.id).first()
    return render_template("users/cards.html", card=card, user_age=current_user.age)


@cards.route("/cards/register", methods=["POST"])
@login_required
def register():
    card_type = request.form.get("card_type")
    try:
        card = TrainCard.query.filter_by(user_id=current_user.id).first()
        if card:
            card.card_type = card_type
        else:
            card = TrainCard(card_type=card_type, user_id=current_user.id)
            db.session.add(card)
        db.session.commit()
    except ValueError as e:
        flash(str(e), category="error")
        return redirect(url_for("cards.manage"))

    return render_template("users/cards.html", card=card, user_age=current_user.age)


@cards.route("/cards/remove", methods=["POST"])
@login_required
def remove():
    card = TrainCard.query.filter_by(user_id=current_user.id).first()
    db.session.delete(card)
    db.session.commit()

    return redirect(url_for("cards.manage", card=card, user_age=current_user.age))
