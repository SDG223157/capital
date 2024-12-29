from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.user import bp

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.first_name = request.form.get('first_name')
        current_user.last_name = request.form.get('last_name')
        current_user.timezone = request.form.get('timezone')
        current_user.preferred_currency = request.form.get('preferred_currency')
        current_user.email_notifications = request.form.get('email_notifications') == 'on'
        
        db.session.commit()
        flash('Profile updated successfully', 'success')
        
    return render_template('user/profile.html')

@bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    
    if not current_user.check_password(current_password):
        flash('Current password is incorrect', 'error')
    else:
        current_user.set_password(new_password)
        db.session.commit()
        flash('Password updated successfully', 'success')
        
    return redirect(url_for('user.profile'))