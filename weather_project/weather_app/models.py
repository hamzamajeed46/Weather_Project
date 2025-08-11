from django.db import models
from django.core.validators import EmailValidator
from django.utils import timezone

# Predefined list of allowed cities
CITY_CHOICES = [
    ("London", "London"),
    ("New York", "New York"),
    ("Tokyo", "Tokyo"),
    ("Paris", "Paris"),
    ("Karachi", "Karachi"),
    # Add more cities as needed
]

class UserSubscription(models.Model):
    email = models.EmailField(
        validators=[EmailValidator()],
        unique=False  # Allow same email for different cities
    )
    city = models.CharField(max_length=100, choices=CITY_CHOICES)
    subscribed_at = models.DateTimeField(default=timezone.now)
    status = models.BooleanField(default=True)  # True = Active, False = Inactive

    class Meta:
        unique_together = ('email', 'city')  # Prevent duplicate subscription for same city

    def __str__(self):
        return f"{self.email} - {self.city} ({'Active' if self.status else 'Inactive'})"


class WeatherLog(models.Model):
    city = models.CharField(max_length=100, choices=CITY_CHOICES)
    temperature = models.FloatField()  # Temperature in °C
    humidity = models.PositiveIntegerField()  # Humidity percentage
    conditions = models.CharField(max_length=255)  # e.g., "clear sky"
    date = models.DateField(default=timezone.now)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.city} - {self.date}: {self.temperature}°C, {self.humidity}% humidity"
