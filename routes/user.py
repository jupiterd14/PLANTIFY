"""User management routes"""
from flask import Blueprint, jsonify, request
from models import db, User
from datetime import datetime, timedelta

user_bp = Blueprint('user', __name__)

def get_current_user():
    user = User.query.get(1)
    if not user:
        user = User(username="demo_user")
        db.session.add(user)
        db.session.commit()
    return user

@user_bp.route('/', methods=['GET'])
def get_user():
    """Get current user info"""
    user = get_current_user()
    return jsonify(user.to_dict())

@user_bp.route('/coins', methods=['POST'])
def update_coins():
    """Add or subtract coins"""
    data = request.json
    user = get_current_user()
    
    amount = data.get('amount', 0)
    user.coins += amount
    
    if user.coins < 0:
        user.coins = 0
        return jsonify({'error': 'Not enough coins'}), 400
    
    db.session.commit()
    return jsonify({'success': True, 'coins': user.coins})

@user_bp.route('/dashboard', methods=['GET'])
def get_dashboard():
    """Get dashboard statistics"""
    user = get_current_user()
    
    tasks = user.tasks
    pending = len([t for t in tasks if not t.done])
    
    today = datetime.now()
    today_name = today.strftime('%a')
    day_map = {'Mon': 'Mon', 'Tue': 'Tue', 'Wed': 'Wed', 'Thu': 'Thu', 
               'Fri': 'Fri', 'Sat': 'Sat', 'Sun': 'Sun'}
    today_weekday = day_map.get(today_name, 'Mon')
    
    today_schedules = [s for s in user.schedules if today_weekday in s.get_days_list()]
    
    urgent = len([t for t in tasks if not t.done and t.due_date == today.strftime('%Y-%m-%d')])
    
    return jsonify({
        'pending_tasks': pending,
        'schedule_count': len(user.schedules),
        'urgent_count': urgent,
        'today_schedules': [s.to_dict() for s in today_schedules]
    })