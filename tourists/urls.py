from django.urls import path
from .views import RegisterView, VerifyEmailOTPView, VerifyPhoneOTPView, LoginView

# These are the API endpoints that your frontend will communicate with.
urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-email/', VerifyEmailOTPView.as_view(), name='verify-email'),
    path('verify-phone/', VerifyPhoneOTPView.as_view(), name='verify-phone'),
    path('login/', LoginView.as_view(), name='login'),
]
