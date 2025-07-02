from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///appdata.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
class Homework(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String(20), nullable=False)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    wins = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)
    ties = db.Column(db.Integer, default=0)


@app.route("/")
def home():
    return render_template("home.html")

@app.route("/homework", methods=["GET", "POST"])
def homework():
    week_ago = datetime.utcnow() - timedelta(days=7)
    Homework.query.filter(Homework.timestamp < week_ago).delete()
    db.session.commit()

    if request.method == "POST":
        day = request.form.get("day")
        text = request.form.get("text")
        if day and text:
            hw = Homework(day=day, text=text)
            db.session.add(hw)
            db.session.commit()
        return redirect(url_for("homework"))

    homeworks = Homework.query.order_by(Homework.timestamp.desc()).all()
    grouped = {}
    for hw in homeworks:
        grouped.setdefault(hw.day, []).append(hw)

    return render_template("homework.html", homeworks=grouped)

@app.route("/rps", methods=["GET", "POST"])
def rps():
    result = None
    comp_choice = None
    player_choice = None
    player_name = None

    if request.method == "POST":
        player_name = request.form.get("name", "").strip()
        player_choice = request.form.get("choice")
        valid_choices = ["rock", "paper", "scissors"]

        if not player_name or player_choice not in valid_choices:
            return redirect(url_for("rps"))

        player = Player.query.filter_by(name=player_name).first()
        if not player:
            player = Player(name=player_name)
            db.session.add(player)
            db.session.commit()

        comp_choice = random.choice(valid_choices)

        if player_choice == comp_choice:
            result = "Tie"
            player.ties += 1
        elif (player_choice == "rock" and comp_choice == "scissors") or \
             (player_choice == "scissors" and comp_choice == "paper") or \
             (player_choice == "paper" and comp_choice == "rock"):
            result = "You Win!"
            player.wins += 1
        else:
            result = "You Lose!"
            player.losses += 1

        db.session.commit()

        player = Player.query.filter_by(name=player_name).first()

    else:
        player = None

    return render_template("rps.html", result=result, comp_choice=comp_choice,
                           player_choice=player_choice, player_name=player_name,
                           player=player)
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)