from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .models import User
# UPDATED: The import statement now uses the correct serializer class names
from .serializers import RegisterSerializer, VerifyEmailSerializer, VerifyPhoneSerializer, LoginSerializer
from .utils import send_email_otp, send_phone_otp

class RegisterView(generics.GenericAPIView):
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.generate_email_otp()
            send_email_otp(user.email, user.email_otp)
            return Response({
                "message": "Registration successful. Please check your email for OTP.",
                "data": { "email": user.email }
            }, status=status.HTTP_201_CREATED)
        
        # Provide more specific error messages
        error_messages = []
        for field, errors in serializer.errors.items():
            for error in errors:
                error_messages.append(f"{field}: {error}")
        return Response({"errors": error_messages}, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailOTPView(generics.GenericAPIView):
    serializer_class = VerifyEmailSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        
        try:
            user = User.objects.get(email=email)
            if user.email_otp == otp:
                user.is_email_verified = True
                user.email_otp = None # Clear OTP after verification
                user.save()
                
                # Now send phone OTP
                user.generate_phone_otp()
                send_phone_otp(user.phone, user.phone_otp)
                
                return Response({
                    "message": "Email verified successfully. Please check your phone for the next OTP.",
                     "data": { "phone": user.phone }
                }, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)


class VerifyPhoneOTPView(generics.GenericAPIView):
    serializer_class = VerifyPhoneSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone']
        otp = serializer.validated_data['otp']

        try:
            user = User.objects.get(phone=phone)
            if user.phone_otp == otp:
                user.is_phone_verified = True
                user.is_active = True
                user.phone_otp = None # Clear OTP
                user.save()
                
                token, _ = Token.objects.get_or_create(user=user)
                
                return Response({
                    "message": "Phone verified successfully. Registration complete.",
                    "token": token.key,
                    "user": {
                        "username": user.username,
                        "email": user.email
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"error": "User with this phone number does not exist."}, status=status.HTTP_404_NOT_FOUND)


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        user = authenticate(request, email=email, password=password)

        if user:
            if not user.is_active:
                return Response({"error": "Account not fully verified. Please complete the OTP process."}, status=status.HTTP_401_UNAUTHORIZED)
            
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                "message": "Login successful.",
                "token": token.key,
                "user": {
                    "username": user.username,
                    "email": user.email,
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)

