"""WSGI entrypoint untuk deployment di PythonAnywhere."""

from app import app

# Variabel `application` yang biasanya dicari PythonAnywhere
application = app

