from flask import Blueprint, render_template
from routes.auth import role_required

admin = Blueprint('admin', __name__, url_prefix='/admin')


@admin.route('/dashboard')
@role_required('admin')
def dashboard():
    return render_template('admin/dashboard.html')
