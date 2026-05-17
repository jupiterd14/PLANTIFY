"""Reminder service for due tasks"""
from datetime import datetime, timedelta
from models import Task

class ReminderService:
    
    @staticmethod
    def get_due_soon_tasks(user_id, hours=24):
        """Get tasks due within next X hours"""
        now = datetime.now()
        cutoff = now + timedelta(hours=hours)
        
        tasks = Task.query.filter_by(user_id=user_id, done=False).all()
        due_soon = []
        
        for task in tasks:
            try:
                due_dt = datetime.strptime(f"{task.due_date} {task.due_time}", "%Y-%m-%d %H:%M")
                if now < due_dt <= cutoff:
                    due_soon.append(task)
            except:
                pass
        
        return due_soon
    
    @staticmethod
    def format_reminder_message(task):
        """Format reminder text"""
        try:
            due_dt = datetime.strptime(f"{task.due_date} {task.due_time}", "%Y-%m-%d %H:%M")
            hours_left = (due_dt - datetime.now()).total_seconds() / 3600
            
            if hours_left < 1:
                return f"URGENT: {task.title} is due in less than an hour!"
            elif hours_left < 6:
                return f"⚠️ {task.title} is due in {int(hours_left)} hours"
            else:
                return f"Reminder: {task.title} is due tomorrow"
        except:
            return f"Reminder: {task.title} is due on {task.due_date}"