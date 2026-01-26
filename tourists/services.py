from datetime import timedelta
from django.utils import timezone

def process_traveler_heartbeat(traveler_id, current_lat, current_lon):
    traveler = Traveler.objects.get(blockchain_id=traveler_id)
    
    # 1. Simple Geofencing for Dzüko Valley
    # Approx coordinates: 25.62, 94.05
    if 25.61 < current_lat < 25.63 and 94.04 < current_lon < 94.06:
        traveler.is_in_danger_zone = True
    else:
        traveler.is_in_danger_zone = False

    # 2. Movement Detection
    if traveler.last_lat == current_lat and traveler.last_lon == current_lon:
        # Stationary. Check how long.
        time_inactive = timezone.now() - traveler.last_movement_time
        
        if time_inactive > timedelta(minutes=30) and traveler.is_in_danger_zone:
            traveler.status = 'RED' # Trigger Police Alert
        elif time_inactive > timedelta(minutes=15) and traveler.is_in_danger_zone:
            traveler.status = 'YELLOW' # Trigger "Are you alright?"
    else:
        # User is moving
        traveler.last_movement_time = timezone.now()
        traveler.status = 'GREEN'
        traveler.last_lat = current_lat
        traveler.last_lon = current_lon

    traveler.save()
    return traveler.status