from flask import Blueprint, render_template
from routes.auth import role_required

user = Blueprint('user', __name__, url_prefix='/user')


@user.route('/dashboard')
@role_required('trekker')
def dashboard():
    return render_template('user/dashboard.html')
