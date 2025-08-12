from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import UserSubscription
from .weather_service import fetch_weather_for_all_subscriptions
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_weather_email(user_email, city, weather_data):
    """Send weather email to a single user"""
    try:
        logger.info(f"Sending weather email to {user_email} for {city}")
        
        # Create HTML email content
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f7fa; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 15px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 28px; font-weight: 300; }}
                .weather-content {{ padding: 40px 30px; text-align: center; }}
                .temperature {{ font-size: 64px; font-weight: bold; color: #667eea; margin: 20px 0; }}
                .condition {{ font-size: 24px; color: #555; margin-bottom: 30px; text-transform: capitalize; }}
                .details {{ display: flex; justify-content: space-around; background: #f8f9fa; padding: 25px; border-radius: 10px; margin: 20px 0; }}
                .detail-item {{ text-align: center; }}
                .detail-label {{ font-size: 14px; color: #666; margin-bottom: 5px; }}
                .detail-value {{ font-size: 20px; font-weight: bold; color: #333; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🌤️ Daily Weather Report</h1>
                    <h2>{city}</h2>
                </div>
                
                <div class="weather-content">
                    <div class="temperature">{weather_data['temperature']}°C</div>
                    <div class="condition">{weather_data['conditions']}</div>
                    
                    <div class="details">
                        <div class="detail-item">
                            <div class="detail-label">💧 Humidity</div>
                            <div class="detail-value">{weather_data['humidity']}%</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">🌡️ Feels Like</div>
                            <div class="detail-value">{weather_data.get('feels_like', weather_data['temperature'])}°C</div>
                        </div>
                    </div>
                </div>
                
                <div class="footer">
                    <p>Have a wonderful day! 🌟</p>
                    <p>Weather data provided by OpenWeatherMap</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        plain_message = f"""
        Daily Weather Report for {city}
        
        Temperature: {weather_data['temperature']}°C
        Conditions: {weather_data['conditions']}
        Humidity: {weather_data['humidity']}%
        
        Have a great day!
        """
        
        send_mail(
            subject=f"Daily Weather Report for {city}",
            message=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"✅ Email sent successfully to {user_email} for {city}")
        return f"Email sent to {user_email} for {city}"
        
    except Exception as e:
        logger.error(f"❌ Failed to send email to {user_email} for {city}: {e}")
        return f"Failed to send email to {user_email}: {str(e)}"

@shared_task
def daily_weather_report_sync():
    """Daily weather report task with synchronous email sending"""
    logger.info("🚀 Starting daily weather report task (synchronous)...")
    
    try:
        # Get weather data for all subscription cities
        weather_data = fetch_weather_for_all_subscriptions()
        
        if not weather_data:
            logger.warning("No weather data found")
            return "No weather data found"
        
        total_emails_sent = 0
        total_emails_failed = 0
        
        # Process each city
        for city, data in weather_data.items():
            if not data.get('success'):
                logger.error(f"Weather data failed for {city}: {data.get('error')}")
                continue
                
            logger.info(f"Processing {city}: {data['temperature']}°C, {data['conditions']}")
            
            # Get all subscribers for this city
            subscribers = UserSubscription.objects.filter(city=city, status=True)
            logger.info(f"Found {subscribers.count()} subscribers for {city}")
            
            # Send email to each subscriber synchronously
            for subscription in subscribers:
                try:
                    logger.info(f"Sending email to {subscription.email} for {city}")
                    
                    # Send email directly (synchronously)
                    result = send_weather_email(subscription.email, city, data)
                    
                    if "sent successfully" in result:
                        total_emails_sent += 1
                        logger.info(f"✅ Email sent to {subscription.email}")
                    else:
                        total_emails_failed += 1
                        logger.error(f"❌ Failed to send to {subscription.email}: {result}")
                        
                except Exception as e:
                    logger.error(f"❌ Failed to send email to {subscription.email}: {e}")
                    total_emails_failed += 1
        
        result_message = f"Processed {len(weather_data)} cities. Sent: {total_emails_sent}, Failed: {total_emails_failed}"
        logger.info(f"✅ Task completed: {result_message}")
        
        return result_message
        
    except Exception as e:
        error_message = f"Daily weather report task failed: {str(e)}"
        logger.error(f"❌ {error_message}")
        return error_message

@shared_task
def daily_weather_report():
    """Original async task (kept for backward compatibility)"""
    return daily_weather_report_sync()

@shared_task
def test_email_task(test_email="mhamzag567@gmail.com"):
    """Test task to send a simple email"""
    try:
        logger.info(f"Sending test email to {test_email}")
        
        send_mail(
            subject="Celery Test Email",
            message="This is a test email from Celery to verify the system is working.",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[test_email],
            fail_silently=False,
        )
        
        logger.info(f"✅ Test email sent successfully to {test_email}")
        return f"Test email sent to {test_email}"
        
    except Exception as e:
        logger.error(f"❌ Failed to send test email: {e}")
        return f"Failed to send test email: {str(e)}"