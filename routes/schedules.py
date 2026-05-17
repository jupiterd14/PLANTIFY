"""Schedule management routes"""
from flask import Blueprint, request, jsonify
from models import db, User, Schedule

schedules_bp = Blueprint('schedules', __name__)

def get_current_user():
    user = User.query.get(1)
    if not user:
        user = User(username="demo_user")
        db.session.add(user)
        db.session.commit()
    return user

@schedules_bp.route('/', methods=['GET'])
def get_schedules():
    """Get all schedules"""
    user = get_current_user()
    schedules = Schedule.query.filter_by(user_id=user.id).all()
    return jsonify([s.to_dict() for s in schedules])

@schedules_bp.route('/', methods=['POST'])
def create_schedule():
    """Create a new schedule"""
    data = request.json
    user = get_current_user()
    
    if not data.get('title') or not data.get('start_time'):
        return jsonify({'error': 'Title and start time required'}), 400
    
    days = data.get('days', ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'])
    days_str = ','.join(days)
    
    schedule = Schedule(
        title=data['title'],
        start_time=data['start_time'],
        end_time=data.get('end_time', ''),
        days=days_str,
        notes=data.get('notes', ''),
        color=data.get('color', 'lavender'),
        user_id=user.id
    )
    
    db.session.add(schedule)
    db.session.commit()
    
    return jsonify({'success': True, 'id': schedule.id})

@schedules_bp.route('/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    """Delete a schedule"""
    schedule = Schedule.query.get(schedule_id)
    if not schedule:
        return jsonify({'error': 'Schedule not found'}), 404
    
    db.session.delete(schedule)
    db.session.commit()
    
    return jsonify({'success': True})