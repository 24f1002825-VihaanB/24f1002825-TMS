from flask import Flask, render_template
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

    # --- Register Blueprints ---
    # Each blueprint handles routes for a specific part of the app.
    # This keeps app.py clean — routes live in their own files.
    from routes.auth import auth
    from routes.admin import admin
    from routes.staff import staff
    from routes.user import user

    app.register_blueprint(auth)
    app.register_blueprint(admin)
    app.register_blueprint(staff)
    app.register_blueprint(user)

    # --- Root route — redirect to login ---
    @app.route('/')
    def index():
        from flask import redirect, url_for, session
        if 'user_id' in session:
            from routes.auth import redirect_to_dashboard
            return redirect_to_dashboard(session['role'])
        return redirect(url_for('auth.login'))

    # --- Custom error handlers ---
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        return render_template('500.html'), 500

    return app


# This block runs only when you execute 'python app.py' directly.
# It does NOT run when another file imports from app.py.
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
