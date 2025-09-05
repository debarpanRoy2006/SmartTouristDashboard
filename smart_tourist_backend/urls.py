from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from tourists.views import TouristViewSet, add_tourist, panic_button
from smart_tourist_backend.views import home

router = DefaultRouter()
router.register(r'tourists', TouristViewSet, basename='tourist')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('api/', include(router.urls)),
    path('api/add-tourist/', add_tourist, name='add-tourist'),
    path('api/panic/', panic_button, name='panic'),
]
