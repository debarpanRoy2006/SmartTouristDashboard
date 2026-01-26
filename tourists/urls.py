from django.urls import path
from . import views  # Import YOUR views.py from the current directory

urlpatterns = [
    # Page Rendering Views
    path('login/', views.login_page, name='login_page'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('destination/', views.dashboard, name='destination'),
    
    # Travel Feature Views (Now correctly referencing your views.py)
    path('explorer/', views.explorer, name='explorer'),
    path('itinerary/', views.itinerary_page, name='itinerary'),
    path('safety/', views.safety_page, name='safety'),
    path('nearby/', views.nearby_page, name='nearby'),
    path('history/', views.history_stats, name='history'),
    path('map/', views.map_page, name='map'),
    path('police-dashboard/', views.police_dashboard, name='police_dashboard'),

    # API Authentication Views (Keep as .as_view() for class-based views)
    path('api/v1/auth/register/', views.RegisterView.as_view(), name='register'),
    path('api/v1/auth/verify-email/', views.VerifyEmailOTPView.as_view(), name='verify-email'),
    path('api/v1/auth/verify-phone/', views.VerifyPhoneOTPView.as_view(), name='verify-phone'),
    path('api/v1/auth/login/', views.LoginView.as_view(), name='api_login'),
    
]