"""Profile routes - View and edit profile"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@profile_bp.route('/edit', methods=['POST'])
@login_required
def edit_profile():
    data = request.form
    
    if 'username' in data and data['username']:
        current_user.username = data['username']
    if 'bio' in data:
        current_user.bio = data['bio']
    if 'location' in data:
        current_user.location = data['location']
    
    db.session.commit()
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('profile.profile'))

@profile_bp.route('/api/stats')
@login_required
def get_stats():
    """Get user stats for profile page"""
    tasks_completed = len([t for t in current_user.tasks if t.done])
    tasks_total = len(current_user.tasks)
    completion_rate = round((tasks_completed / tasks_total * 100) if tasks_total > 0 else 0)
    
    # Calculate this week's progress
    from datetime import datetime, timedelta
    week_ago = datetime.now() - timedelta(days=7)
    this_week_tasks = [t for t in current_user.tasks if t.done and datetime.strptime(t.due_date, '%Y-%m-%d') > week_ago]
    
    return jsonify({
        'tasks_completed': tasks_completed,
        'tasks_total': tasks_total,
        'completion_rate': completion_rate,
        'this_week': len(this_week_tasks),
        'level': current_user.level,
        'xp': current_user.xp,
        'xp_next': current_user.level * 100,
        'coins': current_user.coins
    })