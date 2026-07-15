from datetime import datetime
from extensions import db


# USER MODEL
# Stores ALL users — admins, staff, and trekkers — in one table.
# The 'role' column distinguishes them. This is simpler than having
# 3 separate tables because login works the same way for everyone.

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'staff', 'trekker'
    is_active = db.Column(db.Boolean, default=True)
    is_blacklisted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    # A staff user has one StaffProfile (1-to-1)
    staff_profile = db.relationship('StaffProfile', backref='user', uselist=False)
    # A user can have many bookings (1-to-many)
    bookings = db.relationship('Booking', backref='user', lazy=True)
    # A staff user can be assigned many treks (1-to-many)
    assigned_treks = db.relationship('Trek', backref='staff', lazy=True)

    def __repr__(self):
        return f'<User {self.name} ({self.role})>'


# STAFF PROFILE MODEL
# Extra information for staff members. Linked to User via user_id.
# approval_status tracks whether the admin has approved this staff member.

class StaffProfile(db.Model):
    __tablename__ = 'staff_profile'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    phone = db.Column(db.String(15), default='')
    bio = db.Column(db.Text, default='')
    approval_status = db.Column(db.String(20), default='pending') 
    def __repr__(self):
        return f'<StaffProfile user_id={self.user_id} status={self.approval_status}>'


# TREK MODEL
# Represents a trekking event. Each trek can be assigned to one staff member
# and can have many bookings from users.

class Trek(db.Model):
    __tablename__ = 'trek'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)  # 'easy', 'moderate', 'hard'
    duration = db.Column(db.Integer, nullable=False)  # Duration in days
    available_slots = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, default='')
    status = db.Column(db.String(20), default='open')  # 'open', 'closed', 'completed'
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)

    # Foreign key — which staff member is assigned to lead this trek
    assigned_staff = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    # Relationships
    # A trek can have many bookings (1-to-many)
    bookings = db.relationship('Booking', backref='trek', lazy=True)

    def __repr__(self):
        return f'<Trek {self.name} ({self.status})>'


# BOOKING MODEL
# Links a user (trekker) to a trek they have booked.
# Each booking tracks the trekker booking status.

class Booking(db.Model):
    __tablename__ = 'booking'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey('trek.id'), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    booking_status = db.Column(db.String(20), default='booked')  # 'booked', 'cancelled', 'completed'

    def __repr__(self):
        return f'<Booking user={self.user_id} trek={self.trek_id} ({self.booking_status})>'

