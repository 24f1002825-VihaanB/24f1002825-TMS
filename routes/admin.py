from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import User, StaffProfile, Trek, Booking
from routes.auth import role_required

admin = Blueprint('admin', __name__, url_prefix='/admin')

PER_PAGE = 10  # Treks per page for pagination


# =============================================================================
# DASHBOARD
# =============================================================================

@admin.route('/dashboard')
@role_required('admin')
def dashboard():
    total_treks = Trek.query.count()
    total_users = User.query.filter_by(role='trekker').count()
    total_staff = User.query.filter_by(role='staff').count()
    total_bookings = Booking.query.count()

    # Get the 5 most recent bookings
    recent_bookings = Booking.query.order_by(Booking.booking_date.desc()).limit(5).all()

    return render_template('admin/dashboard.html',
                           total_treks=total_treks,
                           total_users=total_users,
                           total_staff=total_staff,
                           total_bookings=total_bookings,
                           recent_bookings=recent_bookings)


# =============================================================================
# TREK MANAGEMENT — List, Add, Edit, Delete
# =============================================================================

@admin.route('/treks')
@role_required('admin')
def treks():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '').strip()

    # Build query — filter by search term if provided
    query = Trek.query
    if q:
        query = query.filter(
            Trek.name.ilike(f'%{q}%') | Trek.location.ilike(f'%{q}%')
        )

    # Order by most recently created and paginate
    query = query.order_by(Trek.id.desc())
    total = query.count()
    total_pages = (total + PER_PAGE - 1) // PER_PAGE  # Ceiling division
    treks = query.offset((page - 1) * PER_PAGE).limit(PER_PAGE).all()

    return render_template('admin/treks.html',
                           treks=treks,
                           page=page,
                           total_pages=total_pages)


@admin.route('/treks/add', methods=['GET', 'POST'])
@role_required('admin')
def trek_add():
    # Get approved staff for the dropdown
    approved_profiles = StaffProfile.query.filter_by(approval_status='approved').all()
    staff_list = [p.user for p in approved_profiles]

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        location = request.form.get('location', '').strip()
        difficulty = request.form.get('difficulty', '')
        duration = request.form.get('duration', type=int)
        available_slots = request.form.get('available_slots', type=int)
        description = request.form.get('description', '').strip()
        status = request.form.get('status', 'open')
        start_date = request.form.get('start_date', '')
        end_date = request.form.get('end_date', '')
        assigned_staff = request.form.get('assigned_staff', '')

        # Basic validation
        if not all([name, location, difficulty, duration, available_slots]):
            flash('Please fill in all required fields.', 'danger')
            return redirect(url_for('admin.trek_add'))

        trek = Trek(
            name=name,
            location=location,
            difficulty=difficulty,
            duration=duration,
            available_slots=available_slots,
            description=description,
            status=status,
            start_date=datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None,
            end_date=datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None,
            assigned_staff=int(assigned_staff) if assigned_staff else None
        )
        db.session.add(trek)
        db.session.commit()

        flash(f'Trek "{name}" created successfully!', 'success')
        return redirect(url_for('admin.treks'))

    return render_template('admin/trek_form.html', trek=None, staff_list=staff_list)


@admin.route('/treks/<int:trek_id>/edit', methods=['GET', 'POST'])
@role_required('admin')
def trek_edit(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    approved_profiles = StaffProfile.query.filter_by(approval_status='approved').all()
    staff_list = [p.user for p in approved_profiles]

    if request.method == 'POST':
        trek.name = request.form.get('name', '').strip()
        trek.location = request.form.get('location', '').strip()
        trek.difficulty = request.form.get('difficulty', '')
        trek.duration = request.form.get('duration', type=int)
        trek.available_slots = request.form.get('available_slots', type=int)
        trek.description = request.form.get('description', '').strip()
        trek.status = request.form.get('status', 'open')

        start_date = request.form.get('start_date', '')
        end_date = request.form.get('end_date', '')
        assigned_staff = request.form.get('assigned_staff', '')

        trek.start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
        trek.end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        trek.assigned_staff = int(assigned_staff) if assigned_staff else None

        db.session.commit()
        flash(f'Trek "{trek.name}" updated successfully!', 'success')
        return redirect(url_for('admin.treks'))

    return render_template('admin/trek_form.html', trek=trek, staff_list=staff_list)


@admin.route('/treks/<int:trek_id>/delete', methods=['POST'])
@role_required('admin')
def trek_delete(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    # Delete related bookings first (to avoid foreign key errors)
    Booking.query.filter_by(trek_id=trek.id).delete()
    db.session.delete(trek)
    db.session.commit()

    flash(f'Trek "{trek.name}" deleted.', 'info')
    return redirect(url_for('admin.treks'))


# =============================================================================
# STAFF MANAGEMENT — Approve, Reject
# =============================================================================

@admin.route('/staff')
@role_required('admin')
def staff_page():
    tab = request.args.get('tab', 'pending')

    pending = StaffProfile.query.filter_by(approval_status='pending').all()
    approved = StaffProfile.query.filter_by(approval_status='approved').all()
    rejected = StaffProfile.query.filter_by(approval_status='rejected').all()

    # Choose which list to display based on the active tab
    if tab == 'approved':
        current_list = approved
    elif tab == 'rejected':
        current_list = rejected
    else:
        current_list = pending
        tab = 'pending'

    return render_template('admin/staff.html',
                           tab=tab,
                           pending=pending,
                           approved=approved,
                           rejected=rejected,
                           current_list=current_list)


@admin.route('/staff/<int:profile_id>/approve', methods=['POST'])
@role_required('admin')
def staff_approve(profile_id):
    profile = StaffProfile.query.get_or_404(profile_id)
    profile.approval_status = 'approved'
    db.session.commit()
    flash(f'Staff "{profile.user.name}" approved!', 'success')
    return redirect(url_for('admin.staff_page', tab='pending'))


@admin.route('/staff/<int:profile_id>/reject', methods=['POST'])
@role_required('admin')
def staff_reject(profile_id):
    profile = StaffProfile.query.get_or_404(profile_id)
    profile.approval_status = 'rejected'
    db.session.commit()
    flash(f'Staff "{profile.user.name}" rejected.', 'info')
    return redirect(url_for('admin.staff_page', tab='pending'))


# =============================================================================
# USER MANAGEMENT — Blacklist / Unblacklist
# =============================================================================

@admin.route('/users')
@role_required('admin')
def users():
    q = request.args.get('q', '').strip()

    query = User.query
    if q:
        query = query.filter(
            User.name.ilike(f'%{q}%') | User.email.ilike(f'%{q}%')
        )

    users = query.order_by(User.id).all()
    return render_template('admin/users.html', users=users)


@admin.route('/users/<int:user_id>/blacklist', methods=['POST'])
@role_required('admin')
def user_blacklist(user_id):
    user = User.query.get_or_404(user_id)

    # Prevent blacklisting the admin
    if user.role == 'admin':
        flash('Cannot blacklist the admin account.', 'danger')
        return redirect(url_for('admin.users'))

    # Toggle blacklist status
    user.is_blacklisted = not user.is_blacklisted
    db.session.commit()

    action = 'blacklisted' if user.is_blacklisted else 'unblacklisted'
    flash(f'User "{user.name}" has been {action}.', 'info')
    return redirect(url_for('admin.users'))


# =============================================================================
# BOOKINGS — View all bookings
# =============================================================================

@admin.route('/bookings')
@role_required('admin')
def bookings():
    all_bookings = Booking.query.order_by(Booking.booking_date.desc()).all()
    return render_template('admin/bookings.html', bookings=all_bookings)


# =============================================================================
# SEARCH — Unified search across treks and users
# =============================================================================

@admin.route('/search')
@role_required('admin')
def search():
    query = request.args.get('q', '').strip()
    trek_results = []
    user_results = []

    if query:
        # Search treks by name or location
        trek_results = Trek.query.filter(
            Trek.name.ilike(f'%{query}%') | Trek.location.ilike(f'%{query}%')
        ).all()

        # Search users by name or email
        user_results = User.query.filter(
            User.name.ilike(f'%{query}%') | User.email.ilike(f'%{query}%')
        ).all()

    return render_template('admin/search.html',
                           query=query,
                           trek_results=trek_results,
                           user_results=user_results)
