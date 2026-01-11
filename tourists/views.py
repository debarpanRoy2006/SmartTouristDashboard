import os
import time  
import requests
import google.generativeai as genai
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
import json

import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)


from duckduckgo_search import DDGS 

# Existing imports
from .models import User
from .serializers import RegisterSerializer, VerifyEmailSerializer, VerifyPhoneSerializer, LoginSerializer
from .utils import send_email_otp, send_phone_otp

# --- CONFIGURATION FOR AI ---
genai.configure(api_key="AIzaSyDM6sFBd-l44AxT3ci-USCNDlfuNHgGGDM")

# 1. Fetch valid models from Google
valid_models = []
print("Checking available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            valid_models.append(m.name)
except Exception as e:
    print(f"Error listing models: {e}")

# 2. Automatically select the best available model
selected_model_name = 'gemini-pro' # Default fallback

if valid_models:
    if 'models/gemini-1.5-flash' in valid_models:
        selected_model_name = 'models/gemini-1.5-flash'
    elif 'models/gemini-pro' in valid_models:
        selected_model_name = 'models/gemini-pro'
    else:
        selected_model_name = valid_models[0]

print(f"✅ ACTIVATING MODEL: {selected_model_name}")
ai_model = genai.GenerativeModel(selected_model_name)

# ==========================================
# AUTHENTICATION VIEWS (Kept Intact)
# ==========================================

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
                user.email_otp = None 
                user.save()
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
                user.phone_otp = None 
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

# ==========================================
# PAGE RENDERING VIEWS
# ==========================================

def dashboard(request):
    return render(request, 'dashboard.html')

def login_page(request):
    return render(request, 'login.html')

def explorer_page(request):
    # Legacy function for old template route
    query = request.GET.get('query', 'travel')
    images = []
    return render(request, 'explorer.html', {'images': images, 'query': query})

def itinerary_page(request):
    plan = ""
    if request.method == "POST":
        location = request.POST.get('location')
        days = request.POST.get('days')
        prompt = f"Provide a detailed {days}-day travel itinerary for {location}. Break it down into morning, afternoon, and evening."
        try:
            ai_response = ai_model.generate_content(prompt)
            plan = ai_response.text
        except Exception as e:
            plan = f"Could not generate plan: {str(e)}"
    return render(request, 'itinerary.html', {'plan': plan})

def safety_page(request):
    assessment = None
    if request.method == "POST":
        city = request.POST.get('city')
        import random
        score = random.randint(30, 98)
        prompt = f"Give 3 vital safety tips for a tourist in {city}."
        try:
            tips = ai_model.generate_content(prompt).text
        except:
            tips = "Always stay alert and check local news."
        assessment = {'city': city, 'score': score, 'tips': tips}
    return render(request, 'safety.html', {'assessment': assessment})

def nearby_page(request):
    return render(request, 'nearby.html')

def history_stats(request):
    past_trips = [
        {'name': 'Goa', 'score': 85},
        {'name': 'Shimla', 'score': 92},
        {'name': 'Delhi', 'score': 68},
        {'name': 'Munnar', 'score': 90}
    ]
    avg_score = sum(trip['score'] for trip in past_trips) // len(past_trips) if past_trips else 0
    context = {'past_trips': past_trips, 'avg_score': avg_score}
    return render(request, 'history.html', context)

def map_page(request):
    return render(request, 'map.html')



def fetch_image_from_web(query):
    """
    Searches the entire web for an image using DuckDuckGo.
    Replaces the old Wikipedia fetcher to find more local results.
    """
    try:
        search_term = f"{query} tourism high quality"
        
      
        with DDGS() as ddgs:
            results = list(ddgs.images(
                search_term, 
                max_results=1,
                safesearch='on', 
                layout='Wide',   
            ))
            
            if results:
                print(f"DuckDuckGo found image for: {query}")
                return results[0]['image']
                
    except Exception as e:
        
        print(f"Image Search Error for {query}: {e}")
    
    return None

def explorer(request):
    query = request.GET.get('query', '')
    attractions = []
    
    
    SAFE_FALLBACK_IMG = "https://dummyimage.com/600x400/cccccc/000000&text=Image+Not+Found"

    if query:
        
        try:
            prompt = (
                f"Identify 4 real, popular tourist attractions in {query}. "
                f"Return the data ONLY as a JSON list of objects. "
                f"Example format: [{{'name': 'Spot Name', 'description': 'Short info', 'rating': 4.5}}]. "
                f"If the city does not exist, return an empty list []."
            )
            ai_response = ai_model.generate_content(prompt)
            clean_json = ai_response.text.replace('```json', '').replace('```', '').strip()
            attractions = json.loads(clean_json)
        except Exception as e:
            print(f"AI Error: {e}")
            attractions = []

       
        for spot in attractions:
            full_search_query = f"{spot['name']} {query}"
            
            
            image_url = fetch_image_from_web(full_search_query)
            
            if image_url:
                spot['image_url'] = image_url
            else:
                spot['image_url'] = SAFE_FALLBACK_IMG
            
            
            time.sleep(1.8)

    return render(request, 'explorer.html', {
        'query': query,
        'attractions': attractions
    })