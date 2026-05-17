"""Task management routes"""
from flask import Blueprint, request, jsonify
from models import db, User, Task
from datetime import datetime

tasks_bp = Blueprint('tasks', __name__)

def get_current_user():
    """Get demo user (simplified auth for now)"""
    user = User.query.get(1)
    if not user:
        user = User(username="demo_user")
        db.session.add(user)
        db.session.commit()
    return user

@tasks_bp.route('/', methods=['GET'])
def get_tasks():
    """Get all tasks for current user"""
    user = get_current_user()
    tasks = Task.query.filter_by(user_id=user.id).order_by(Task.due_date).all()
    return jsonify([t.to_dict() for t in tasks])

@tasks_bp.route('/', methods=['POST'])
def create_task():
    """Create a new task"""
    data = request.json
    user = get_current_user()
    
    if not data.get('title'):
        return jsonify({'error': 'Title required'}), 400
    
    task = Task(
        title=data['title'],
        description=data.get('description', ''),
        due_date=data.get('due_date', datetime.now().strftime('%Y-%m-%d')),
        due_time=data.get('due_time', '23:59'),
        priority=data.get('priority', 'low'),
        category=data.get('category', 'Personal'),
        user_id=user.id
    )
    
    db.session.add(task)
    db.session.commit()
    
    return jsonify({'success': True, 'id': task.id})

@tasks_bp.route('/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Update a task (complete, edit)"""
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    data = request.json
    
    if 'done' in data:
        task.done = data['done']
        
        if task.done:
            user = get_current_user()
            reward = task.get_reward()
            user.coins += reward
            leveled_up = user.add_xp(reward * 10)
            db.session.commit()
            
            # Emit socket event
            from app import socketio
            socketio.emit('task_completed', {
                'task_id': task.id,
                'reward': reward,
                'new_coins': user.coins,
                'leveled_up': leveled_up,
                'new_level': user.level
            })
    
    if 'title' in data:
        task.title = data['title']
    if 'description' in data:
        task.description = data['description']
    if 'due_date' in data:
        task.due_date = data['due_date']
    if 'priority' in data:
        task.priority = data['priority']
    
    db.session.commit()
    return jsonify({'success': True})

@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task"""
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    db.session.delete(task)
    db.session.commit()
    
    from app import socketio
    socketio.emit('task_deleted', {'task_id': task_id})
    
    return jsonify({'success': True})