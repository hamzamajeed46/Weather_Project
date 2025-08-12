from django.shortcuts import render, redirect
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
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
    user_subscriptions = None
    if request.user.is_authenticated:
        user_subscriptions = UserSubscription.objects.filter(user=request.user)
    
    context = {
        'user_subscriptions': user_subscriptions
    }
    return render(request, 'weather_app/home.html', context)

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


@login_required
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
    responses={201: {'description': 'Subscription successful'}} 
)
@api_view(["POST"])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def subscribe(request):
    """Handle subscription via both HTML form and API"""
    try:
        # Check if it's a form submission or API call
        if request.content_type == 'application/json' or 'application/json' in request.META.get('CONTENT_TYPE', ''):
            # API call - get data from request.data (JSON)
            email = request.data.get('email')
            city = request.data.get('city')
            is_api_call = True
        else:
            # Form submission - get data from request.POST
            email = request.POST.get('email')
            city = request.POST.get('city')
            is_api_call = False
        
        # Get the authenticated user
        user = request.user
        
        # Validate email format
        if not email:
            error_msg = 'Email is required'
            if is_api_call:
                return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)
            else:
                messages.error(request, error_msg)
                return redirect('home')
        
        try:
            validate_email(email)
        except ValidationError:
            error_msg = 'Invalid email format'
            if is_api_call:
                return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)
            else:
                messages.error(request, error_msg)
                return redirect('home')
        
        # Validate city
        if not city:
            error_msg = 'City is required'
            if is_api_call:
                return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)
            else:
                messages.error(request, error_msg)
                return redirect('home')
        
        valid_cities = [choice[0] for choice in CITY_CHOICES]
        if city not in valid_cities:
            error_msg = 'City not in allowed list' if is_api_call else 'Invalid city selected'
            if is_api_call:
                return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)
            else:
                messages.error(request, error_msg)
                return redirect('home')
        
        # Check for duplicate subscription (user + city combination)
        if UserSubscription.objects.filter(user=user, city=city).exists():
            error_msg = 'You are already subscribed to this city'
            if is_api_call:
                return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)
            else:
                messages.warning(request, f'You are already subscribed to {city}.')
                return redirect('home')
        
        # Create subscription with user
        subscription = UserSubscription.objects.create(
            user=user,
            email=email,
            city=city
        )
        
        # Return appropriate response
        if is_api_call:
            return Response({
                'message': 'Successfully subscribed',
                'subscription_id': subscription.id,
                'user_id': user.id,
                'email': email,
                'city': city
            }, status=status.HTTP_201_CREATED)
        else:
            messages.success(request, f'Successfully subscribed to weather updates for {city}!')
            return redirect('home')
        
    except Exception as e:
        error_msg = 'An error occurred'
        if 'is_api_call' in locals() and is_api_call:
            return Response({'error': error_msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            messages.error(request, error_msg)
            return redirect('home')


@login_required
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
@api_view(["POST"])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def unsubscribe(request):
    """Handle unsubscription via both HTML form and API"""
    try:
        # Check if it's a form submission or API call
        if request.content_type == 'application/json' or 'application/json' in request.META.get('CONTENT_TYPE', ''):
            # API call - get data from request.data (JSON)
            email = request.data.get('email')
            city = request.data.get('city')
            is_api_call = True
        else:
            # Form submission - get data from request.POST
            email = request.POST.get('email')
            city = request.POST.get('city')
            is_api_call = False
        
        # Get the authenticated user
        user = request.user
        
        # Validate required fields
        if not email:
            error_msg = 'Email is required'
            if is_api_call:
                return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)
            else:
                messages.error(request, 'Please provide both email and city.')
                return redirect('home')
        
        if not city:
            error_msg = 'City is required'
            if is_api_call:
                return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)
            else:
                messages.error(request, 'Please provide both email and city.')
                return redirect('home')
        
        # Find subscription by user, email, and city
        try:
            subscription = UserSubscription.objects.get(
                user=user,
                email=email,
                city=city
            )
            subscription.delete()
            
            # Return appropriate response
            if is_api_call:
                return Response({
                    'message': 'Successfully unsubscribed',
                    'user_id': user.id,
                    'email': email,
                    'city': city
                }, status=status.HTTP_200_OK)
            else:
                messages.success(request, f'Successfully unsubscribed from {city} weather updates.')
                return redirect('home')
                
        except UserSubscription.DoesNotExist:
            error_msg = 'Subscription not found for this user, email, and city combination'
            if is_api_call:
                return Response({'error': error_msg}, status=status.HTTP_404_NOT_FOUND)
            else:
                messages.error(request, f'No subscription found for {city} with email {email}.')
                return redirect('home')
        
    except Exception as e:
        error_msg = 'An error occurred'
        if 'is_api_call' in locals() and is_api_call:
            return Response({'error': error_msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            messages.error(request, error_msg)
            return redirect('home')


@extend_schema(
    parameters=[
        {
            'name': 'email',
            'description': 'Email address to filter subscriptions',
            'required': False,
            'type': 'string',
            'in': 'query'
        }
    ],
    responses={
        200: {
            'description': 'List of subscriptions',
            'content': {
                'application/json': {
                    'type': 'object',
                    'properties': {
                        'subscriptions': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'id': {'type': 'integer'},
                                    'email': {'type': 'string'},
                                    'city': {'type': 'string'},
                                    'subscribed_at': {'type': 'string', 'format': 'date-time'},
                                    'status': {'type': 'boolean'}
                                }
                            }
                        },
                        'count': {'type': 'integer'}
                    }
                }
            }
        }
    }
)
@api_view(["GET"])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def list_subscriptions(request):
    try:
        # Get the authenticated user
        user = request.user
        
        # Get email parameter from query string
        email_filter = request.GET.get('email')
        
        # Start with user's subscriptions
        subscriptions = UserSubscription.objects.filter(user=user)
        
        # Filter by email if provided
        if email_filter:
            subscriptions = subscriptions.filter(email=email_filter)
        
        # Serialize the data
        subscription_data = []
        for subscription in subscriptions:
            subscription_data.append({
                'id': subscription.id,
                'email': subscription.email,
                'city': subscription.city,
                'subscribed_at': subscription.subscribed_at.isoformat(),
                'status': subscription.status
            })
        
        return Response({
            'subscriptions': subscription_data,
            'count': len(subscription_data)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({'error': 'An error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)