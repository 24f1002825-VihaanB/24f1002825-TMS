from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import User, StaffProfile

auth = Blueprint('auth', __name__)


# =============================================================================
# DECORATORS — Reusable access control
# =============================================================================

def login_required(f):
    """Decorator that redirects to login page if user is not logged in.

    Usage: Put @login_required above any route that needs authentication.

    How it works:
    1. Check if 'user_id' exists in the session
    2. If not → redirect to login page with a flash message
    3. If yes → run the original route function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def role_required(role):
    """Decorator that restricts a route to a specific role.

    Usage: @role_required('admin') — only admins can access this route.

    How it works:
    1. First checks if user is logged in (same as login_required)
    2. Then checks if their role matches the required role
    3. If not → show 403 Forbidden page
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            if session.get('role') != role:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# =============================================================================
# LOGIN
# =============================================================================

@auth.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect to their dashboard
    if 'user_id' in session:
        return redirect_to_dashboard(session['role'])

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        # Find user by email
        user = User.query.filter_by(email=email).first()

        # Check if user exists and password is correct
        if user is None or not check_password_hash(user.password_hash, password):
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('auth.login'))

        # Check if user is blacklisted
        if user.is_blacklisted:
            flash('Your account has been suspended. Contact the administrator.', 'danger')
            return redirect(url_for('auth.login'))

        # Check if user is inactive
        if not user.is_active:
            flash('Your account is inactive. Contact the administrator.', 'danger')
            return redirect(url_for('auth.login'))

        # Staff-specific check: must be approved by admin
        if user.role == 'staff':
            profile = StaffProfile.query.filter_by(user_id=user.id).first()
            if profile and profile.approval_status != 'approved':
                flash('Your staff account is awaiting admin approval.', 'warning')
                return redirect(url_for('auth.login'))

        # All checks passed — create session
        session['user_id'] = user.id
        session['user_name'] = user.name
        session['role'] = user.role

        flash(f'Welcome back, {user.name}!', 'success')
        return redirect_to_dashboard(user.role)

    return render_template('auth/login.html')


# =============================================================================
# REGISTER
# =============================================================================

@auth.route('/register', methods=['GET', 'POST'])
def register():
    # If user is already logged in, redirect to their dashboard
    if 'user_id' in session:
        return redirect_to_dashboard(session['role'])

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', '')

        # --- Validation ---
        if not all([name, email, password, confirm_password, role]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('auth.register'))

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.register'))

        if len(password) < 4:
            flash('Password must be at least 4 characters.', 'danger')
            return redirect(url_for('auth.register'))

        # Admin cannot register — they are created by the seed script
        if role not in ['trekker', 'staff']:
            flash('Invalid role selected.', 'danger')
            return redirect(url_for('auth.register'))

        # Check if email is already taken
        if User.query.filter_by(email=email).first():
            flash('An account with this email already exists.', 'danger')
            return redirect(url_for('auth.register'))

        # --- Create the user ---
        new_user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role=role
        )
        db.session.add(new_user)
        db.session.commit()

        # If registering as staff, create a StaffProfile (pending approval)
        if role == 'staff':
            staff_profile = StaffProfile(
                user_id=new_user.id,
                approval_status='pending'
            )
            db.session.add(staff_profile)
            db.session.commit()
            flash('Registration successful! Your staff account is pending admin approval.', 'info')
        else:
            flash('Registration successful! You can now log in.', 'success')

        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


# =============================================================================
# LOGOUT
# =============================================================================

@auth.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


# =============================================================================
# HELPER — Redirect user to their role-specific dashboard
# =============================================================================

def redirect_to_dashboard(role):
    """Send the user to the correct dashboard based on their role."""
    if role == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif role == 'staff':
        return redirect(url_for('staff.dashboard'))
    else:
        return redirect(url_for('user.dashboard'))
