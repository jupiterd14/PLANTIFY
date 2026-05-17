"""WebSocket event handlers"""
from flask import Blueprint
from app import socketio

websocket_bp = Blueprint('websocket', __name__)

@socketio.on('connect')
def handle_connect():
    """Client connected"""
    print(f'🔌 Client connected: {request.sid}')
    socketio.emit('connected', {'message': 'Connected to Planify!'})

@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected"""
    print(f'🔌 Client disconnected: {request.sid}')

# Import request here to avoid circular import
from flask import request