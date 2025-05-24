from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock
from .models import Location, Trip, Route, Stop, Log

class LocationModelTests(TestCase):
    def test_location_creation(self):
        location = Location.objects.create(latitude=10.0, longitude=20.0, name="Test Location")
        self.assertIsInstance(location, Location)
        self.assertEqual(location.latitude, 10.0)
        self.assertEqual(location.longitude, 20.0)
        self.assertEqual(location.name, "Test Location")
        self.assertEqual(str(location), "Test Location")

class TripModelTests(TestCase):
    def setUp(self):
        self.driver = User.objects.create_user(username="testdriver", password="password")
        self.start_location = Location.objects.create(latitude=10.0, longitude=20.0, name="Start Location")
        self.end_location = Location.objects.create(latitude=30.0, longitude=40.0, name="End Location")

    def test_trip_creation(self):
        trip = Trip.objects.create(
            current_location=self.start_location,
            pickup_location=self.start_location,
            dropoff_location=self.end_location,
            current_cycle_used=0.0
        )
        self.assertIsInstance(trip, Trip)
        self.assertEqual(trip.current_location, self.start_location)
        self.assertEqual(trip.pickup_location, self.start_location)
        self.assertEqual(trip.dropoff_location, self.end_location)
        self.assertEqual(trip.current_cycle_used, 0.0)
        self.assertEqual(str(trip), f"Trip from {self.start_location} to {self.end_location} via {self.start_location}")

class RouteModelTests(TestCase):
    def setUp(self):
        self.driver = User.objects.create_user(username="testdriver", password="password")
        self.start_location = Location.objects.create(latitude=10.0, longitude=20.0, name="Start Location")
        self.end_location = Location.objects.create(latitude=30.0, longitude=40.0, name="End Location")
        self.trip = Trip.objects.create(
            current_location=self.start_location,
            pickup_location=self.start_location,
            dropoff_location=self.end_location,
            current_cycle_used=0.0
        )
        self.location1 = Location.objects.create(latitude=11.0, longitude=21.0, name="Route Location 1")
        self.location2 = Location.objects.create(latitude=12.0, longitude=22.0, name="Route Location 2")

    def test_route_creation(self):
        route = Route.objects.create(trip=self.trip, geometry={"test": "data"}, distance=10.0, duration=1.0)
        self.assertIsInstance(route, Route)
        self.assertEqual(route.trip, self.trip)
        self.assertEqual(route.geometry, {"test": "data"})
        self.assertEqual(route.distance, 10.0)
        self.assertEqual(route.duration, 1.0)
        self.assertEqual(str(route), f"Route for {self.trip}")

class StopModelTests(TestCase):
    def setUp(self):
        self.driver = User.objects.create_user(username="testdriver", password="password")
        self.start_location = Location.objects.create(latitude=10.0, longitude=20.0, name="Start Location")
        self.end_location = Location.objects.create(latitude=30.0, longitude=40.0, name="End Location")
        self.trip = Trip.objects.create(
            current_location=self.start_location,
            pickup_location=self.start_location,
            dropoff_location=self.end_location,
            current_cycle_used=0.0
        )
        self.route = Route.objects.create(trip=self.trip, geometry={"test": "data"}, distance=10.0, duration=1.0)
        self.stop_location = Location.objects.create(latitude=15.0, longitude=25.0, name="Stop Location")

    def test_stop_creation(self):
        stop = Stop.objects.create(
            route=self.route,
            location=self.stop_location,
            type="pickup",
            duration=0.5
        )
        self.assertIsInstance(stop, Stop)
        self.assertEqual(stop.route, self.route)
        self.assertEqual(stop.location, self.stop_location)
        self.assertEqual(stop.type, "pickup")
        self.assertEqual(stop.duration, 0.5)
        self.assertEqual(str(stop), f"{stop.type} at {self.stop_location}")

class LogModelTests(TestCase):
    def setUp(self):
        self.driver = User.objects.create_user(username="testdriver", password="password")
        self.start_location = Location.objects.create(latitude=10.0, longitude=20.0, name="Start Location")
        self.end_location = Location.objects.create(latitude=30.0, longitude=40.0, name="End Location")
        self.trip = Trip.objects.create(
            current_location=self.start_location,
            pickup_location=self.start_location,
            dropoff_location=self.end_location,
            current_cycle_used=0.0
        )
        self.log_location = Location.objects.create(latitude=18.0, longitude=28.0, name="Log Location")

    def test_log_creation(self):
        log = Log.objects.create(
            trip=self.trip,
            day=1,
            start_time="08:00",
            end_time="12:00",
            status="driving"
        )
        self.assertIsInstance(log, Log)
        self.assertEqual(log.trip, self.trip)
        self.assertEqual(log.day, 1)
        self.assertEqual(log.start_time, "08:00")
        self.assertEqual(log.end_time, "12:00")
        self.assertEqual(log.status, "driving")
        self.assertEqual(str(log), f"Log for {self.trip} on day {log.day}: {log.status}")


class TripPlanViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", password="password")
        self.client.force_authenticate(user=self.user)

    @patch('drivertacker.views.Nominatim') # Nominatim is used in views.py directly
    @patch('drivertacker.utils.requests.get') # requests.get is now used in utils.py
    def test_create_trip_plan_valid_data(self, mock_requests_get, mock_nominatim):
        # Mock Nominatim
        mock_geolocator = mock_nominatim.return_value
        mock_location_current = MagicMock(latitude=34.0522, longitude=-118.2437) # LA
        mock_location_pickup = MagicMock(latitude=36.1699, longitude=-115.1398) # Las Vegas
        mock_location_dropoff = MagicMock(latitude=32.7157, longitude=-117.1611) # San Diego
        mock_geolocator.geocode.side_effect = [
            mock_location_current, mock_location_pickup, mock_location_dropoff
        ]

        # Mock OSRM response (requests.get)
        mock_osrm_response = MagicMock()
        mock_osrm_response.status_code = 200
        mock_osrm_response.json.return_value = {
            "routes": [{
                "geometry": "gfo}EtohhU", # Using a simple valid polyline
                "distance": 300 * 1609.34,  # 300 miles in meters
                "duration": 5 * 3600  # 5 hours in seconds
            }],
            "code": "Ok",
            "waypoints": [
                {"location": [-118.2437, 34.0522]}, # LA
                {"location": [-115.1398, 36.1699]}, # Las Vegas
                {"location": [-117.1611, 32.7157]}  # San Diego
            ]
        }
        mock_requests_get.return_value = mock_osrm_response

        data = {
            "current_location": "Los Angeles, CA",
            "pickup_location": "Las Vegas, NV",
            "dropoff_location": "San Diego, CA",
            "current_cycle_used": 10.0
        }

        response = self.client.post('/trip-plan/', data, format='json') # Removed /api prefix

        self.assertEqual(response.status_code, 201) # Check for 201 CREATED
        self.assertTrue(Trip.objects.exists())
        self.assertTrue(Route.objects.exists())
        self.assertTrue(Stop.objects.exists()) # At least pickup and dropoff stops
        self.assertTrue(Log.objects.exists())

        # Validate response data structure (RouteSerializer output)
        self.assertIn("id", response.data) # Route ID
        self.assertIn("trip", response.data)
        self.assertIn("id", response.data["trip"]) # Trip ID
        self.assertEqual(response.data["trip"]["current_location"]["name"], "Los Angeles, CA")
        self.assertIn("geometry", response.data)
        self.assertIn("stops", response.data)
        self.assertNotIn("logs", response.data) # Logs are not part of RouteSerializer

        # Check if locations were created
        self.assertTrue(Location.objects.filter(name="Los Angeles, CA").exists())
        self.assertTrue(Location.objects.filter(name="Las Vegas, NV").exists())
        self.assertTrue(Location.objects.filter(name="San Diego, CA").exists())

        # Check trip details from database
        trip = Trip.objects.first()
        self.assertEqual(trip.current_location.name, "Los Angeles, CA")
        self.assertEqual(trip.pickup_location.name, "Las Vegas, NV")
        self.assertEqual(trip.dropoff_location.name, "San Diego, CA")
        self.assertEqual(trip.current_cycle_used, 10.0)

        # Check route details from database
        route = Route.objects.first()
        self.assertEqual(route.trip, trip)
        self.assertEqual(route.distance, 600.0) # Miles (300 * 2)
        self.assertEqual(route.duration, 10.0) # Hours (5 * 2)
        self.assertEqual(route.geometry,  [[36.45556, -116.86667]]) # JSONField stores list of lists

        # Check stops from response (RouteSerializer includes stops)
        self.assertEqual(len(response.data["stops"]), 2)
        # Further checks on stop types and locations from response can be added

        # Check logs (basic check, assuming simulate_trip creates some logs in DB)
        logs = Log.objects.filter(trip=trip)
        self.assertTrue(logs.exists())

    def test_create_trip_plan_missing_fields(self):
        data = {
            "current_location": "Los Angeles, CA",
            # pickup_location is missing
            "dropoff_location": "San Diego, CA",
            "current_cycle_used": 10.0
        }
        response = self.client.post('/trip-plan/', data, format='json') # Removed /api prefix
        self.assertEqual(response.status_code, 400)
        self.assertIn("pickup_location", response.data) # Check for error message on the field
        self.assertFalse(Trip.objects.exists()) # No objects should be created

    @patch('drivertacker.views.Nominatim')
    def test_create_trip_plan_invalid_location_name(self, mock_nominatim):
        # Mock Nominatim to return None for an invalid location
        mock_geolocator = mock_nominatim.return_value
        mock_geolocator.geocode.return_value = None

        data = {
            "current_location": "Invalid Location Name That Does Not Exist",
            "pickup_location": "Las Vegas, NV",
            "dropoff_location": "San Diego, CA",
            "current_cycle_used": 10.0
        }
        response = self.client.post('/trip-plan/', data, format='json') # Removed /api prefix
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.data) # Check for generic error message
        self.assertEqual(response.data["error"], "Invalid location")
        self.assertFalse(Trip.objects.exists())

    def test_create_trip_plan_cycle_used_out_of_range(self):
        data = {
            "current_location": "Los Angeles, CA",
            "pickup_location": "Las Vegas, NV",
            "dropoff_location": "San Diego, CA",
            "current_cycle_used": 80.0 # Exceeds 70
        }
        response = self.client.post('/trip-plan/', data, format='json') # Removed /api prefix
        self.assertEqual(response.status_code, 400)
        self.assertIn("current_cycle_used", response.data)
        self.assertFalse(Trip.objects.exists())

    @patch('drivertacker.views.Nominatim')
    def test_create_trip_plan_geocoding_exception(self, mock_nominatim):
        # Mock Nominatim to raise an exception
        mock_geolocator = mock_nominatim.return_value
        mock_geolocator.geocode.side_effect = Exception("Geocoding service unavailable")

        data = {
            "current_location": "Los Angeles, CA",
            "pickup_location": "Las Vegas, NV",
            "dropoff_location": "San Diego, CA",
            "current_cycle_used": 10.0
        }
        response = self.client.post('/trip-plan/', data, format='json') # Removed /api prefix
        self.assertEqual(response.status_code, 500) # Or 400 depending on how it's handled
        self.assertIn("error", response.data) # Check for a generic error message
        self.assertFalse(Trip.objects.exists())

    @patch('drivertacker.views.Nominatim')
    @patch('drivertacker.utils.requests.get') # requests.get is now used in utils.py
    def test_create_trip_plan_osrm_failure_status(self, mock_requests_get, mock_nominatim):
        # Mock Nominatim for successful geocoding
        mock_geolocator = mock_nominatim.return_value
        mock_location = MagicMock(latitude=34.0522, longitude=-118.2437)
        mock_geolocator.geocode.return_value = mock_location

        # Mock OSRM response (requests.get) to return a non-200 status
        mock_osrm_response = MagicMock()
        mock_osrm_response.status_code = 503 # Service Unavailable
        mock_requests_get.return_value = mock_osrm_response

        data = {
            "current_location": "Los Angeles, CA",
            "pickup_location": "Las Vegas, NV",
            "dropoff_location": "San Diego, CA",
            "current_cycle_used": 10.0
        }
        response = self.client.post('/trip-plan/', data, format='json') # Removed /api prefix
        self.assertEqual(response.status_code, 500) # Or 400
        self.assertIn("error", response.data)
        self.assertFalse(Trip.objects.exists())
        self.assertFalse(Route.objects.exists())

    @patch('drivertacker.views.Nominatim')
    @patch('drivertacker.utils.requests.get') # requests.get is now used in utils.py
    @patch('drivertacker.utils.simulate_trip') # simulate_trip is now in utils.py
    def test_create_trip_plan_hos_limit_exceeded(self, mock_simulate_trip, mock_requests_get, mock_nominatim):
        # Mock Nominatim
        mock_geolocator = mock_nominatim.return_value
        mock_location = MagicMock(latitude=34.0522, longitude=-118.2437)
        mock_geolocator.geocode.return_value = mock_location

        # Mock OSRM response
        mock_osrm_response = MagicMock()
        mock_osrm_response.status_code = 200
        mock_osrm_response.json.return_value = {
            "routes": [{"geometry": "gfo}EtohhU", "distance": 5000 * 1609.34, "duration": 80 * 3600}], # 80 hours
            "code": "Ok",
             "waypoints": [ {"location": [-118.2437, 34.0522]}, {"location": [-115.1398, 36.1699]}, {"location": [-117.1611, 32.7157]}]
        }
        mock_requests_get.return_value = mock_osrm_response

        # Mock simulate_trip to return empty lists (HOS limit exceeded)
        mock_simulate_trip.return_value = ([], [])

        data = {
            "current_location": "Los Angeles, CA",
            "pickup_location": "Very Far Away", # To trigger long duration
            "dropoff_location": "Even Farther Away",
            "current_cycle_used": 0.0
        }

        response = self.client.post('/trip-plan/', data, format='json') # Removed /api prefix

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"], "Trip exceeds 70-hour HOS limit")
        self.assertFalse(Trip.objects.exists()) # Trip and Route should be deleted
        self.assertFalse(Route.objects.exists()) # Trip and Route should be deleted
        self.assertFalse(Stop.objects.exists()) # No stops should be created
        self.assertFalse(Log.objects.exists())  # No logs should be created

    def test_list_trip_plans(self):
        # Create some locations
        loc1 = Location.objects.create(name="Location A", latitude=1.0, longitude=1.0)
        loc2 = Location.objects.create(name="Location B", latitude=2.0, longitude=2.0)
        loc3 = Location.objects.create(name="Location C", latitude=3.0, longitude=3.0)

        # Create some trips
        Trip.objects.create(current_location=loc1, pickup_location=loc2, dropoff_location=loc3, current_cycle_used=5.0)
        Trip.objects.create(current_location=loc2, pickup_location=loc1, dropoff_location=loc3, current_cycle_used=10.0)

        response = self.client.get('/trip-plan/', format='json') # Removed /api prefix
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertIn("current_location", response.data[0])
        self.assertIn("pickup_location", response.data[0])
        self.assertIn("dropoff_location", response.data[0])

    def test_retrieve_trip_plan(self):
        # Create a location
        loc1 = Location.objects.create(name="Location X", latitude=1.0, longitude=1.0)
        loc2 = Location.objects.create(name="Location Y", latitude=2.0, longitude=2.0)
        loc3 = Location.objects.create(name="Location Z", latitude=3.0, longitude=3.0)

        # Create a trip
        trip = Trip.objects.create(current_location=loc1, pickup_location=loc2, dropoff_location=loc3, current_cycle_used=15.0)

        # Create a route for the trip
        route = Route.objects.create(trip=trip, geometry="test_geom", distance=100.0, duration=2.0)

        # Create stops for the route
        stop1 = Stop.objects.create(route=route, location=loc2, type="pickup", duration=0.25)
        stop2 = Stop.objects.create(route=route, location=loc3, type="dropoff", duration=0.25)

        # Create logs for the trip
        Log.objects.create(trip=trip, day=1, start_time="08:00", end_time="10:00", status="driving")

        response = self.client.get(f'/trip-plan/{trip.id}/', format='json') # Removed /api prefix
        self.assertEqual(response.status_code, 200)

        # Validate main trip details (TripSerializer output)
        self.assertEqual(response.data["id"], trip.id)
        self.assertEqual(response.data["current_location"]["id"], loc1.id) # Expecting nested Location object
        self.assertEqual(response.data["current_location"]["name"], loc1.name)
        self.assertEqual(response.data["pickup_location"]["id"], loc2.id)
        self.assertEqual(response.data["pickup_location"]["name"], loc2.name)
        self.assertEqual(response.data["dropoff_location"]["id"], loc3.id)
        self.assertEqual(response.data["dropoff_location"]["name"], loc3.name)
        self.assertEqual(response.data["current_cycle_used"], 15.0)

        # Route, Stops, and Logs are not part of the default TripSerializer for retrieve,
        # unless TripSerializer is customized or a custom retrieve method is used.
        # The 'create' action has a custom response structure.
        # For 'retrieve', we expect only the Trip model fields.
        self.assertNotIn("route", response.data)
        self.assertNotIn("logs", response.data)
