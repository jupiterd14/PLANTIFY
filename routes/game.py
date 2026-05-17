"""Game routes"""
from flask import Blueprint, jsonify, request
from models import db, User

game_bp = Blueprint('game', __name__)

def get_current_user():
    user = User.query.get(1)
    if not user:
        user = User(username="demo_user")
        db.session.add(user)
        db.session.commit()
    return user

@game_bp.route('/play', methods=['POST'])
def play_game():
    """Start a game - deduct coins"""
    data = request.json
    user = get_current_user()
    
    cost = 5
    
    if user.coins < cost:
        return jsonify({'error': 'Not enough coins'}), 400
    
    user.coins -= cost
    db.session.commit()
    
    return jsonify({'success': True, 'coins': user.coins})

@game_bp.route('/reward', methods=['POST'])
def game_reward():
    """Add game winnings"""
    data = request.json
    user = get_current_user()
    
    earned = data.get('earned', 0)
    user.coins += earned
    db.session.commit()
    
    return jsonify({'success': True, 'coins': user.coins})