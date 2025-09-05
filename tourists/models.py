from django.db import models
class Tourist(models.Model):
    name = models.CharField(max_length=200)
    passport_id = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    itinerary = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name
