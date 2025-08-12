from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from weather_app.models import UserSubscription
from weather_app.weather_service import fetch_weather_for_all_subscriptions, get_weather_data
from weather_app.tasks import daily_weather_report, send_weather_email
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Debug weather email system step by step'

    def add_arguments(self, parser):
        parser.add_argument('--step', type=str, choices=['all', 'db', 'weather', 'email', 'task'], 
                          default='all', help='Which step to debug')
        parser.add_argument('--email', type=str, help='Test email address')

    def handle(self, *args, **options):
        step = options['step']
        test_email = options.get('email', 'mhamzag567@gmail.com')
        
        self.stdout.write("🔍 DEBUG: Weather Email System")
        self.stdout.write("=" * 50)
        
        if step in ['all', 'db']:
            self.debug_database()
        
        if step in ['all', 'weather']:
            self.debug_weather_api()
            
        if step in ['all', 'email']:
            self.debug_email_settings()
            self.debug_direct_email(test_email)
            
        if step in ['all', 'task']:
            self.debug_celery_task()

    def debug_database(self):
        """Check database for subscriptions"""
        self.stdout.write("\n📊 Step 1: Database Check")
        self.stdout.write("-" * 30)
        
        total_users = UserSubscription.objects.count()
        active_users = UserSubscription.objects.filter(status=True).count()
        
        self.stdout.write(f"Total subscriptions: {total_users}")
        self.stdout.write(f"Active subscriptions: {active_users}")
        
        if active_users == 0:
            self.stdout.write(self.style.ERROR("❌ No active subscriptions found!"))
            self.stdout.write("   Create some test subscriptions first.")
            return
        
        # Show subscriptions by city
        from django.db.models import Count
        city_counts = UserSubscription.objects.filter(status=True).values('city').annotate(count=Count('city'))
        
        self.stdout.write("\nSubscriptions by city:")
        for item in city_counts:
            self.stdout.write(f"  🏙️ {item['city']}: {item['count']} subscribers")
            
        # Show recent subscriptions
        recent = UserSubscription.objects.filter(status=True).order_by('-subscribed_at')[:5]
        self.stdout.write("\nRecent active subscriptions:")
        for sub in recent:
            self.stdout.write(f"  📧 {sub.email} -> {sub.city} ({sub.subscribed_at.strftime('%Y-%m-%d %H:%M')})")

    def debug_weather_api(self):
        """Test weather API"""
        self.stdout.write("\n🌤️ Step 2: Weather API Check")
        self.stdout.write("-" * 30)
        
        try:
            weather_data = fetch_weather_for_all_subscriptions()
            
            if not weather_data:
                self.stdout.write(self.style.ERROR("❌ No weather data fetched!"))
                return
                
            self.stdout.write(f"✅ Fetched weather for {len(weather_data)} cities:")
            for city, data in weather_data.items():
                if data.get('success'):
                    self.stdout.write(f"  🌡️ {city}: {data['temperature']}°C, {data['conditions']}")
                else:
                    self.stdout.write(f"  ❌ {city}: {data.get('error', 'Unknown error')}")
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Weather API error: {str(e)}"))

    def debug_email_settings(self):
        """Check email configuration"""
        self.stdout.write("\n📧 Step 3: Email Settings Check")
        self.stdout.write("-" * 30)
        
        email_settings = {
            'EMAIL_HOST': getattr(settings, 'EMAIL_HOST', 'Not set'),
            'EMAIL_PORT': getattr(settings, 'EMAIL_PORT', 'Not set'),
            'EMAIL_HOST_USER': getattr(settings, 'EMAIL_HOST_USER', 'Not set'),
            'EMAIL_USE_TLS': getattr(settings, 'EMAIL_USE_TLS', 'Not set'),
            'DEFAULT_FROM_EMAIL': getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set'),
        }
        
        for key, value in email_settings.items():
            status = "✅" if value != 'Not set' else "❌"
            display_value = value if key != 'EMAIL_HOST_PASSWORD' else '*' * 10
            self.stdout.write(f"  {status} {key}: {display_value}")

    def debug_direct_email(self, test_email):
        """Test direct email sending"""
        self.stdout.write("\n📤 Step 4: Direct Email Test")
        self.stdout.write("-" * 30)
        
        try:
            # Test simple email
            self.stdout.write(f"Sending test email to: {test_email}")
            
            send_mail(
                subject="Weather System Test Email",
                message="This is a test email from the weather system.",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[test_email],
                fail_silently=False,
            )
            
            self.stdout.write(self.style.SUCCESS("✅ Test email sent successfully!"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to send test email: {str(e)}"))

    def debug_celery_task(self):
        """Test the actual Celery task"""
        self.stdout.write("\n⚙️ Step 5: Celery Task Test")
        self.stdout.write("-" * 30)
        
        try:
            self.stdout.write("Running daily_weather_report task...")
            result = daily_weather_report()
            self.stdout.write(f"✅ Task result: {result}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Task failed: {str(e)}"))
