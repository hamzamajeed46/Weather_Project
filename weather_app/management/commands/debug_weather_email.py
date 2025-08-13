from django.core.management.base import BaseCommand
from weather_app.tasks import daily_weather_report_sync
from celery import current_app
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test the exact task that Celery Beat should run'
    
    def add_arguments(self, parser):
        parser.add_argument('--celery', action='store_true', help='Run via Celery worker')
        parser.add_argument('--direct', action='store_true', help='Run directly (default)')
    
    def handle(self, *args, **options):
        use_celery = options.get('celery', False)
        
        self.stdout.write("🧪 Testing Scheduled Task")
        self.stdout.write("=" * 50)
        
        if use_celery:
            self.test_via_celery()
        else:
            self.test_direct()
    
    def test_direct(self):
        """Run the task directly (same as debug command)"""
        self.stdout.write("🔄 Running task directly...")
        
        try:
            result = daily_weather_report_sync()
            self.stdout.write(self.style.SUCCESS(f"✅ Direct execution result: {result}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Direct execution failed: {e}"))
    
    def test_via_celery(self):
        """Run the task via Celery worker"""
        self.stdout.write("🔄 Sending task to Celery worker...")
        
        try:
            # Check if Celery is available
            celery_app = current_app
            self.stdout.write(f"📡 Celery broker: {celery_app.conf.broker_url}")
            
            # Send task to worker
            result = daily_weather_report_sync.delay()
            self.stdout.write(f"📨 Task sent with ID: {result.id}")
            
            # Wait for result (timeout after 30 seconds)
            try:
                task_result = result.get(timeout=30)
                self.stdout.write(self.style.SUCCESS(f"✅ Celery task result: {task_result}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Celery task failed or timed out: {e}"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Celery execution failed: {e}"))