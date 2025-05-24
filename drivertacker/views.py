from rest_framework import viewsets # Added missing import
from rest_framework.response import Response
from rest_framework import status
from .serializers import TripInputSerializer, TripSerializer, RouteSerializer
from .models import Location, Trip, Route, Stop, Log
from geopy.geocoders import Nominatim
# import requests # Moved to utils
# import polyline # Moved to utils
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from . import utils # Import the new utils module

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

        route1 = utils.get_osrm_route(current_latlon, pickup_latlon) # Call util function
        route2 = utils.get_osrm_route(pickup_latlon, dropoff_latlon) # Call util function
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
        logs, stops = utils.simulate_trip( # Call util function
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

    # get_osrm_route, interpolate_position, and simulate_trip are now in utils.py