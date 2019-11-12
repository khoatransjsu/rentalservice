from datetime import datetime
from app import db
from app import login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128), index=True, nullable=False, unique=True)
    studentid = db.Column(db.Integer, index=True, nullable=False, unique=True)
    firstname = db.Column(db.String(128))
    lastname = db.Column(db.String(128))
    password_hash = db.Column(db.String(128))
    orders = db.relationship('Orders', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User {}>'.format(self.email)    

class Orders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_no = db.Column(db.String(64))
    item_id = db.Column(db.Text)
    cost = db.Column(db.Numeric(10,2))
    comment = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Orders {}>'.format(self.invoice_no)

class Items(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    description = db.Column(db.Text)
    duration = db.Column(db.Integer)
    inventory = db.Column(db.Integer)
    price = db.Column(db.Numeric(10,2))
    imgUrl = db.Column(db.Text)

    def __repr__(self):
        return '<Items {}>'.format(self.name)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))