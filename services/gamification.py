"""Gamification service - handles XP, levels, achievements"""
from models import User

class GamificationService:
    
    @staticmethod
    def calculate_xp_for_task(task):
        """Calculate XP reward based on task difficulty"""
        base_xp = {
            'low': 50,
            'med': 75,
            'high': 100
        }
        return base_xp.get(task.priority, 50)
    
    @staticmethod
    def check_achievements(user):
        """Check and unlock achievements"""
        achievements = []
        
        # Task master: completed 10 tasks
        completed_tasks = len([t for t in user.tasks if t.done])
        if completed_tasks >= 10:
            achievements.append('task_master')
        
        # Early bird: completed task before 9am
        # Coin collector: 100 coins
        if user.coins >= 100:
            achievements.append('coin_collector')
        
        # Level up rewards
        if user.level >= 5:
            achievements.append('rising_star')
        
        return achievements