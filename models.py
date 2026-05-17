"""Database models"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# Association table for friends (many-to-many)
friends = db.Table('friends',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('friend_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('status', db.String(20), default='pending'),  # pending, accepted, blocked
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    avatar = db.Column(db.String(200), default='/static/default-avatar.png')
    bio = db.Column(db.String(500), default='')
    location = db.Column(db.String(100), default='')
    coins = db.Column(db.Integer, default=15)
    xp = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    is_online = db.Column(db.Boolean, default=False)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    tasks = db.relationship('Task', backref='user', lazy=True, cascade='all, delete-orphan')
    schedules = db.relationship('Schedule', backref='user', lazy=True, cascade='all, delete-orphan')
    
    # Friend relationships
    friends_list = db.relationship(
        'User', secondary=friends,
        primaryjoin=id == friends.c.user_id,
        secondaryjoin=id == friends.c.friend_id,
        lazy='dynamic'
    )
    
    def add_xp(self, amount):
        """Add XP and handle level ups"""
        self.xp += amount
        leveled_up = False
        while self.xp >= self.level * 100:
            self.level += 1
            leveled_up = True
        return leveled_up
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'avatar': self.avatar,
            'bio': self.bio,
            'location': self.location,
            'coins': self.coins,
            'xp': self.xp,
            'level': self.level,
            'is_online': self.is_online,
            'last_seen': self.last_seen.strftime('%Y-%m-%d %H:%M') if self.last_seen else None
        }
    
    def get_friends(self, status='accepted'):
        """Get friends by status"""
        if status == 'accepted':
            return User.query.join(friends, (User.id == friends.c.friend_id)).filter(
                friends.c.user_id == self.id, friends.c.status == 'accepted'
            ).union(
                User.query.join(friends, (User.id == friends.c.user_id)).filter(
                    friends.c.friend_id == self.id, friends.c.status == 'accepted'
                )
            ).all()
        return []

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    due_date = db.Column(db.String(20), nullable=False)
    due_time = db.Column(db.String(10), default='23:59')
    priority = db.Column(db.String(10), default='low')
    category = db.Column(db.String(50), default='Personal')
    done = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_reward(self):
        rewards = {'low': 5, 'med': 7, 'high': 10}
        return rewards.get(self.priority, 5)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'due_date': self.due_date,
            'due_time': self.due_time,
            'priority': self.priority,
            'category': self.category,
            'done': self.done
        }

class Schedule(db.Model):
    __tablename__ = 'schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    start_time = db.Column(db.String(10), nullable=False)
    end_time = db.Column(db.String(10), default='')
    days = db.Column(db.String(100), nullable=False)
    notes = db.Column(db.Text, default='')
    color = db.Column(db.String(20), default='lavender')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def get_days_list(self):
        return self.days.split(',') if self.days else []
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'days': self.get_days_list(),
            'notes': self.notes,
            'color': self.color
        }

class FriendRequest(db.Model):
    __tablename__ = 'friend_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    from_user = db.relationship('User', foreign_keys=[from_user_id])
    to_user = db.relationship('User', foreign_keys=[to_user_id])