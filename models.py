from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    kyc_status = db.Column(db.String(20), default='pending')
    kyc_verified_at = db.Column(db.DateTime, nullable=True)
    identity_verified = db.Column(db.Boolean, default=False)
    identity_info = db.relationship('IdentityInfo', backref='user', uselist=False)

class KYCVerification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    selfie_path = db.Column(db.String(200))
    liveness_score = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='pending')
    identity_card_front = db.Column(db.String(200))
    identity_card_back = db.Column(db.String(200))

class IdentityInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    id_number = db.Column(db.String(12), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    nationality = db.Column(db.String(50), nullable=False)
    residence_address = db.Column(db.String(200), nullable=False)
    birth_place = db.Column(db.String(100), nullable=False)
    issue_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime, nullable=True)
