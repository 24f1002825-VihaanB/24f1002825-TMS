from werkzeug.security import generate_password_hash
from extensions import db
from models import User


def seed_admin():
    """Create the admin user if one doesn't already exist.

    This function is IDEMPOTENT — calling it multiple times won't create
    duplicate admins. It checks first, then creates only if needed.
    """
    existing_admin = User.query.filter_by(role='admin').first()

    if existing_admin is None:
        admin = User(
            name='Admin',
            email='admin@trekking.com',
            password_hash=generate_password_hash('admin123'),
            role='admin',
            is_active=True,
            is_blacklisted=False
        )
        db.session.add(admin)
        db.session.commit()
        print('[OK] Admin user created (admin@trekking.com / admin123)')
    else:
        print('[OK] Admin user already exists, skipping seed')
