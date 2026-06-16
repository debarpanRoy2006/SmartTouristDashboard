from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
import random
from django.utils import timezone
from django.conf import settings  # ADDED: To correctly link to your custom User model

class UserManager(BaseUserManager):
    """Define a model manager for User model."""

    def _create_user(self, email, password=None, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        if not extra_fields.get('username'):
            raise ValueError('The given username must be set')
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    # The 'name' field has been removed.
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, unique=True)
    passport_aadhaar = models.CharField(max_length=20, unique=True)

    is_phone_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)

    phone_otp = models.CharField(max_length=6, null=True, blank=True)
    email_otp = models.CharField(max_length=6, null=True, blank=True)

    USERNAME_FIELD = 'email'
    # 'name' has been removed from required fields.
    REQUIRED_FIELDS = ['username', 'phone', 'passport_aadhaar']

    objects = UserManager()

    def __str__(self):
        return self.email

    def generate_phone_otp(self):
        self.phone_otp = str(random.randint(100000, 999999))
        self.save()

    def generate_email_otp(self):
        self.email_otp = str(random.randint(100000, 999999))
        self.save()


class AuthorityProfile(models.Model):
    """
    Links a standard Django User account to a specific police department
    and sets their jurisdiction (e.g., Nagaland, Assam).
    """
    # FIXED: Now uses settings.AUTH_USER_MODEL to prevent the crash
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    department_name = models.CharField(max_length=150, help_text="e.g., Kohima Central Police")
    jurisdiction = models.CharField(max_length=100, help_text="e.g., Nagaland, Assam")

    def __str__(self):
        return f"{self.department_name} ({self.jurisdiction})"


class Traveler(models.Model):
    """
    Stores live tracking data, location, and emergency information for tourists.
    (Unified from your two previous model definitions)
    """
    STATUS_CHOICES = [
        ('safe', 'Safe'),
        ('warning', 'Warning'),
        ('emergency', 'Emergency / Unresponsive'),
    ]
    
    # Basic Info
    name = models.CharField(max_length=100)
    traveler_id = models.CharField(max_length=20, unique=True, default="TEMP_ID")
    blockchain_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Location Tracking
    current_region = models.CharField(
        max_length=100, 
        default="Nagaland", 
        help_text="Used to filter which police department sees this traveler"
    ) 
    last_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    last_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_name = models.CharField(max_length=150, blank=True, help_text="e.g., Dzüko Valley Forest")
    
    # Heartbeat monitoring & Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='safe')
    status_note = models.CharField(max_length=255, blank=True, help_text="e.g., SOS Button Triggered")
    last_movement_time = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    is_in_danger_zone = models.BooleanField(default=False)
    
    # Emergency Rescue Packet Data
    medical_info = models.TextField(blank=True, help_text="Medical history, blood type, allergies")
    emergency_contact = models.CharField(max_length=150, blank=True, help_text="Name and Phone Number")

    def __str__(self):
        return f"{self.name} ({self.traveler_id}) - {self.get_status_display()}"