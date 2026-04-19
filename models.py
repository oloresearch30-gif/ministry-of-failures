from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class AdminUser(UserMixin, db.Model):
    __tablename__ = 'admin_users'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role          = db.Column(db.String(20), default='editor')  # 'superadmin' or 'editor'
    active        = db.Column(db.Boolean, default=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_active(self):
        return self.active


class IndexCard(db.Model):
    __tablename__ = 'index_cards'
    id          = db.Column(db.Integer, primary_key=True)
    number      = db.Column(db.String(4), nullable=False)        # "01", "02"
    title_si    = db.Column(db.String(300), nullable=False)      # Sinhala title
    title_en    = db.Column(db.String(300), nullable=False)      # English title
    body        = db.Column(db.Text, nullable=False)             # HTML body content
    tags        = db.Column(db.String(500), default='')          # comma separated
    tag_type    = db.Column(db.String(20), default='')           # red, yellow, etc
    active      = db.Column(db.Boolean, default=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __str__(self):
        return f"{self.number} — {self.title_en}"