from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.String(100), nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(200))

class Meeting(db.Model):
    __tablename__ = 'meetings'
    id = db.Column(db.Integer, primary_key=True)
    meeting_name = db.Column(db.String(100), nullable=False)
    meeting_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(200))
