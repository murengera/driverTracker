from rest_framework import serializers
from .models import Location, Trip, Route, Stop, Log

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name', 'latitude', 'longitude']

class TripSerializer(serializers.ModelSerializer):
    current_location = LocationSerializer()
    pickup_location = LocationSerializer()
    dropoff_location = LocationSerializer()

    class Meta:
        model = Trip
        fields = ['id', 'current_location', 'pickup_location', 'dropoff_location', 'current_cycle_used']

class StopSerializer(serializers.ModelSerializer):
    location = LocationSerializer()

    class Meta:
        model = Stop
        fields = ['id', 'location', 'type', 'duration']

class RouteSerializer(serializers.ModelSerializer):
    trip = TripSerializer()
    stops = StopSerializer(many=True)

    class Meta:
        model = Route
        fields = ['id', 'trip', 'geometry', 'distance', 'duration', 'stops']


class LogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Log
        fields = ['id', 'trip', 'day', 'start_time', 'end_time', 'status']


class TripInputSerializer(serializers.Serializer):
    current_location = serializers.CharField(max_length=255)
    pickup_location = serializers.CharField(max_length=255)
    dropoff_location = serializers.CharField(max_length=255)
    current_cycle_used = serializers.FloatField(min_value=0, max_value=70)