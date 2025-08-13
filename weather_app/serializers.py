from rest_framework import serializers
from .models import UserSubscription, WeatherLog


class UserSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for UserSubscription model"""
    class Meta:
        model = UserSubscription
        fields = ['id', 'user', 'city', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class WeatherLogSerializer(serializers.ModelSerializer):
    """Serializer for WeatherLog model"""
    class Meta:
        model = WeatherLog
        fields = ['id', 'city', 'temperature', 'humidity', 'conditions', 'date']
        read_only_fields = ['id', 'date']
