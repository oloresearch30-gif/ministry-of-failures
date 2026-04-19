from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, AdminUser

auth = Blueprint('auth', __name__)
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return AdminUser.query.get(int(user_id))

@auth.route('/admin/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/admin/')
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = AdminUser.query.filter_by(username=username).first()
        if user and user.check_password(password) and user.active:
            login_user(user)
            return redirect('/admin/')
        flash('Invalid username or password', 'error')
    return render_template('admin_login.html')

@auth.route('/admin/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))