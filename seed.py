from datetime import date
from werkzeug.security import generate_password_hash
from extensions import db
from models import User, StaffProfile, Trek


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


def seed_demo_data():
    """Create demo treks, a sample staff member, and a sample trekker.

    Only runs if no treks exist in the database — safe to call repeatedly.
    This gives the app a polished look during viva demonstration.
    """
    if Trek.query.first() is not None:
        print('[OK] Demo data already exists, skipping')
        return

    # --- Create a demo staff member (approved) ---
    staff_user = User.query.filter_by(email='staff@trekking.com').first()
    if staff_user is None:
        staff_user = User(
            name='Rajesh Kumar',
            email='staff@trekking.com',
            password_hash=generate_password_hash('staff123'),
            role='staff',
            is_active=True
        )
        db.session.add(staff_user)
        db.session.commit()

        staff_profile = StaffProfile(
            user_id=staff_user.id,
            approval_status='approved',
            phone='9876543210',
            bio='Experienced trek guide with 5 years of Himalayan trekking.'
        )
        db.session.add(staff_profile)
        db.session.commit()
        print('[OK] Demo staff created (staff@trekking.com / staff123)')

    # --- Create a demo trekker ---
    trekker = User.query.filter_by(email='trekker@trekking.com').first()
    if trekker is None:
        trekker = User(
            name='Amit Sharma',
            email='trekker@trekking.com',
            password_hash=generate_password_hash('trekker123'),
            role='trekker',
            is_active=True
        )
        db.session.add(trekker)
        db.session.commit()
        print('[OK] Demo trekker created (trekker@trekking.com / trekker123)')

    # --- Create sample treks ---
    sample_treks = [
        Trek(
            name='Kedarkantha Trek',
            location='Uttarakhand',
            difficulty='moderate',
            duration=6,
            available_slots=20,
            description='A stunning winter trek to Kedarkantha peak at 12,500 ft. '
                        'Perfect for beginners looking for a moderate challenge with '
                        'panoramic views of Himalayan peaks.',
            status='open',
            start_date=date(2026, 8, 15),
            end_date=date(2026, 8, 20),
            assigned_staff=staff_user.id
        ),
        Trek(
            name='Valley of Flowers',
            location='Uttarakhand',
            difficulty='easy',
            duration=5,
            available_slots=25,
            description='Walk through a UNESCO World Heritage Site filled with '
                        'alpine flowers and breathtaking meadows at 12,000 ft.',
            status='open',
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 5),
            assigned_staff=staff_user.id
        ),
        Trek(
            name='Hampta Pass',
            location='Himachal Pradesh',
            difficulty='moderate',
            duration=5,
            available_slots=15,
            description='A dramatic crossover trek from Kullu valley to the barren '
                        'landscapes of Spiti. Altitude: 14,000 ft.',
            status='open',
            start_date=date(2026, 9, 10),
            end_date=date(2026, 9, 14),
            assigned_staff=None
        ),
        Trek(
            name='Roopkund Trek',
            location='Uttarakhand',
            difficulty='hard',
            duration=8,
            available_slots=12,
            description='The famous "Skeleton Lake" trek at 15,700 ft. A challenging '
                        'route through dense forests, alpine meadows, and glacial terrain.',
            status='open',
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 8),
            assigned_staff=None
        ),
        Trek(
            name='Triund Trek',
            location='Himachal Pradesh',
            difficulty='easy',
            duration=2,
            available_slots=30,
            description='A short weekend trek near Dharamshala with stunning views of '
                        'the Dhauladhar range. Ideal for first-time trekkers.',
            status='open',
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 2),
            assigned_staff=staff_user.id
        ),
    ]

    for trek in sample_treks:
        db.session.add(trek)

    db.session.commit()
    print(f'[OK] {len(sample_treks)} demo treks created')
