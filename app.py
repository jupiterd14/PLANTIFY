"""Flask app factory and initialization"""
from flask import Flask, redirect, url_for
from flask_socketio import SocketIO
from flask_login import LoginManager
from config import config
from models import db, User

# Initialize extensions
socketio = SocketIO()
login_manager = LoginManager()

def create_app(config_name='default'):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.profile import profile_bp
    from routes.friends import friends_bp
    from routes.tasks import tasks_bp
    from routes.schedules import schedules_bp
    from routes.user import user_bp
    from routes.game import game_bp
    from routes.websocket import websocket_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(profile_bp, url_prefix='/profile')
    app.register_blueprint(friends_bp, url_prefix='/friends')
    app.register_blueprint(tasks_bp, url_prefix='/api/tasks')
    app.register_blueprint(schedules_bp, url_prefix='/api/schedules')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(game_bp, url_prefix='/api/game')
    app.register_blueprint(websocket_bp)
    
    # Main route - redirect to login if not authenticated
    @app.route('/')
    def index():
        from flask_login import current_user
        if current_user.is_authenticated:
            return render_template('index.html', user=current_user)
        return redirect(url_for('auth.login'))
    
    # Create tables and sample data
    with app.app_context():
        db.create_all()
    
    return app

# Import here to avoid circular imports
from flask import render_template