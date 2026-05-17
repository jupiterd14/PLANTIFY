"""Application configuration"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Ensure database directory exists
DB_DIR = Path(__file__).parent / 'database'
DB_DIR.mkdir(exist_ok=True)

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-me')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_DIR / "planify.db"}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Game settings
    GAME_COST = 5
    
    # Task rewards
    TASK_REWARDS = {
        'low': 5,
        'med': 7,
        'high': 10
    }
    
    # XP per level
    XP_PER_LEVEL = 100
    
    # Session settings
    REMEMBER_COOKIE_DURATION = 30 * 24 * 3600  # 30 days

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}