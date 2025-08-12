from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule

class Command(BaseCommand):
    help = 'Schedule daily weather emails at 7:00 PM PKT'
    
    def handle(self, *args, **options):
        # Delete any existing task with the same name
        PeriodicTask.objects.filter(name='Daily Weather Email').delete()

        # Create schedule for 7:30 PM PKT (19:30)
        schedule, created = CrontabSchedule.objects.get_or_create(
            hour=19,        # 7 PM
            minute=30,      # 30 minutes
            day_of_week='*',  # Every day
            timezone='Asia/Karachi'  # Pakistan Time
        )
        
        # Create the periodic task
        task = PeriodicTask.objects.create(
            name='Daily Weather Email',
            crontab=schedule,
            task='weather_app.tasks.daily_weather_report_sync',  # Updated task name
            enabled=True
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Scheduled daily weather emails at 7:30 PM PKT\n'
                f'   Task ID: {task.id}\n'
                f'   Schedule: Every day at 19:30 Asia/Karachi)\n'
                f'   Task: weather_app.tasks.daily_weather_report_sync'
            )
        )