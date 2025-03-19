# from rest_framework import viewsets
# from rest_framework.response import Response
# from rest_framework import status
# from .serializers import TripInputSerializer, TripSerializer, RouteSerializer
# from .models import Location, Trip, Route, Stop, Log
# from geopy.geocoders import Nominatim
# import requests
# import polyline
#
#
# class TripPlanViewSet(viewsets.ViewSet):
#
#     def create(self, request):
#         # Validate input
#         serializer = TripInputSerializer(data=request.data)
#         if not serializer.is_valid():
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#         data = serializer.validated_data
#         current_loc_name = data['current_location']
#         pickup_loc_name = data['pickup_location']
#         dropoff_loc_name = data['dropoff_location']
#         current_cycle_used = data['current_cycle_used']
#
#         # Geocode locations
#         geolocator = Nominatim(user_agent="trip_planner")
#         try:
#             current_coords = geolocator.geocode(current_loc_name)
#             pickup_coords = geolocator.geocode(pickup_loc_name)
#             dropoff_coords = geolocator.geocode(dropoff_loc_name)
#             if not all([current_coords, pickup_coords, dropoff_coords]):
#                 return Response({"error": "Invalid location"}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception:
#             return Response({"error": "Geocoding failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#         # Save locations to database
#         current_loc, _ = Location.objects.get_or_create(
#             name=current_loc_name, latitude=current_coords.latitude, longitude=current_coords.longitude
#         )
#         pickup_loc, _ = Location.objects.get_or_create(
#             name=pickup_loc_name, latitude=pickup_coords.latitude, longitude=pickup_coords.longitude
#         )
#         dropoff_loc, _ = Location.objects.get_or_create(
#             name=dropoff_loc_name, latitude=dropoff_coords.latitude, longitude=dropoff_coords.longitude
#         )
#
#         # Create Trip instance
#         trip = Trip.objects.create(
#             current_location=current_loc,
#             pickup_location=pickup_loc,
#             dropoff_location=dropoff_loc,
#             current_cycle_used=current_cycle_used
#         )
#
#         # Get routes from OSRM
#         current_latlon = (current_coords.latitude, current_coords.longitude)
#         pickup_latlon = (pickup_coords.latitude, pickup_coords.longitude)
#         dropoff_latlon = (dropoff_coords.latitude, dropoff_coords.longitude)
#
#         route1 = self.get_osrm_route(current_latlon, pickup_latlon)
#         route2 = self.get_osrm_route(pickup_latlon, dropoff_latlon)
#         if not route1 or not route2:
#             trip.delete()
#             return Response({"error": "Unable to calculate route"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#         # Combine routes
#         full_geometry = route1['geometry'] + route2['geometry'][1:]
#         total_distance = route1['distance'] + route2['distance']
#         total_duration = route1['duration'] + route2['duration']
#
#         # Create Route instance
#         route = Route.objects.create(
#             trip=trip,
#             geometry=full_geometry,
#             distance=total_distance,
#             duration=total_duration
#         )
#
#         # Simulate trip and save stops/logs
#         logs, stops = self.simulate_trip(
#             current_latlon, pickup_latlon, dropoff_latlon,
#             route1, route2, current_cycle_used
#         )
#         if not logs:
#             route.delete()
#             trip.delete()
#             return Response({"error": "Trip exceeds 70-hour HOS limit"}, status=status.HTTP_400_BAD_REQUEST)
#
#         # Save stops
#         for stop_data in stops:
#             stop_loc = Location.objects.create(
#                 name=f"{stop_data['type']} stop", latitude=stop_data['location'][0], longitude=stop_data['location'][1]
#             )
#             Stop.objects.create(
#                 route=route,
#                 location=stop_loc,
#                 type=stop_data['type'],
#                 duration=stop_data['duration']
#             )
#
#         # Save logs (simplified to day 1)
#         for log in logs[0]['segments']:
#             Log.objects.create(
#                 trip=trip,
#                 day=1,
#                 start_time=log['start'],
#                 end_time=log['end'],
#                 status=log['status']
#             )
#
#         # Serialize and return response
#         route_serializer = RouteSerializer(route)
#         return Response(route_serializer.data, status=status.HTTP_201_CREATED)
#
#     def get_osrm_route(self, start, end):
#         url = f"http://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}?overview=full&steps=true"
#         try:
#             response = requests.get(url, timeout=10)
#             if response.status_code != 200:
#                 return None
#             data = response.json()
#             if data['code'] != 'Ok':
#                 return None
#             route = data['routes'][0]
#             geometry = polyline.decode(route['geometry'])
#             return {
#                 'geometry': geometry,
#                 'distance': route['distance'] / 1609.34,  # meters to miles
#                 'duration': route['duration'] / 3600      # seconds to hours
#             }
#         except requests.RequestException:
#             return None
#
#     def interpolate_position(self, geometry, fraction):
#         if fraction <= 0:
#             return geometry[0]
#         if fraction >= 1:
#             return geometry[-1]
#         n = len(geometry)
#         for i in range(n - 1):
#             start = i / (n - 1)
#             end = (i + 1) / (n - 1)
#             if start <= fraction < end:
#                 segment_fraction = (fraction - start) / (end - start)
#                 lat = geometry[i][0] + segment_fraction * (geometry[i + 1][0] - geometry[i][0])
#                 lon = geometry[i][1] + segment_fraction * (geometry[i + 1][1] - geometry[i][1])
#                 return (lat, lon)
#         return geometry[-1]
#
#     def simulate_trip(self, current, pickup, dropoff, route1, route2, current_cycle_used):
#         current_time = 0
#         driving_time = 0
#         on_duty_time = 0
#         total_on_duty = current_cycle_used
#         distance_since_fuel = 0
#         current_position = current
#         logs = []
#         stops = []
#
#         def format_time(hours):
#             h = int(hours % 24)
#             m = int((hours % 1) * 60)
#             return f"{h:02d}:{m:02d}"
#
#         def add_log(start_time, end_time, status):
#             logs.append({
#                 "start": format_time(start_time),
#                 "end": format_time(end_time),
#                 "status": status
#             })
#
#         # Leg 1: Current to Pickup
#         duration = route1['duration']
#         distance = route1['distance']
#         speed = distance / duration if duration > 0 else 0
#         time_driven = 0
#         while time_driven < duration:
#             time_until_rest = min(11 - driving_time, 14 - on_duty_time)
#             time_until_fuel = (1000 - distance_since_fuel) / speed if speed > 0 else float('inf')
#             time_to_drive = min(duration - time_driven, time_until_rest, time_until_fuel)
#
#             if time_to_drive <= 0:
#                 add_log(current_time, current_time + 10, "off-duty")
#                 stops.append({"location": current_position, "type": "rest", "duration": 10})
#                 current_time += 10
#                 driving_time = 0
#                 on_duty_time = 0
#                 continue
#
#             distance_driven = time_to_drive * speed
#             fraction = (time_driven + time_to_drive) / duration
#             current_position = self.interpolate_position(route1['geometry'], fraction)
#             add_log(current_time, current_time + time_to_drive, "driving")
#             current_time += time_to_drive
#             driving_time += time_to_drive
#             on_duty_time += time_to_drive
#             total_on_duty += time_to_drive
#             distance_since_fuel += distance_driven
#             time_driven += time_to_drive
#
#             if total_on_duty > 70:
#                 return [], []
#
#             if time_to_drive == time_until_rest:
#                 add_log(current_time, current_time + 10, "off-duty")
#                 stops.append({"location": current_position, "type": "rest", "duration": 10})
#                 current_time += 10
#                 driving_time = 0
#                 on_duty_time = 0
#             elif time_to_drive == time_until_fuel:
#                 add_log(current_time, current_time + 0.5, "on-duty not driving")
#                 stops.append({"location": current_position, "type": "fueling", "duration": 0.5})
#                 current_time += 0.5
#                 on_duty_time += 0.5
#                 total_on_duty += 0.5
#                 distance_since_fuel = 0
#
#         # Pickup
#         add_log(current_time, current_time + 1, "on-duty not driving")
#         stops.append({"location": pickup, "type": "pickup", "duration": 1})
#         current_time += 1
#         on_duty_time += 1
#         total_on_duty += 1
#         if total_on_duty > 70:
#             return [], []
#
#         # Leg 2: Pickup to Dropoff
#         duration = route2['duration']
#         distance = route2['distance']
#         speed = distance / duration if duration > 0 else 0
#         time_driven = 0
#         current_position = pickup
#         while time_driven < duration:
#             time_until_rest = min(11 - driving_time, 14 - on_duty_time)
#             time_until_fuel = (1000 - distance_since_fuel) / speed if speed > 0 else float('inf')
#             time_to_drive = min(duration - time_driven, time_until_rest, time_until_fuel)
#
#             if time_to_drive <= 0:
#                 add_log(current_time, current_time + 10, "off-duty")
#                 stops.append({"location": current_position, "type": "rest", "duration": 10})
#                 current_time += 10
#                 driving_time = 0
#                 on_duty_time = 0
#                 continue
#
#             distance_driven = time_to_drive * speed
#             fraction = (time_driven + time_to_drive) / duration
#             current_position = self.interpolate_position(route2['geometry'], fraction)
#             add_log(current_time, current_time + time_to_drive, "driving")
#             current_time += time_to_drive
#             driving_time += time_to_drive
#             on_duty_time += time_to_drive
#             total_on_duty += time_to_drive
#             distance_since_fuel += distance_driven
#             time_driven += time_to_drive
#
#             if total_on_duty > 70:
#                 return [], []
#
#             if time_to_drive == time_until_rest:
#                 add_log(current_time, current_time + 10, "off-duty")
#                 stops.append({"location": current_position, "type": "rest", "duration": 10})
#                 current_time += 10
#                 driving_time = 0
#                 on_duty_time = 0
#             elif time_to_drive == time_until_fuel:
#                 add_log(current_time, current_time + 0.5, "on-duty not driving")
#                 stops.append({"location": current_position, "type": "fueling", "duration": 0.5})
#                 current_time += 0.5
#                 on_duty_time += 0.5
#                 total_on_duty += 0.5
#                 distance_since_fuel = 0
#
#         # Dropoff
#         add_log(current_time, current_time + 1, "on-duty not driving")
#         stops.append({"location": dropoff, "type": "dropoff", "duration": 1})
#         total_on_duty += 1
#         if total_on_duty > 70:
#             return [], []
#
#         return [{"day": 1, "segments": logs}], stops


from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from .serializers import TripInputSerializer, TripSerializer, RouteSerializer
from .models import Location, Trip, Route, Stop, Log
from geopy.geocoders import Nominatim
import requests
import polyline
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class TripPlanViewSet(viewsets.ModelViewSet):
    queryset = Trip.objects.all()  # Define the queryset for the Trip model
    serializer_class = TripSerializer  # Default serializer for Trip model

    # Swagger schema for the custom create endpoint
    @swagger_auto_schema(
        request_body=TripInputSerializer,
        responses={
            201: RouteSerializer,
            400: "Bad Request",
            500: "Internal Server Error"
        },
        operation_description="Create a trip plan with current location, pickup, dropoff, and cycle used."
    )
    def create(self, request, *args, **kwargs):
        # Validate input using TripInputSerializer
        serializer = TripInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        current_loc_name = data['current_location']
        pickup_loc_name = data['pickup_location']
        dropoff_loc_name = data['dropoff_location']
        current_cycle_used = data['current_cycle_used']

        # Geocode locations
        geolocator = Nominatim(user_agent="trip_planner")
        try:
            current_coords = geolocator.geocode(current_loc_name)
            pickup_coords = geolocator.geocode(pickup_loc_name)
            dropoff_coords = geolocator.geocode(dropoff_loc_name)
            if not all([current_coords, pickup_coords, dropoff_coords]):
                return Response({"error": "Invalid location"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"error": "Geocoding failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Save locations to database
        current_loc, _ = Location.objects.get_or_create(
            name=current_loc_name, latitude=current_coords.latitude, longitude=current_coords.longitude
        )
        pickup_loc, _ = Location.objects.get_or_create(
            name=pickup_loc_name, latitude=pickup_coords.latitude, longitude=pickup_coords.longitude
        )
        dropoff_loc, _ = Location.objects.get_or_create(
            name=dropoff_loc_name, latitude=dropoff_coords.latitude, longitude=dropoff_coords.longitude
        )

        # Create Trip instance
        trip = Trip.objects.create(
            current_location=current_loc,
            pickup_location=pickup_loc,
            dropoff_location=dropoff_loc,
            current_cycle_used=current_cycle_used
        )

        # Get routes from OSRM
        current_latlon = (current_coords.latitude, current_coords.longitude)
        pickup_latlon = (pickup_coords.latitude, pickup_coords.longitude)
        dropoff_latlon = (dropoff_coords.latitude, dropoff_coords.longitude)

        route1 = self.get_osrm_route(current_latlon, pickup_latlon)
        route2 = self.get_osrm_route(pickup_latlon, dropoff_latlon)
        if not route1 or not route2:
            trip.delete()
            return Response({"error": "Unable to calculate route"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Combine routes
        full_geometry = route1['geometry'] + route2['geometry'][1:]
        total_distance = route1['distance'] + route2['distance']
        total_duration = route1['duration'] + route2['duration']

        # Create Route instance
        route = Route.objects.create(
            trip=trip,
            geometry=full_geometry,
            distance=total_distance,
            duration=total_duration
        )

        # Simulate trip and save stops/logs
        logs, stops = self.simulate_trip(
            current_latlon, pickup_latlon, dropoff_latlon,
            route1, route2, current_cycle_used
        )
        if not logs:
            route.delete()
            trip.delete()
            return Response({"error": "Trip exceeds 70-hour HOS limit"}, status=status.HTTP_400_BAD_REQUEST)

        # Save stops
        for stop_data in stops:
            stop_loc = Location.objects.create(
                name=f"{stop_data['type']} stop", latitude=stop_data['location'][0], longitude=stop_data['location'][1]
            )
            Stop.objects.create(
                route=route,
                location=stop_loc,
                type=stop_data['type'],
                duration=stop_data['duration']
            )

        # Save logs (simplified to day 1)
        for log in logs[0]['segments']:
            Log.objects.create(
                trip=trip,
                day=1,
                start_time=log['start'],
                end_time=log['end'],
                status=log['status']
            )

        # Serialize and return response
        route_serializer = RouteSerializer(route)
        return Response(route_serializer.data, status=status.HTTP_201_CREATED)

    def get_osrm_route(self, start, end):
        url = f"http://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}?overview=full&steps=true"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                return None
            data = response.json()
            if data['code'] != 'Ok':
                return None
            route = data['routes'][0]
            geometry = polyline.decode(route['geometry'])
            return {
                'geometry': geometry,
                'distance': route['distance'] / 1609.34,  # meters to miles
                'duration': route['duration'] / 3600      # seconds to hours
            }
        except requests.RequestException:
            return None

    def interpolate_position(self, geometry, fraction):
        if fraction <= 0:
            return geometry[0]
        if fraction >= 1:
            return geometry[-1]
        n = len(geometry)
        for i in range(n - 1):
            start = i / (n - 1)
            end = (i + 1) / (n - 1)
            if start <= fraction < end:
                segment_fraction = (fraction - start) / (end - start)
                lat = geometry[i][0] + segment_fraction * (geometry[i + 1][0] - geometry[i][0])
                lon = geometry[i][1] + segment_fraction * (geometry[i + 1][1] - geometry[i][1])
                return (lat, lon)
        return geometry[-1]

    def simulate_trip(self, current, pickup, dropoff, route1, route2, current_cycle_used):
        current_time = 0
        driving_time = 0
        on_duty_time = 0
        total_on_duty = current_cycle_used
        distance_since_fuel = 0
        current_position = current
        logs = []
        stops = []

        def format_time(hours):
            h = int(hours % 24)
            m = int((hours % 1) * 60)
            return f"{h:02d}:{m:02d}"

        def add_log(start_time, end_time, status):
            logs.append({
                "start": format_time(start_time),
                "end": format_time(end_time),
                "status": status
            })

        # Leg 1: Current to Pickup
        duration = route1['duration']
        distance = route1['distance']
        speed = distance / duration if duration > 0 else 0
        time_driven = 0
        while time_driven < duration:
            time_until_rest = min(11 - driving_time, 14 - on_duty_time)
            time_until_fuel = (1000 - distance_since_fuel) / speed if speed > 0 else float('inf')
            time_to_drive = min(duration - time_driven, time_until_rest, time_until_fuel)

            if time_to_drive <= 0:
                add_log(current_time, current_time + 10, "off-duty")
                stops.append({"location": current_position, "type": "rest", "duration": 10})
                current_time += 10
                driving_time = 0
                on_duty_time = 0
                continue

            distance_driven = time_to_drive * speed
            fraction = (time_driven + time_to_drive) / duration
            current_position = self.interpolate_position(route1['geometry'], fraction)
            add_log(current_time, current_time + time_to_drive, "driving")
            current_time += time_to_drive
            driving_time += time_to_drive
            on_duty_time += time_to_drive
            total_on_duty += time_to_drive
            distance_since_fuel += distance_driven
            time_driven += time_to_drive

            if total_on_duty > 70:
                return [], []

            if time_to_drive == time_until_rest:
                add_log(current_time, current_time + 10, "off-duty")
                stops.append({"location": current_position, "type": "rest", "duration": 10})
                current_time += 10
                driving_time = 0
                on_duty_time = 0
            elif time_to_drive == time_until_fuel:
                add_log(current_time, current_time + 0.5, "on-duty not driving")
                stops.append({"location": current_position, "type": "fueling", "duration": 0.5})
                current_time += 0.5
                on_duty_time += 0.5
                total_on_duty += 0.5
                distance_since_fuel = 0

        # Pickup
        add_log(current_time, current_time + 1, "on-duty not driving")
        stops.append({"location": pickup, "type": "pickup", "duration": 1})
        current_time += 1
        on_duty_time += 1
        total_on_duty += 1
        if total_on_duty > 70:
            return [], []

        # Leg 2: Pickup to Dropoff
        duration = route2['duration']
        distance = route2['distance']
        speed = distance / duration if duration > 0 else 0
        time_driven = 0
        current_position = pickup
        while time_driven < duration:
            time_until_rest = min(11 - driving_time, 14 - on_duty_time)
            time_until_fuel = (1000 - distance_since_fuel) / speed if speed > 0 else float('inf')
            time_to_drive = min(duration - time_driven, time_until_rest, time_until_fuel)

            if time_to_drive <= 0:
                add_log(current_time, current_time + 10, "off-duty")
                stops.append({"location": current_position, "type": "rest", "duration": 10})
                current_time += 10
                driving_time = 0
                on_duty_time = 0
                continue

            distance_driven = time_to_drive * speed
            fraction = (time_driven + time_to_drive) / duration
            current_position = self.interpolate_position(route2['geometry'], fraction)
            add_log(current_time, current_time + time_to_drive, "driving")
            current_time += time_to_drive
            driving_time += time_to_drive
            on_duty_time += time_to_drive
            total_on_duty += time_to_drive
            distance_since_fuel += distance_driven
            time_driven += time_to_drive

            if total_on_duty > 70:
                return [], []

            if time_to_drive == time_until_rest:
                add_log(current_time, current_time + 10, "off-duty")
                stops.append({"location": current_position, "type": "rest", "duration": 10})
                current_time += 10
                driving_time = 0
                on_duty_time = 0
            elif time_to_drive == time_until_fuel:
                add_log(current_time, current_time + 0.5, "on-duty not driving")
                stops.append({"location": current_position, "type": "fueling", "duration": 0.5})
                current_time += 0.5
                on_duty_time += 0.5
                total_on_duty += 0.5
                distance_since_fuel = 0

        # Dropoff
        add_log(current_time, current_time + 1, "on-duty not driving")
        stops.append({"location": dropoff, "type": "dropoff", "duration": 1})
        total_on_duty += 1
        if total_on_duty > 70:
            return [], []

        return [{"day": 1, "segments": logs}], stops