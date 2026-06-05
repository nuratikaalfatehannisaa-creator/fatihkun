"""Entrypoint aplikasi Flask.

File ini dibuat agar pengguna bisa menjalankan aplikasi dengan:

    python run.py

Sekaligus memastikan database awal dibuat (inisialisasi_db dari app.py).
"""

import os

from app import app, inisialisasi_db


if __name__ == "__main__":
    inisialisasi_db()

    # izinkan pengaturan debug lewat environment variable (opsional)
    debug_env = os.getenv("FLASK_DEBUG")
    debug = True if debug_env is None else debug_env.lower() in {"1", "true", "yes", "on"}


    # 0.0.0.0 agar bisa diakses dari jaringan (selama firewall mengizinkan)
    app.run(host="0.0.0.0", debug=True)

