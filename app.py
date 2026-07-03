from flask import Flask
from config import Config
from extensions import db
from models import User, StaffProfile, Trek, Booking
from seed import seed_admin


def create_app():
    """Application factory — creates and configures the Flask app.

    Why a function instead of just 'app = Flask(__name__)'?
    It keeps things organized. The function creates the app, loads the
    config, initializes the database, and seeds the admin — all in one
    clean sequence. This is a standard Flask pattern.
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize SQLAlchemy with this app
    db.init_app(app)

    # Create all database tables and seed the admin user
    with app.app_context():
        db.create_all()
        seed_admin()

    # Simple test route — confirms the app is running
    @app.route('/')
    def index():
        return '<h1>Trekking Management Application</h1><p>App is running.</p>'

    return app


# This block runs only when you execute 'python app.py' directly.
# It does NOT run when another file imports from app.py.
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
