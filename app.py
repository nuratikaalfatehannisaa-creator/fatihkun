from flask import Flask, render_template, redirect, url_for, request, flash, abort

from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Absensi
from datetime import datetime
import secrets


app = Flask(__name__)


app.config['SECRET_KEY'] = 'kunci_rahasia_super_aman_123'
# Gunakan SQLite yang relatif terhadap direktori aplikasi
# (lebih aman untuk deploy platform yang berbeda)
import os
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'absensi.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- ROUTE UTAMA & AUTENTIKASI ---

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        nama_lengkap = request.form.get('nama_lengkap').strip()
        nim = request.form.get('nim').strip()

        # Validasi Input Dasar
        if not username or not password or not nama_lengkap or not nim:
            flash('Semua field wajib diisi!', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first() or User.query.filter_by(nim=nim).first():
            flash('Username atau NIM sudah terdaftar!', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='scrypt')
        new_user = User(
            username=username,
            password=hashed_password,
            role='user',
            nama_lengkap=nama_lengkap,
            nim=nim,
        )
        
        db.session.add(new_user)

        db.session.commit()
        flash('Registrasi berhasil! Silakan login.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('user_dashboard'))
        
        flash('Username atau password salah!', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Anda telah logout.', 'success')
    return redirect(url_for('login'))

# --- DASHBOARD & FITUR USER ---

@app.route('/dashboard/user', methods=['GET', 'POST'])
@login_required
def user_dashboard():
    if current_user.role != 'user':
        return "Akses Ditolak", 403
    
    # Fitur 1: Mengisi Absensi (Check-in)
    if request.method == 'POST':
        status = request.form.get('status')
        keterangan = request.form.get('keterangan', '')
        
        # Cek apakah hari ini sudah absen
        hari_ini = datetime.utcnow().date()
        sudah_absen = Absensi.query.filter_by(user_id=current_user.id, tanggal=hari_ini).first()
        
        if sudah_absen:
            flash('Anda sudah melakukan absensi hari ini!', 'warning')
        else:
            absen_baru = Absensi(user_id=current_user.id, status=status, keterangan=keterangan)
            db.session.add(absen_baru)
            db.session.commit()
            flash('Absensi berhasil disimpan!', 'success')
            
    # Fitur 2: Riwayat Absensi Pribadi
    riwayat = Absensi.query.filter_by(user_id=current_user.id).order_by(Absensi.id.desc()).all()
    return render_template('user_dashboard.html', riwayat=riwayat)

# --- DASHBOARD & FITUR CRUD ADMIN ---

@app.route('/dashboard/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return "Akses Ditolak", 403
    
    # Fitur 3: Rekap Absensi Global (Read data)
    semua_absensi = Absensi.query.order_by(Absensi.id.desc()).all()
    total_mahasiswa = User.query.filter_by(role='user').count()
    return render_template('admin_dashboard.html', semua_absensi=semua_absensi, total_mahasiswa=total_mahasiswa)

@app.route('/admin/mahasiswa', methods=['GET', 'POST'])
@login_required
def kelola_mahasiswa():
    if current_user.role != 'admin':
        return "Akses Ditolak", 403
    
    # Fitur 4: Tambah Data Mahasiswa Baru (Create)
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        nama_lengkap = request.form.get('nama_lengkap')
        nim = request.form.get('nim')

        hashed_password = generate_password_hash(password, method='scrypt')
        user_baru = User(
            username=username,
            password=hashed_password,
            role='user',
            nama_lengkap=nama_lengkap,
            nim=nim,
        )

        db.session.add(user_baru)
        db.session.commit()
        flash('Berhasil menambahkan mahasiswa baru! QR siap dipakai untuk absensi.', 'success')

    daftar_mahasiswa = User.query.filter_by(role='user').all()
    return render_template('kelola_mahasiswa.html', daftar_mahasiswa=daftar_mahasiswa)


# Fitur 5: Update & Delete Data Mahasiswa
@app.route('/admin/mahasiswa/edit/<int:id>', methods=['POST'])
@login_required
def edit_mahasiswa(id):
    if current_user.role != 'admin':
        return "Akses Ditolak", 403
    user = User.query.get_or_404(id)
    user.nama_lengkap = request.form.get('nama_lengkap')
    user.nim = request.form.get('nim')

    db.session.commit()

    flash('Data mahasiswa berhasil diperbarui!', 'success')
    return redirect(url_for('kelola_mahasiswa'))


@app.route('/admin/mahasiswa/hapus/<int:id>')
@login_required
def hapus_mahasiswa(id):
    if current_user.role != 'admin': return "Akses Ditolak", 403
    user = User.query.get_or_404(id)
    # Hapus juga data absensi terkait agar tidak error (Cascade)
    Absensi.query.filter_by(user_id=id).delete()
    db.session.delete(user)
    db.session.commit()
    flash('Data mahasiswa berhasil dihapus!', 'warning')
    return redirect(url_for('kelola_mahasiswa'))




# Membuat database awal & Akun Admin bawaan saat pertama kali dijalankan

def inisialisasi_db():
    with app.app_context():
        db.create_all()
        # Jika admin belum ada, buat otomatis
        if not User.query.filter_by(username='admin').first():
            admin_default = User(
                username='admin',
                password=generate_password_hash('admin123', method='scrypt'),
                role='admin',
                nama_lengkap='Administrator Sistem'
            )
            db.session.add(admin_default)
            db.session.commit()


if __name__ == '__main__':
    inisialisasi_db()
    app.run(debug=True)