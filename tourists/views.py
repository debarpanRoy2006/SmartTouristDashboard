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
import re
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required


import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)


from duckduckgo_search import DDGS 

# Existing imports
from .models import User
from .serializers import RegisterSerializer, VerifyEmailSerializer, VerifyPhoneSerializer, LoginSerializer
from .utils import send_email_otp, send_phone_otp

# --- CONFIGURATION FOR AI ---
genai.configure(api_key="AIzaSyCN1ENCcvps_l5dNnRTC_6yJUfvvOJAdSg")

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







def safety_page(request):
    assessment = None
    city = request.POST.get('city', '')

    if request.method == "POST":
        # Get Safety Report from Gemini
        prompt = (
            f"Provide a detailed travel safety report for {city}. "
            f"Use clear headers for Crime, Health, and Transport. "
            f"Provide 3 specific Emergency Tips. "
            f"Keep the tone professional and do not use raw JSON."
        )
        
        try:
            response = ai_model.generate_content(prompt)
            assessment = response.text
        except Exception:
            assessment = "Safety system is temporarily busy. Please try again."

    return render(request, 'safety.html', {
        'assessment': assessment, 
        'city': city
    })
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



def itinerary_page(request):
    plan_data = [] # List to hold our structured day dictionaries
    location = ""
    days = ""

    if request.method == "POST":
        location = request.POST.get('location')
        days = request.POST.get('days')
        
        # Engineering a structured response for easy parsing
        prompt = (
            f"Generate a {days}-day itinerary for {location}. "
            f"Strictly start each new day with the marker '###DAY [Number]###'. "
            f"Include sections for Morning, Afternoon, Evening, and a Safety Tip. "
            f"Keep text clean without extra markdown symbols like **."
        )
        
        try:
            response = ai_model.generate_content(prompt)
            raw_text = response.text
            
            # Parsing the AI text into individual Day cards
            days_raw = re.split(r'###DAY \d+###', raw_text)
            for index, content in enumerate(days_raw[1:], start=1):
                if content.strip():
                    plan_data.append({
                        "count": index,
                        "content": content.strip().replace('\n', '<br>') # Convert newlines for HTML
                    })
        except Exception as e:
            plan_data = [{"count": "!", "content": f"Architect Error: {str(e)}"}]

    return render(request, 'itinerary.html', {
        'plan_data': plan_data,
        'location': location,
        'days': days
    })
import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Traveler

@login_required(login_url='/staff-login/')
def police_dashboard(request):
    # 1. Security Check: Ensure the user is a registered police authority
    if not hasattr(request.user, 'authorityprofile'):
        return redirect('home')
        
    profile = request.user.authorityprofile
    jurisdiction = profile.jurisdiction
    
    # 2. Fetch travelers only in this officer's jurisdiction
    travelers = Traveler.objects.filter(current_region=jurisdiction).order_by('-last_updated')
    
    # 3. Calculate Stats
    safe_count = travelers.filter(status='safe').count()
    alert_count = travelers.exclude(status='safe').count()
    
    # 4. Prepare data for the Leaflet Map (JavaScript)
    map_data = []
    for t in travelers:
        if t.last_latitude and t.last_longitude:
            map_data.append({
                'id': t.traveler_id,
                'name': t.name,
                'lat': float(t.last_latitude),
                'lng': float(t.last_longitude),
                'status': t.status,
                'location': t.location_name or "Unknown Location",
                'note': t.status_note or "No recent alerts"
            })

    context = {
        'department_name': profile.department_name,
        'jurisdiction': jurisdiction,
        'travelers': travelers,
        'safe_count': safe_count,
        'alert_count': alert_count,
        'map_data_json': json.dumps(map_data) # Passes data safely to JavaScript
    }
    
    return render(request, 'policedashboard.html', context)

    
    
def fetch_blockchain_id_details(request, blockchain_id):
    # Mocking a call to a Smart Contract/Decentralized Ledger
    # In a real scenario, you'd use web3.py here
    rescue_packet = {
        "verified_id": blockchain_id,
        "aadhar_hash": "67xx-xxxx-xx89",
        "medical_info": {
            "blood_group": "O+",
            "emergency_contact": "+91-98765-43210"
        },
        "path_history": "/api/v1/traveler/path/8821/"
    }
    return JsonResponse(rescue_packet)
<<<<<<< HEAD
=======



def staff_login_view(request):
    # If already logged in, redirect them immediately to their respective dashboards
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('adminpage') 
        elif hasattr(request.user, 'authorityprofile'):
            return redirect('police_dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # --- REDIRECT LOGIC ---
            if user.is_superuser:
                # Redirect to your custom Super Admin panel
                return redirect('adminpage') 
            elif hasattr(user, 'authorityprofile'):
                # Redirect to the Regional Police Command Center
                return redirect('police_dashboard')
            else:
                # Regular users shouldn't use this portal
                messages.error(request, "Access Denied: You lack Authority clearance.")
                return redirect('home') # Or wherever regular users go
                
        else:
            messages.error(request, "Invalid Badge ID or Secure Access Key.")
    else:
        form = AuthenticationForm()
        
    return render(request, 'staff_login.html', {'form': form})
import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.csrf import csrf_exempt
from .models import AuthorityProfile
User = get_user_model()
# --- SECURITY HELPER ---
def is_superuser(user):
    """Check if the user is a master admin"""
    return user.is_active and user.is_superuser

# --- 1. PAGE RENDER VIEW ---
@user_passes_test(is_superuser, login_url='/staff-login/')
def adminpage(request):
    """
    Renders the Super Admin dashboard.
    Fetches all active authority profiles to populate the HTML table.
    """
    # Using select_related to optimize the database query for the linked User model
    authorities = AuthorityProfile.objects.select_related('user').all().order_by('-id')
    
    context = {
        'authorities': authorities
    }
    return render(request, 'adminpage.html', context)


import uuid
import random
from django.contrib.auth import get_user_model

User = get_user_model()
def tracking_page(request):
    return render(request, 'tracking.html')
# ... (keep your adminpage view the same) ...

@csrf_exempt
@user_passes_test(is_superuser, login_url='/staff-login/')
def create_authority_account(request):
    """
    API endpoint that receives JSON data from the adminpage form,
    securely hashes the password, and provisions the account.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            department_name = data.get('department_name')
            jurisdiction = data.get('jurisdiction')
            username = data.get('username')
            password = data.get('password')

            if not all([department_name, jurisdiction, username, password]):
                return JsonResponse({"error": "All fields are required."}, status=400)

            if User.objects.filter(username=username).exists():
                return JsonResponse({"error": f"Username '{username}' is already in use."}, status=400)

            # --- THE FIX: Generate missing required fields for your custom model ---
            official_email = f"{username}@police.smarttourist.gov"
            # Generate a unique fake phone and ID just to satisfy your Traveler database constraints
            unique_phone = str(random.randint(1000000000, 9999999999)) 
            unique_id = f"AUTH-{uuid.uuid4().hex[:8].upper()}"

            # Pass the email first (as required by your custom UserManager) 
            # and include the other required extra_fields.
            user = User.objects.create_user(
                email=official_email,
                password=password,
                username=username,
                phone=unique_phone,
                passport_aadhaar=unique_id
            )

            # 2. Create the linked Authority Profile
            AuthorityProfile.objects.create(
                user=user,
                jurisdiction=jurisdiction,
                department_name=department_name
            )

            return JsonResponse({
                "success": f"Account for {department_name} successfully provisioned!"
            }, status=201)

        except Exception as e:
            return JsonResponse({"error": f"Server error: {str(e)}"}, status=500)
            
    return JsonResponse({"error": "Method not allowed. Use POST."}, status=405)
>>>>>>> dedec42e8b5fd72ac9b91b686e17a3e295fc0a71
