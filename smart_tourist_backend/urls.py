from django.contrib import admin
from django.urls import path, include
from .views import home # Import from the project's views.py

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # The root URL of your site will now be handled by this home view
    path('', home, name='home'),
    
    # Your API endpoints will be prefixed with 'api/v1/auth/'
    path('api/v1/auth/', include('tourists.urls')),
]
