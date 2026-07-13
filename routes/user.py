from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from extensions import db
from models import User, Trek, Booking
from routes.auth import role_required

user = Blueprint('user', __name__, url_prefix='/user')


# =============================================================================
# DASHBOARD
# =============================================================================

@user.route('/dashboard')
@role_required('trekker')
def dashboard():
    user_id = session['user_id']

    # Get open treks with available slots (limit to 5 for dashboard)
    available_treks = Trek.query.filter(
        Trek.status == 'open',
        Trek.available_slots > 0
    ).limit(5).all()

    # Get user's recent bookings
    my_bookings = Booking.query.filter_by(user_id=user_id)\
        .order_by(Booking.booking_date.desc()).limit(5).all()

    return render_template('user/dashboard.html',
                           available_treks=available_treks,
                           my_bookings=my_bookings)


# =============================================================================
# BROWSE TREKS — Search and filter open treks
# =============================================================================

@user.route('/treks')
@role_required('trekker')
def browse_treks():
    q = request.args.get('q', '').strip()
    difficulty = request.args.get('difficulty', '').strip()
    location = request.args.get('location', '').strip()

    # Start with only open treks
    query = Trek.query.filter_by(status='open')

    # Apply search filter
    if q:
        query = query.filter(
            Trek.name.ilike(f'%{q}%') | Trek.location.ilike(f'%{q}%')
        )

    # Apply difficulty filter
    if difficulty in ['easy', 'moderate', 'hard']:
        query = query.filter_by(difficulty=difficulty)

    # Apply location filter
    if location:
        query = query.filter_by(location=location)

    treks = query.order_by(Trek.id.desc()).all()

    # Get distinct locations for the filter dropdown
    all_locations = db.session.query(Trek.location).filter_by(status='open')\
        .distinct().order_by(Trek.location).all()
    locations = [loc[0] for loc in all_locations]

    return render_template('user/treks.html', treks=treks, locations=locations)


# =============================================================================
# TREK DETAIL — View full trek info + Book Now
# =============================================================================

@user.route('/trek/<int:trek_id>')
@role_required('trekker')
def trek_detail(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    user_id = session['user_id']

    # Check if user already has an active booking for this trek
    already_booked = Booking.query.filter(
        Booking.user_id == user_id,
        Booking.trek_id == trek_id,
        Booking.booking_status != 'cancelled'
    ).first() is not None

    return render_template('user/trek_detail.html',
                           trek=trek,
                           already_booked=already_booked)


# =============================================================================
# BOOK TREK — Create a new booking
# =============================================================================

@user.route('/trek/<int:trek_id>/book', methods=['POST'])
@role_required('trekker')
def book_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    user_id = session['user_id']

    # --- Business Rule Checks ---

    # 1. Trek must be open
    if trek.status != 'open':
        flash('This trek is not available for booking.', 'danger')
        return redirect(url_for('user.trek_detail', trek_id=trek.id))

    # 2. Trek must have available slots
    if trek.available_slots <= 0:
        flash('Sorry, this trek is fully booked.', 'danger')
        return redirect(url_for('user.trek_detail', trek_id=trek.id))

    # 3. User must not have already booked this trek
    existing_booking = Booking.query.filter(
        Booking.user_id == user_id,
        Booking.trek_id == trek_id,
        Booking.booking_status != 'cancelled'
    ).first()

    if existing_booking:
        flash('You have already booked this trek.', 'warning')
        return redirect(url_for('user.trek_detail', trek_id=trek.id))

    # --- All checks passed, create booking ---
    booking = Booking(
        user_id=user_id,
        trek_id=trek_id,
        booking_status='booked'
    )
    db.session.add(booking)

    # Decrement available slots
    trek.available_slots -= 1

    db.session.commit()

    flash(f'Successfully booked "{trek.name}"!', 'success')
    return redirect(url_for('user.my_bookings'))


# =============================================================================
# MY BOOKINGS — List all user's bookings
# =============================================================================

@user.route('/bookings')
@role_required('trekker')
def my_bookings():
    user_id = session['user_id']
    bookings = Booking.query.filter_by(user_id=user_id)\
        .order_by(Booking.booking_date.desc()).all()

    return render_template('user/bookings.html', bookings=bookings)


# =============================================================================
# BOOKING DETAIL — View a specific booking
# =============================================================================

@user.route('/booking/<int:booking_id>')
@role_required('trekker')
def booking_detail(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    # SECURITY: Users can only view their own bookings
    if booking.user_id != session['user_id']:
        flash('You do not have permission to view this booking.', 'danger')
        return redirect(url_for('user.my_bookings'))

    return render_template('user/booking_detail.html', booking=booking)


# =============================================================================
# CANCEL BOOKING
# =============================================================================

@user.route('/booking/<int:booking_id>/cancel', methods=['POST'])
@role_required('trekker')
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    # Security check
    if booking.user_id != session['user_id']:
        flash('You do not have permission to cancel this booking.', 'danger')
        return redirect(url_for('user.my_bookings'))

    # Can only cancel active bookings
    if booking.booking_status != 'booked':
        flash('This booking cannot be cancelled.', 'warning')
        return redirect(url_for('user.booking_detail', booking_id=booking.id))

    # Cancel the booking and restore the slot
    booking.booking_status = 'cancelled'
    booking.trek.available_slots += 1

    db.session.commit()

    flash('Booking cancelled successfully.', 'info')
    return redirect(url_for('user.my_bookings'))


# =============================================================================
# TREKKING HISTORY — View completed treks
# =============================================================================

@user.route('/history')
@role_required('trekker')
def history():
    user_id = session['user_id']
    completed = Booking.query.filter_by(
        user_id=user_id,
        booking_status='completed'
    ).order_by(Booking.booking_date.desc()).all()

    return render_template('user/history.html', history=completed)


# =============================================================================
# PROFILE — View and edit
# =============================================================================

@user.route('/profile', methods=['GET', 'POST'])
@role_required('trekker')
def profile():
    current_user = User.query.get(session['user_id'])

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if name:
            current_user.name = name
            db.session.commit()
            session['user_name'] = name
            flash('Profile updated successfully!', 'success')
        else:
            flash('Name cannot be empty.', 'danger')

        return redirect(url_for('user.profile'))

    return render_template('user/profile.html', user=current_user)

