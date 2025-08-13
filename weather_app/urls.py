from django.urls import path
from . import views

urlpatterns = [
    # Home page
    path('', views.home, name='home'),
    
    # Authentication pages
    path('auth/', views.auth_page, name='auth_page'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    
    # Form handlers (using same functions as API)
    path('subscribe-form/', views.subscribe, name='subscribe_form'),
    path('unsubscribe-form/', views.unsubscribe, name='unsubscribe_form'),
    
    # API endpoints
    path('api/subscribe/', views.subscribe, name='subscribe'),
    path('api/unsubscribe/', views.unsubscribe, name='unsubscribe'),
    path('unsubscribe-link/', views.unsubscribe_link, name='unsubscribe_link'),
    path('api/subscriptions/', views.list_subscriptions, name='list_subscriptions'),
    path('api/weather/history/<str:city>/', views.get_weather_history, name='weather_history'),
]
