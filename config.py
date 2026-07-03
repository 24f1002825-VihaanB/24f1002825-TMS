import os


class Config:
    """Base configuration for the Flask application."""

    # Secret key for session management and CSRF protection
    # In production, use a proper random key. For development, this is fine.
    SECRET_KEY = os.environ.get('SECRET_KEY', 'trekking-app-secret-key-change-in-production')

    # SQLite database path — stored inside the 'instance' folder
    # Flask automatically creates the 'instance' folder if it doesn't exist
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db'

    # Disable modification tracking (saves memory, we don't need it)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
