from django.db import models

class Location(models.Model):
    name = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return self.name

class Trip(models.Model):
    current_location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='trips_from')
    pickup_location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='trips_pickup')
    dropoff_location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='trips_dropoff')
    current_cycle_used = models.FloatField()

    def __str__(self):
        return f"Trip from {self.current_location} to {self.dropoff_location} via {self.pickup_location}"

class Route(models.Model):
    trip = models.OneToOneField(Trip, on_delete=models.CASCADE)
    geometry = models.JSONField()  # Stores route polyline as JSON
    distance = models.FloatField()  # In miles
    duration = models.FloatField()  # In hours

    def __str__(self):
        return f"Route for {self.trip}"


class Stop(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='stops')
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    type = models.CharField(
        max_length=20,
        choices=[
            ('rest', 'Rest'),
            ('fueling', 'Fueling'),
            ('pickup', 'Pickup'),
            ('dropoff', 'Dropoff')
        ]
    )
    duration = models.FloatField()  # In hours

    def __str__(self):
        return f"{self.type} at {self.location}"

class Log(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='logs')
    day = models.IntegerField()  # Day number of the trip
    start_time = models.CharField(max_length=5)  # e.g., "08:00"
    end_time = models.CharField(max_length=5)    # e.g., "12:00"
    status = models.CharField(
        max_length=20,
        choices=[
            ('driving', 'Driving'),
            ('on-duty not driving', 'On-duty not driving'),
            ('off-duty', 'Off-duty')
        ]
    )

    def __str__(self):
        return f"Log for {self.trip} on day {self.day}: {self.status}"