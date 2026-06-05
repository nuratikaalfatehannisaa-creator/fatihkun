from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), nullable=False, default='user') # 'admin' atau 'user'
    nama_lengkap = db.Column(db.String(100), nullable=False)
    nim = db.Column(db.String(20), unique=True, nullable=True) # Khusus Mahasiswa




class Absensi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tanggal = db.Column(db.Date, default=datetime.utcnow().date, nullable=False)
    waktu = db.Column(db.Time, default=datetime.utcnow().time, nullable=False)
    status = db.Column(db.String(20), nullable=False) # Hadir, Izin, Sakit, Alpa
    keterangan = db.Column(db.String(255), nullable=True)

    # Relasi ke tabel User
    mahasiswa = db.relationship('User', backref=db.backref('daftar_absen', lazy=True))