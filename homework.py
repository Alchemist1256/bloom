from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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
    time = db.Column(db.String(50), nullable=False)
    monday = db.Column(db.String(100), default="")
    tuesday = db.Column(db.String(100), default="")
    wednesday = db.Column(db.String(100), default="")
    thursday = db.Column(db.String(100), default="")
    friday = db.Column(db.String(100), default="")
    saturday = db.Column(db.String(100), default="")
    sunday = db.Column(db.String(100), default="")

@app.before_request
def create_tables():
    db.create_all()
    if TimeSlot.query.count() == 0:
        default_slots = ['8:00 - 9:00', '9:00 - 10:00', '10:00 - 11:00']
        for time in default_slots:
            db.session.add(TimeSlot(time=time))
        db.session.commit()

@app.route('/')
def index():
    assignments = Assignment.query.order_by(Assignment.dueDate).all()
    timetable = TimeSlot.query.order_by(TimeSlot.id).all()
    hard_count = sum(1 for a in assignments if a.difficulty == "Hard")
    medium_count = sum(1 for a in assignments if a.difficulty == "Medium")
    alert = None
    if hard_count > 3 or medium_count > 12:
        alert = "Warning: You have too many difficult assignments!"
    return render_template("index.html", assignments=assignments, timetable=timetable, alert=alert)

@app.route('/add-assignment', methods=['POST'])
def add_assignment():
    homework = request.form['homework']
    hwClass = request.form['hwClass']
    professor = request.form['professor']
    dueDate = datetime.strptime(request.form['dueDate'], "%Y-%m-%d").date()
    difficulty = request.form['difficulty']
    db.session.add(Assignment(homework=homework, hwClass=hwClass,
                              professor=professor, dueDate=dueDate,
                              difficulty=difficulty, completed=False))
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/toggle-completion/<int:assignment_id>', methods=['POST'])
def toggle_completion(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    assignment.completed = not assignment.completed
    db.session.commit()
    return jsonify(success=True)

@app.route('/delete-assignment/<int:assignment_id>', methods=['POST'])
def delete_assignment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    db.session.delete(assignment)
    db.session.commit()
    return jsonify(success=True)

@app.route('/add-timeslot', methods=['POST'])
def add_timeslot():
    db.session.add(TimeSlot(time=""))
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/update-timeslot/<int:timeslot_id>', methods=['POST'])
def update_timeslot(timeslot_id):
    data = request.json
    slot = TimeSlot.query.get_or_404(timeslot_id)
    for field in ['time', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
        if field in data:
            setattr(slot, field, data[field])
    db.session.commit()
    return jsonify(success=True)

@app.route('/delete-timeslot/<int:timeslot_id>', methods=['POST'])
def delete_timeslot(timeslot_id):
    db.session.delete(TimeSlot.query.get_or_404(timeslot_id))
    db.session.commit()
    return jsonify(success=True)

if __name__ == '__main__':
    app.run(debug=True)
