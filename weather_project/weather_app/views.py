from django.shortcuts import render, redirect
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from drf_spectacular.utils import extend_schema
from django.contrib import messages
from .models import UserSubscription, CITY_CHOICES
import json

def home(request):
    """Home page - shows different content based on authentication status"""
    return render(request, 'weather_app/home.html')

def auth_page(request):
    """Login and Signup page"""
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'weather_app/auth.html')

def login_view(request):
    """Handle user login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Successfully logged in!')
                return redirect('home')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please provide both username and password.')
    
    return redirect('auth_page')

def signup_view(request):
    """Handle user signup"""
    if request.method == 'POST':
        username = request.POST.get('signup_username')
        email = request.POST.get('signup_email')
        password = request.POST.get('signup_password')
        
        if username and email and password:
            # Check if username already exists
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists.')
                return redirect('auth_page')
            
            # Check if email already exists
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists.')
                return redirect('auth_page')
            
            # Validate email format
            try:
                validate_email(email)
            except ValidationError:
                messages.error(request, 'Invalid email format.')
                return redirect('auth_page')
            
            # Create user
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('home')
        else:
            messages.error(request, 'Please fill in all fields.')
    
    return redirect('auth_page')

def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'Successfully logged out!')
    return redirect('auth_page')


@extend_schema(
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'email': {'type': 'string', 'format': 'email'},
                'city': {'type': 'string'}
            },
            'required': ['email', 'city']
        }
    },
    responses={200: {'description': 'Subscription successful'}}
)
@csrf_exempt
@api_view(["POST"])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def subscribe(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        city = data.get('city')
        
        # Get the authenticated user
        user = request.user
        
        # Validate email format
        if not email:
            return JsonResponse({'error': 'Email is required'}, status=400)
        
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({'error': 'Invalid email format'}, status=400)
        
        # Validate city
        if not city:
            return JsonResponse({'error': 'City is required'}, status=400)
        
        valid_cities = [choice[0] for choice in CITY_CHOICES]
        if city not in valid_cities:
            return JsonResponse({'error': 'City not in allowed list'}, status=400)
        
        # Check for duplicate subscription (user + city combination)
        if UserSubscription.objects.filter(user=user, city=city).exists():
            return JsonResponse({'error': 'You are already subscribed to this city'}, status=400)
        
        # Create subscription with user
        subscription = UserSubscription.objects.create(
            user=user,
            email=email,
            city=city
        )
        
        return JsonResponse({
            'message': 'Successfully subscribed',
            'subscription_id': subscription.id,
            'user_id': user.id,
            'email': email,
            'city': city
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'An error occurred'}, status=500)


@extend_schema(
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'email': {'type': 'string', 'format': 'email'},
                'city': {'type': 'string'}
            },
            'required': ['email', 'city']
        }
    },
    responses={200: {'description': 'Unsubscribed successfully'}}
)
@csrf_exempt
@api_view(["POST"])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def unsubscribe(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        city = data.get('city')
        
        # Get the authenticated user
        user = request.user
        
        # Validate required fields
        if not email:
            return JsonResponse({'error': 'Email is required'}, status=400)
        
        if not city:
            return JsonResponse({'error': 'City is required'}, status=400)
        
        # Find subscription by user, email, and city
        try:
            subscription = UserSubscription.objects.get(
                user=user,
                email=email,
                city=city
            )
            subscription.delete()
            return JsonResponse({
                'message': 'Successfully unsubscribed',
                'user_id': user.id,
                'email': email,
                'city': city
            }, status=200)
        except UserSubscription.DoesNotExist:
            return JsonResponse({
                'error': 'Subscription not found for this user, email, and city combination'
            }, status=404)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'An error occurred'}, status=500)