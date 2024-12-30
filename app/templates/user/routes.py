from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from app import db
from app.models import User

bp = Blueprint('user', __name__)

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Handle profile updates
        username = request.form.get('username')
        email = request.form.get('email')
        
        if username and username != current_user.username:
            # Check if username is already taken
            if User.query.filter_by(username=username).first() is not None:
                flash('Username already taken.', 'error')
                return redirect(url_for('user.profile'))
            current_user.username = username
            
        if email and email != current_user.email:
            # Check if email is already registered
            if User.query.filter_by(email=email).first() is not None:
                flash('Email already registered.', 'error')
                return redirect(url_for('user.profile'))
            current_user.email = email
            
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error updating profile.', 'error')
            
        return redirect(url_for('user.profile'))
        
    return render_template('user/profile.html')