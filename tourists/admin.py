from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User # Correctly import the 'User' model

# This custom admin class will display your extra fields in the Django admin panel.
class CustomUserAdmin(UserAdmin):
    model = User
    # Add your custom fields to the fieldsets to make them editable in the admin
    fieldsets = UserAdmin.fieldsets + (
            ('Tourist Information', {'fields': ('phone_number', 'passport_aadhaar')}),
            ('Verification Status', {'fields': ('is_email_verified', 'is_phone_verified')}),
    )
    # Display these fields in the user list view
    list_display = ['email', 'username', 'is_staff', 'is_active', 'is_email_verified', 'is_phone_verified']

# Register the User model with the custom admin class
admin.site.register(User, CustomUserAdmin)
