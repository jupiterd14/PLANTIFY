"""Run the Flask application"""
from app import create_app, socketio

app = create_app('development')

if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("🚀 PLANIFY IS RUNNING!")
    print("📍 Open http://localhost:5000 in your browser")
    print("=" * 50 + "\n")
    
    socketio.run(app, debug=True, port=5000)