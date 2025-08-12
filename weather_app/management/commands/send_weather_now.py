from django.core.management.base import BaseCommand
from weather_app.models import UserSubscription
from weather_app.weather_service import fetch_weather_for_all_subscriptions
from weather_app.tasks import send_weather_email, daily_weather_report
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Send weather emails immediately (bypass Celery scheduler)'

    def add_arguments(self, parser):
        parser.add_argument('--async', action='store_true', help='Use Celery tasks (async)')
        parser.add_argument('--sync', action='store_true', help='Send emails directly (sync)')
        parser.add_argument('--city', type=str, help='Send for specific city only')

    def handle(self, *args, **options):
        use_async = options.get('async', False)
        use_sync = options.get('sync', True)
        specific_city = options.get('city')
        
        self.stdout.write("🚀 Sending Weather Emails Now")
        self.stdout.write("=" * 50)
        
        if use_async:
            self.stdout.write("Using Celery tasks (async)...")
            self.send_async()
        else:
            self.stdout.write("Sending emails directly (sync)...")
            self.send_sync(specific_city)

    def send_sync(self, specific_city=None):
        """Send emails directly without Celery"""
        try:
            # Get weather data
            weather_data = fetch_weather_for_all_subscriptions()
            
            if not weather_data:
                self.stdout.write(self.style.ERROR("❌ No weather data found"))
                return
            
            total_sent = 0
            total_failed = 0
            
            # Filter by specific city if provided
            if specific_city:
                weather_data = {k: v for k, v in weather_data.items() if k.lower() == specific_city.lower()}
                if not weather_data:
                    self.stdout.write(self.style.ERROR(f"❌ No weather data found for {specific_city}"))
                    return
            
            # Process each city
            for city, data in weather_data.items():
                if not data.get('success'):
                    self.stdout.write(self.style.ERROR(f"❌ Weather data failed for {city}: {data.get('error')}"))
                    continue
                
                self.stdout.write(f"\n🌍 Processing {city}:")
                self.stdout.write(f"   🌡️ {data['temperature']}°C, {data['conditions']}")
                
                # Get subscribers
                subscribers = UserSubscription.objects.filter(city=city, status=True)
                self.stdout.write(f"   📧 Found {subscribers.count()} subscribers")
                
                # Send to each subscriber
                for i, subscription in enumerate(subscribers, 1):
                    try:
                        self.stdout.write(f"   [{i}/{subscribers.count()}] Sending to {subscription.email}...")
                        
                        result = send_weather_email(subscription.email, city, data)
                        
                        if "sent successfully" in result:
                            self.stdout.write(f"      ✅ Success")
                            total_sent += 1
                        else:
                            self.stdout.write(f"      ❌ Failed: {result}")
                            total_failed += 1
                            
                    except Exception as e:
                        self.stdout.write(f"      ❌ Error: {str(e)}")
                        total_failed += 1
            
            self.stdout.write(f"\n📊 Summary:")
            self.stdout.write(f"   ✅ Emails sent: {total_sent}")
            self.stdout.write(f"   ❌ Emails failed: {total_failed}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Command failed: {str(e)}"))

    def send_async(self):
        """Use Celery task"""
        try:
            result = daily_weather_report.delay()
            self.stdout.write(f"✅ Task queued with ID: {result.id}")
            self.stdout.write("Check Celery worker logs for progress")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to queue task: {str(e)}"))