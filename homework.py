from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///appdata.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models from first app
class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    homework = db.Column(db.String(200), nullable=False)
    hwClass = db.Column(db.String(100), nullable=False)
    professor = db.Column(db.String(100), nullable=False)
    dueDate = db.Column(db.Date, nullable=False)
    difficulty = db.Column(db.String(10), nullable=False)
    completed = db.Column(db.Boolean, default=False)

class TimeSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.String(50))
    monday = db.Column(db.String(100), default="")
    tuesday = db.Column(db.String(100), default="")
    wednesday = db.Column(db.String(100), default="")
    thursday = db.Column(db.String(100), default="")
    friday = db.Column(db.String(100), default="")
    saturday = db.Column(db.String(100), default="")
    sunday = db.Column(db.String(100), default="")

# Models from second app
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

@app.before_request
def create_tables():
    db.create_all()

# Routes from first app
@app.route("/")
def home():
    return render_template("home.html")


@app.route('/homework', methods=['GET', 'POST'])
def homework():
    # This will serve assignments and timetable together (from first app)
    assignments = Assignment.query.order_by(Assignment.dueDate).all()
    timetable = TimeSlot.query.order_by(TimeSlot.id).all()
    alert = None
    hard_count = sum(1 for a in assignments if a.difficulty == "Hard" and not a.completed)
    medium_count = sum(1 for a in assignments if a.difficulty == "Medium" and not a.completed)
    if hard_count > 3 or medium_count > 12:
        alert = "You have too many hard or medium assignments! Try to manage your workload."

    return render_template('homework.html', assignments=assignments, timetable=timetable, alert=alert)

@app.route('/add_assignment', methods=['POST'])
def add_assignment():
    homework = request.form['homework']
    hwClass = request.form['hwClass']
    professor = request.form['professor']
    dueDate = datetime.strptime(request.form['dueDate'], '%Y-%m-%d')
    difficulty = request.form['difficulty']
    new_assignment = Assignment(
        homework=homework,
        hwClass=hwClass,
        professor=professor,
        dueDate=dueDate,
        difficulty=difficulty
    )
    db.session.add(new_assignment)
    db.session.commit()
    return redirect(url_for('homework'))

@app.route('/toggle-completion/<int:id>', methods=['POST'])
def toggle_completion(id):
    assignment = Assignment.query.get_or_404(id)
    assignment.completed = not assignment.completed
    db.session.commit()
    return '', 204

@app.route('/delete-assignment/<int:id>', methods=['POST'])
def delete_assignment(id):
    assignment = Assignment.query.get_or_404(id)
    db.session.delete(assignment)
    db.session.commit()
    return jsonify(success=True)

@app.route('/add_timeslot', methods=['POST'])
def add_timeslot():
    slot = TimeSlot(time="")
    db.session.add(slot)
    db.session.commit()
    return redirect(url_for('homework'))

@app.route('/update-timeslot/<int:id>', methods=['POST'])
def update_timeslot(id):
    slot = TimeSlot.query.get_or_404(id)
    data = request.get_json()
    for field, value in data.items():
        if hasattr(slot, field):
            setattr(slot, field, value)
    db.session.commit()
    return '', 204

@app.route('/delete-timeslot/<int:id>', methods=['POST'])
def delete_timeslot(id):
    slot = TimeSlot.query.get_or_404(id)
    db.session.delete(slot)
    db.session.commit()
    return '', 204

# Routes from second app

@app.route('/homework-old', methods=["GET", "POST"])
def homework_old():
    # This is the old "Homework" logic from your second app
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
        return redirect(url_for("homework_old"))

    homeworks = Homework.query.order_by(Homework.timestamp.desc()).all()
    grouped = {}
    for hw in homeworks:
        grouped.setdefault(hw.day, []).append(hw)

    return render_template("homework_old.html", homeworks=grouped)

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

    else:
        player = None

    return render_template("rps.html", result=result, comp_choice=comp_choice,
                           player_choice=player_choice, player_name=player_name,
                           player=player)

@app.route("/random")
def random_games():
    return render_template("random.html")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
