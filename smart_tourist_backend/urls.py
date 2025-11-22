from django.contrib import admin
from django.urls import path, include
from .views import home

# --- Add these imports ---
from django.conf import settings
from django.conf.urls.static import static
# -------------------------

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('api/v1/auth/', include('tourists.urls')),
]

# --- Add this line at the bottom ---
# This tells Django how to serve static files during development.
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])