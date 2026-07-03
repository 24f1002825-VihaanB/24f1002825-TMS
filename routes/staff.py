from flask import Blueprint, render_template
from routes.auth import role_required

staff = Blueprint('staff', __name__, url_prefix='/staff')


@staff.route('/dashboard')
@role_required('staff')
def dashboard():
    return render_template('staff/dashboard.html')
