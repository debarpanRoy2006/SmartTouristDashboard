from django.urls import path
from .views import RegisterView, VerifyEmailOTPView, VerifyPhoneOTPView, LoginView, dashboard

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-email/', VerifyEmailOTPView.as_view(), name='verify-email'),
    path('verify-phone/', VerifyPhoneOTPView.as_view(), name='verify-phone'),
    path('login/', LoginView.as_view(), name='login'),
    path('dashboard/', dashboard, name='dashboard'),  # <-- KEEP THIS ONE ONLY
    path('destination', dashboard, name='destination'),  # <-- KEEP THIS ONE ONLY
]
