from database import db
from flask_bcrypt import Bcrypt
from datetime import datetime
bcrypt = Bcrypt()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # Duration in minutes
    calories_burned = db.Column(db.Integer, nullable=True)  # Calories burned
    workout_type = db.Column(db.String(50), nullable=True)  # e.g., Cardio, Strength, Yoga
    intensity = db.Column(db.String(20), nullable=True)  # e.g., Low, Medium, High
    notes = db.Column(db.Text, nullable=True)  # Additional workout notes
    user = db.relationship('User', backref='workouts')

    def __repr__(self):
        return f'<Workout {self.title} - {self.date}>'
    
    
class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  
    goal_type = db.Column(db.String(50), nullable=False)  # e.g., 'Calories', 'Duration', 'Frequency'
    target_value = db.Column(db.Integer, nullable=False)  # e.g., 5000 calories, 10 workouts
    current_value = db.Column(db.Integer, default=0)  # Tracks progress toward the goal
    start_date = db.Column(db.Date, default=datetime.utcnow)  
    end_date = db.Column(db.Date, nullable=False)  # Goal deadline
    status = db.Column(db.String(20), default="In Progress")  # In Progress, Completed, Failed

    user = db.relationship('User', backref='goals')

    def __repr__(self):
        return f'<Goal {self.goal_type} - {self.target_value}>'

    def update_progress(self, value):
        self.current_value += value
        if self.current_value >= self.target_value:
            self.status = "Completed"

