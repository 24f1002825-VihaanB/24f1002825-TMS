from flask_sqlalchemy import SQLAlchemy

# Create the SQLAlchemy instance here, separate from app.py.
#
# WHY a separate file?
# If we put db = SQLAlchemy() inside app.py, then models.py would need to
# import from app.py, and app.py imports from models.py — that's a circular
# import. By putting 'db' in its own file, both app.py and models.py can
# import from here without any circular dependency.

db = SQLAlchemy()
