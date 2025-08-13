import requests
import os
from django.conf import settings
from .models import WeatherLog, CITY_CHOICES
import logging
from dotenv import load_dotenv


# Set up logging
logger = logging.getLogger(__name__)

load_dotenv()

def get_weather_data(city):
    """
    Fetch weather data for a specific city - checks DB first, then API if needed
    
    Args:
        city (str): Name of the city
    
    Returns:
        dict: Weather data or None if failed
        Format: {
            'city': str,
            'temperature': float,
            'humidity': int,
            'conditions': str,
            'feels_like': float,
            'success': bool,
            'source': str ('database' or 'api'),
            'error': str (if success=False)
        }
    """
    try:
        from django.utils import timezone
        from datetime import timedelta
        
        # Validate city is in allowed list first
        valid_cities = [choice[0] for choice in CITY_CHOICES]
        if city not in valid_cities:
            logger.error(f"Invalid city: {city}")
            return {
                'success': False,
                'error': f'City "{city}" is not in the allowed list'
            }
        
        # Step 1: Check database for recent weather data (within last 3 hours)
        three_hours_ago = timezone.now() - timedelta(hours=3)
        recent_weather = WeatherLog.objects.filter(
            city=city,
            date__gte=three_hours_ago  # Changed from fetched_at to date
        ).order_by('-date').first()  # Changed from -fetched_at to -date
        
        if recent_weather:
            # Use cached data from database
            logger.info(f"📊 Using cached weather data for {city} (fetched at {recent_weather.date})")
            return {
                'city': city,
                'temperature': float(recent_weather.temperature),
                'humidity': recent_weather.humidity,
                'conditions': recent_weather.conditions,
                'feels_like': float(recent_weather.temperature),  # You can add feels_like field to model later
                'success': True,
                'source': 'database'
            }
        
        # Step 2: No recent data found, fetch from API
        logger.info(f"🌐 No recent data found for {city}, fetching from API")
        
        # Get API key from environment
        api_key = os.getenv('WEATHER_API')
        if not api_key:
            logger.error("Weather API key not found in environment variables")
            return {
                'success': False,
                'error': 'Weather API key not configured'
            }
        
        # Build API URL
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        
        # Make API request
        logger.info(f"Fetching fresh weather data for {city} from OpenWeather API")
        response = requests.get(url, timeout=10)
        
        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            
            # Extract relevant data
            weather_data = {
                'city': city,
                'temperature': round(data['main']['temp'], 1),
                'humidity': data['main']['humidity'],
                'conditions': data['weather'][0]['description'],
                'feels_like': round(data['main'].get('feels_like', data['main']['temp']), 1),
                'success': True,
                'source': 'api'
            }
            
            # Step 3: Save API result to database for future use
            try:
                WeatherLog.objects.create(
                    city=city,
                    temperature=weather_data['temperature'],
                    humidity=weather_data['humidity'],
                    conditions=weather_data['conditions'],
                    date=timezone.now()  # Changed from fetched_at to date
                )
                logger.info(f"💾 Saved fresh weather data for {city} to database")
            except Exception as save_error:
                logger.warning(f"⚠️ Failed to save weather data for {city}: {save_error}")
                # Don't fail the main request if saving fails
            
            logger.info(f"✅ Successfully fetched weather for {city}: {weather_data['temperature']}°C")
            return weather_data
            
        elif response.status_code == 404:
            logger.error(f"City not found: {city}")
            return {
                'success': False,
                'error': f'City "{city}" not found in weather service'
            }
        else:
            logger.error(f"API request failed for {city}: {response.status_code} - {response.text}")
            return {
                'success': False,
                'error': f'Weather API returned status {response.status_code}'
            }
            
    except requests.exceptions.Timeout:
        logger.error(f"Timeout while fetching weather for {city}")
        return {
            'success': False,
            'error': 'Request timeout while fetching weather data'
        }
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error while fetching weather for {city}")
        return {
            'success': False,
            'error': 'Connection error while fetching weather data'
        }
    except Exception as e:
        logger.error(f"Unexpected error while fetching weather for {city}: {str(e)}")
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }


def fetch_weather_for_cities(cities):
    """
    Fetch weather data for multiple cities
    
    Args:
        cities (list): List of city names
    
    Returns:
        dict: Results for each city
        Format: {
            'city_name': weather_data,
            ...
        }
    """
    results = {}
    
    for city in cities:
        weather_data = get_weather_data(city)
        results[city] = weather_data
        
        # Log the data source
        if weather_data.get('success'):
            source = weather_data.get('source', 'unknown')
            logger.info(f"Weather data for {city} obtained from: {source}")
    
    return results


def get_unique_subscription_cities():
    """
    Get list of unique cities from all active subscriptions
    
    Returns:
        list: List of unique city names that have active subscriptions
    """
    from .models import UserSubscription
    
    try:
        # Get unique cities from active subscriptions
        unique_cities = UserSubscription.objects.filter(
            status=True
        ).values_list('city', flat=True).distinct()
        
        cities_list = list(unique_cities)
        logger.info(f"Found {len(cities_list)} unique cities with active subscriptions: {cities_list}")
        return cities_list
        
    except Exception as e:
        logger.error(f"Error getting unique subscription cities: {str(e)}")
        return []


def fetch_weather_for_all_subscriptions():
    """
    Fetch weather data for all cities that have active subscriptions
    
    Returns:
        dict: Weather data for all subscription cities
    """
    # Get unique cities from subscriptions
    cities = get_unique_subscription_cities()
    
    if not cities:
        logger.info("No cities with active subscriptions found")
        return {}
    
    # Fetch weather for all cities
    logger.info(f"Fetching weather data for {len(cities)} cities")
    results = fetch_weather_for_cities(cities)
    
    # Log summary
    successful = sum(1 for result in results.values() if result.get('success'))
    failed = len(results) - successful
    logger.info(f"Weather fetch complete: {successful} successful, {failed} failed")
    
    return results


# Example usage and testing functions
def test_weather_api():
    """
    Test function to verify weather API is working
    """
    test_city = "London"
    result = get_weather_data(test_city)
    
    if result.get('success'):
        print(f"✅ Weather API test successful for {test_city}:")
        print(f"   Temperature: {result['temperature']}°C")
        print(f"   Humidity: {result['humidity']}%")
        print(f"   Conditions: {result['conditions']}")
    else:
        print(f"❌ Weather API test failed for {test_city}:")
        print(f"   Error: {result.get('error')}")
    
    return result
