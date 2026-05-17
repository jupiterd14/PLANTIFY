"""Friends routes - Add, accept, remove friends"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, User, FriendRequest

friends_bp = Blueprint('friends', __name__)

@friends_bp.route('/search', methods=['GET'])
@login_required
def search_users():
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    
    users = User.query.filter(
        User.username.contains(query),
        User.id != current_user.id
    ).limit(10).all()
    
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'avatar': u.avatar,
        'level': u.level
    } for u in users])

@friends_bp.route('/requests', methods=['GET'])
@login_required
def get_requests():
    """Get pending friend requests"""
    pending = FriendRequest.query.filter_by(
        to_user_id=current_user.id, 
        status='pending'
    ).all()
    
    return jsonify([{
        'id': r.id,
        'from_user': r.from_user.username,
        'from_user_id': r.from_user.id,
        'avatar': r.from_user.avatar,
        'level': r.from_user.level,
        'created_at': r.created_at.strftime('%Y-%m-%d')
    } for r in pending])

@friends_bp.route('/add', methods=['POST'])
@login_required
def add_friend():
    data = request.json
    friend_id = data.get('user_id')
    
    if friend_id == current_user.id:
        return jsonify({'error': 'Cannot add yourself'}), 400
    
    friend = User.query.get(friend_id)
    if not friend:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if request already exists
    existing = FriendRequest.query.filter_by(
        from_user_id=current_user.id,
        to_user_id=friend_id,
        status='pending'
    ).first()
    
    if existing:
        return jsonify({'error': 'Request already sent'}), 400
    
    # Create friend request
    request_obj = FriendRequest(
        from_user_id=current_user.id,
        to_user_id=friend_id,
        status='pending'
    )
    db.session.add(request_obj)
    db.session.commit()
    
    # Emit socket notification
    from app import socketio
    socketio.emit('friend_request', {
        'from': current_user.username,
        'to': friend.username
    }, room=f'user_{friend_id}')
    
    return jsonify({'success': True, 'message': 'Friend request sent!'})

@friends_bp.route('/accept/<int:request_id>', methods=['POST'])
@login_required
def accept_request(request_id):
    req = FriendRequest.query.get_or_404(request_id)
    
    if req.to_user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    req.status = 'accepted'
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Friend added!'})

@friends_bp.route('/reject/<int:request_id>', methods=['POST'])
@login_required
def reject_request(request_id):
    req = FriendRequest.query.get_or_404(request_id)
    
    if req.to_user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(req)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Request rejected'})

@friends_bp.route('/list', methods=['GET'])
@login_required
def get_friends():
    """Get list of friends"""
    friends = current_user.get_friends()
    
    return jsonify([{
        'id': f.id,
        'username': f.username,
        'avatar': f.avatar,
        'level': f.level,
        'is_online': f.is_online
    } for f in friends])