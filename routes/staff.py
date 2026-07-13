from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from extensions import db
from models import User, StaffProfile, Trek, Booking
from routes.auth import role_required

staff = Blueprint('staff', __name__, url_prefix='/staff')


# =============================================================================
# DASHBOARD
# =============================================================================

@staff.route('/dashboard')
@role_required('staff')
def dashboard():
    user_id = session['user_id']

    # Get only treks assigned to this staff member
    assigned_treks = Trek.query.filter_by(assigned_staff=user_id).all()

    # Count total participants across all assigned treks (exclude cancelled)
    total_participants = 0
    for trek in assigned_treks:
        total_participants += Booking.query.filter(
            Booking.trek_id == trek.id,
            Booking.booking_status != 'cancelled'
        ).count()

    # Count open treks
    open_treks = sum(1 for t in assigned_treks if t.status == 'open')

    return render_template('staff/dashboard.html',
                           assigned_treks=assigned_treks,
                           total_participants=total_participants,
                           open_treks=open_treks)


# =============================================================================
# MY TREKS — List all assigned treks
# =============================================================================

@staff.route('/my-treks')
@role_required('staff')
def my_treks():
    user_id = session['user_id']
    assigned_treks = Trek.query.filter_by(assigned_staff=user_id).all()

    # Build participant count for each trek
    trek_data = []
    for trek in assigned_treks:
        participant_count = Booking.query.filter(
            Booking.trek_id == trek.id,
            Booking.booking_status != 'cancelled'
        ).count()
        trek_data.append({'trek': trek, 'participants': participant_count})

    return render_template('staff/my_treks.html', trek_data=trek_data)

# =============================================================================
# TREK DETAIL — View trek info + participant list
# =============================================================================

@staff.route('/trek/<int:trek_id>')
@role_required('staff')
def trek_detail(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    # SECURITY: Only the assigned staff can view this trek
    if trek.assigned_staff != session['user_id']:
        flash('You are not assigned to this trek.', 'danger')
        return redirect(url_for('staff.dashboard'))

    # Get all bookings for this trek (participants)
    participants = Booking.query.filter_by(trek_id=trek.id).all()

    return render_template('staff/trek_detail.html',
                           trek=trek,
                           participants=participants)


# =============================================================================
# UPDATE AVAILABLE SLOTS
# =============================================================================

@staff.route('/trek/<int:trek_id>/update-slots', methods=['POST'])
@role_required('staff')
def update_slots(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    if trek.assigned_staff != session['user_id']:
        flash('You are not assigned to this trek.', 'danger')
        return redirect(url_for('staff.dashboard'))

    new_slots = request.form.get('available_slots', type=int)
    if new_slots is not None and new_slots >= 0:
        trek.available_slots = new_slots
        db.session.commit()
        flash(f'Available slots updated to {new_slots}.', 'success')
    else:
        flash('Invalid slot count.', 'danger')

    return redirect(url_for('staff.trek_detail', trek_id=trek.id))


# =============================================================================
# UPDATE TREK STATUS (Open / Closed)
# =============================================================================

@staff.route('/trek/<int:trek_id>/update-status', methods=['POST'])
@role_required('staff')
def update_status(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    if trek.assigned_staff != session['user_id']:
        flash('You are not assigned to this trek.', 'danger')
        return redirect(url_for('staff.dashboard'))

    new_status = request.form.get('status', '')
    if new_status in ['open', 'closed']:
        trek.status = new_status
        db.session.commit()
        flash(f'Trek status changed to {new_status.title()}.', 'success')
    else:
        flash('Invalid status.', 'danger')

    return redirect(url_for('staff.trek_detail', trek_id=trek.id))


# =============================================================================
# MARK TREK AS STARTED
# =============================================================================

@staff.route('/trek/<int:trek_id>/mark-started', methods=['POST'])
@role_required('staff')
def mark_started(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    if trek.assigned_staff != session['user_id']:
        flash('You are not assigned to this trek.', 'danger')
        return redirect(url_for('staff.dashboard'))

    if trek.status == 'completed':
        flash('This trek is already completed.', 'warning')
        return redirect(url_for('staff.trek_detail', trek_id=trek.id))

    # Close the trek (no more bookings) when it starts
    trek.status = 'closed'
    db.session.commit()
    flash('Trek marked as started! Status set to Closed (no more bookings).', 'success')

    return redirect(url_for('staff.trek_detail', trek_id=trek.id))


# =============================================================================
# MARK TREK AS COMPLETED
# =============================================================================

@staff.route('/trek/<int:trek_id>/mark-completed', methods=['POST'])
@role_required('staff')
def mark_completed(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    if trek.assigned_staff != session['user_id']:
        flash('You are not assigned to this trek.', 'danger')
        return redirect(url_for('staff.dashboard'))

    # Mark trek as completed
    trek.status = 'completed'

    # Update all active bookings to 'completed'
    active_bookings = Booking.query.filter(
        Booking.trek_id == trek.id,
        Booking.booking_status == 'booked'
    ).all()

    for booking in active_bookings:
        booking.booking_status = 'completed'

    db.session.commit()
    flash(f'Trek "{trek.name}" marked as completed! {len(active_bookings)} booking(s) updated.', 'success')

    return redirect(url_for('staff.trek_detail', trek_id=trek.id))


# =============================================================================
# STAFF PROFILE — View and edit
# =============================================================================

@staff.route('/profile', methods=['GET', 'POST'])
@role_required('staff')
def profile():
    user = User.query.get(session['user_id'])
    staff_profile = StaffProfile.query.filter_by(user_id=user.id).first()

    if request.method == 'POST':
        user.name = request.form.get('name', '').strip()
        staff_profile.phone = request.form.get('phone', '').strip()
        staff_profile.bio = request.form.get('bio', '').strip()

        db.session.commit()

        # Update session name in case it changed
        session['user_name'] = user.name

        flash('Profile updated successfully!', 'success')
        return redirect(url_for('staff.profile'))

    return render_template('staff/profile.html', user=user, profile=staff_profile)

