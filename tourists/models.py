from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
import random

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
