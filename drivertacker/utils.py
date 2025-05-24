import requests
import polyline

def get_osrm_route(start_coords, end_coords):
    """
    Fetches route data from OSRM.
    start_coords: tuple (latitude, longitude)
    end_coords: tuple (latitude, longitude)
    """
    url = f"http://router.project-osrm.org/route/v1/driving/{start_coords[1]},{start_coords[0]};{end_coords[1]},{end_coords[0]}?overview=full&steps=true"
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
    except (KeyError, IndexError, ValueError): # Handle potential JSON issues
        return None

def interpolate_position(geometry, fraction):
    """
    Interpolates a position along a route geometry.
    geometry: list of (lat, lon) tuples representing the route.
    fraction: float between 0 and 1 representing the proportion of the route covered.
    """
    if not geometry: # Handle empty geometry
        return None
    if fraction <= 0:
        return geometry[0]
    if fraction >= 1:
        return geometry[-1]
    
    # Calculate total distance of the polyline (simplified for this context)
    # For accurate interpolation, one would sum segment lengths.
    # Here, we use index-based interpolation for simplicity.
    n_points = len(geometry)
    if n_points == 1:
        return geometry[0]

    target_index_float = fraction * (n_points - 1)
    prev_index = int(target_index_float)
    next_index = prev_index + 1

    if next_index >= n_points:
        return geometry[-1]

    segment_fraction = target_index_float - prev_index

    lat_prev, lon_prev = geometry[prev_index]
    lat_next, lon_next = geometry[next_index]

    lat = lat_prev + segment_fraction * (lat_next - lat_prev)
    lon = lon_prev + segment_fraction * (lon_next - lon_prev)
    
    return (lat, lon)


def simulate_trip(current_coords, pickup_coords, dropoff_coords, route1_data, route2_data, current_cycle_used_hours):
    """
    Simulates a trip including driving segments, rest stops, and HOS calculations.
    Returns a tuple: (logs_by_day, stops_list)
    logs_by_day: list of dictionaries, where each dictionary represents a day's logs.
    stops_list: list of dictionaries, where each dictionary represents a stop.
    Returns ([], []) if HOS limits are exceeded.
    """
    current_time_hours = 0  # Relative time in hours from trip start
    driving_hours_current_stint = 0
    on_duty_hours_current_stint = 0 # Includes driving and other on-duty tasks
    total_on_duty_cycle_hours = current_cycle_used_hours # 70-hour cycle

    # Max driving/on-duty hours before mandatory rest
    MAX_DRIVING_BEFORE_REST = 11
    MAX_ON_DUTY_BEFORE_REST = 14
    MANDATORY_REST_HOURS = 10
    HOS_CYCLE_LIMIT = 70

    # Fueling constants
    MAX_DISTANCE_BEFORE_FUEL_MILES = 1000 # Simplified: assume fixed range
    FUELING_STOP_DURATION_HOURS = 0.5

    # Pickup/Dropoff constants
    PICKUP_DURATION_HOURS = 1
    DROPOFF_DURATION_HOURS = 1
    
    logs_output = []
    stops_output = []

    # Helper to format time from hours to HH:MM
    def format_time_str(hours):
        total_minutes = int(hours * 60)
        h = (total_minutes // 60) % 24 # Handle multi-day trips for time display
        m = total_minutes % 60
        return f"{h:02d}:{m:02d}"

    # Helper to add log entries
    def add_log_entry(start_hours, end_hours, status):
        logs_output.append({
            "start": format_time_str(start_hours),
            "end": format_time_str(end_hours),
            "status": status
        })

    # Helper to add stop entries
    def add_stop_entry(location_coords, stop_type, duration_hours):
        stops_output.append({
            "location": location_coords, # (lat, lon) tuple
            "type": stop_type,
            "duration": duration_hours
        })

    # --- Simulate trip ---
    # Leg 1: Current location to Pickup location
    leg1_duration_hours = route1_data['duration']
    leg1_distance_miles = route1_data['distance']
    leg1_geometry = route1_data['geometry']
    
    # Driving Leg 1
    distance_driven_on_leg1 = 0
    time_spent_on_leg1_driving = 0

    while time_spent_on_leg1_driving < leg1_duration_hours:
        # Check HOS before starting/continuing this driving segment
        if driving_hours_current_stint >= MAX_DRIVING_BEFORE_REST or \
           on_duty_hours_current_stint >= MAX_ON_DUTY_BEFORE_REST or \
           total_on_duty_cycle_hours >= HOS_CYCLE_LIMIT:
            
            # Mandatory rest
            rest_start_time = current_time_hours
            add_log_entry(rest_start_time, rest_start_time + MANDATORY_REST_HOURS, "off-duty")
            current_pos_on_leg1 = interpolate_position(leg1_geometry, distance_driven_on_leg1 / leg1_distance_miles if leg1_distance_miles > 0 else 0)
            add_stop_entry(current_pos_on_leg1, "rest", MANDATORY_REST_HOURS)
            
            current_time_hours += MANDATORY_REST_HOURS
            driving_hours_current_stint = 0
            on_duty_hours_current_stint = 0
            # total_on_duty_cycle_hours doesn't reset until a 34-hour restart, not modeled here simply.
            # For 70h cycle, off-duty time counts. Assume it doesn't reset cycle here for simplicity.
            if total_on_duty_cycle_hours >= HOS_CYCLE_LIMIT : # If rest didn't solve cycle limit
                 return [], [] # Trip invalid

        # Determine max drivable time in this segment
        # Time until next HOS break
        time_to_max_driving = MAX_DRIVING_BEFORE_REST - driving_hours_current_stint
        time_to_max_on_duty = MAX_ON_DUTY_BEFORE_REST - on_duty_hours_current_stint
        time_to_cycle_limit = HOS_CYCLE_LIMIT - total_on_duty_cycle_hours
        
        # Remaining time for this leg
        remaining_leg_time = leg1_duration_hours - time_spent_on_leg1_driving
        
        # Time to drive now is minimum of these
        drive_duration_this_segment = min(remaining_leg_time, time_to_max_driving, time_to_max_on_duty, time_to_cycle_limit)

        if drive_duration_this_segment <= 0: # Should not happen if HOS is checked before
            # This implies an issue or mandatory stop is immediately needed.
            # For robustness, force a rest if this edge case is hit.
            rest_start_time = current_time_hours
            add_log_entry(rest_start_time, rest_start_time + MANDATORY_REST_HOURS, "off-duty")
            current_pos_on_leg1 = interpolate_position(leg1_geometry, distance_driven_on_leg1 / leg1_distance_miles if leg1_distance_miles > 0 else 0)
            add_stop_entry(current_pos_on_leg1, "rest", MANDATORY_REST_HOURS)
            current_time_hours += MANDATORY_REST_HOURS
            driving_hours_current_stint = 0
            on_duty_hours_current_stint = 0
            if total_on_duty_cycle_hours + MANDATORY_REST_HOURS > HOS_CYCLE_LIMIT and drive_duration_this_segment == time_to_cycle_limit : # check if cycle limit was the reason
                 return [], [] # Trip invalid
            continue


        # Log driving segment
        segment_start_time = current_time_hours
        add_log_entry(segment_start_time, segment_start_time + drive_duration_this_segment, "driving")

        # Update times
        current_time_hours += drive_duration_this_segment
        driving_hours_current_stint += drive_duration_this_segment
        on_duty_hours_current_stint += drive_duration_this_segment
        total_on_duty_cycle_hours += drive_duration_this_segment
        time_spent_on_leg1_driving += drive_duration_this_segment
        distance_driven_on_leg1 += drive_duration_this_segment * (leg1_distance_miles / leg1_duration_hours if leg1_duration_hours > 0 else 0)


    # Arrived at Pickup Location
    # Pickup Stop
    pickup_start_time = current_time_hours
    add_log_entry(pickup_start_time, pickup_start_time + PICKUP_DURATION_HOURS, "on-duty not driving")
    add_stop_entry(pickup_coords, "pickup", PICKUP_DURATION_HOURS)
    current_time_hours += PICKUP_DURATION_HOURS
    on_duty_hours_current_stint += PICKUP_DURATION_HOURS # Pickup is on-duty
    total_on_duty_cycle_hours += PICKUP_DURATION_HOURS

    if total_on_duty_cycle_hours > HOS_CYCLE_LIMIT:
        return [], []


    # Leg 2: Pickup location to Dropoff location
    leg2_duration_hours = route2_data['duration']
    leg2_distance_miles = route2_data['distance']
    leg2_geometry = route2_data['geometry']

    distance_driven_on_leg2 = 0
    time_spent_on_leg2_driving = 0
    
    while time_spent_on_leg2_driving < leg2_duration_hours:
        if driving_hours_current_stint >= MAX_DRIVING_BEFORE_REST or \
           on_duty_hours_current_stint >= MAX_ON_DUTY_BEFORE_REST or \
           total_on_duty_cycle_hours >= HOS_CYCLE_LIMIT:
            
            rest_start_time = current_time_hours
            add_log_entry(rest_start_time, rest_start_time + MANDATORY_REST_HOURS, "off-duty")
            current_pos_on_leg2 = interpolate_position(leg2_geometry, distance_driven_on_leg2 / leg2_distance_miles if leg2_distance_miles > 0 else 0)
            add_stop_entry(current_pos_on_leg2, "rest", MANDATORY_REST_HOURS)

            current_time_hours += MANDATORY_REST_HOURS
            driving_hours_current_stint = 0
            on_duty_hours_current_stint = 0
            if total_on_duty_cycle_hours >= HOS_CYCLE_LIMIT:
                 return [], []

        time_to_max_driving = MAX_DRIVING_BEFORE_REST - driving_hours_current_stint
        time_to_max_on_duty = MAX_ON_DUTY_BEFORE_REST - on_duty_hours_current_stint
        time_to_cycle_limit = HOS_CYCLE_LIMIT - total_on_duty_cycle_hours
        remaining_leg_time = leg2_duration_hours - time_spent_on_leg2_driving
        drive_duration_this_segment = min(remaining_leg_time, time_to_max_driving, time_to_max_on_duty, time_to_cycle_limit)

        if drive_duration_this_segment <= 0:
            rest_start_time = current_time_hours
            add_log_entry(rest_start_time, rest_start_time + MANDATORY_REST_HOURS, "off-duty")
            current_pos_on_leg2 = interpolate_position(leg2_geometry, distance_driven_on_leg2 / leg2_distance_miles if leg2_distance_miles > 0 else 0)
            add_stop_entry(current_pos_on_leg2, "rest", MANDATORY_REST_HOURS)
            current_time_hours += MANDATORY_REST_HOURS
            driving_hours_current_stint = 0
            on_duty_hours_current_stint = 0
            if total_on_duty_cycle_hours + MANDATORY_REST_HOURS > HOS_CYCLE_LIMIT and drive_duration_this_segment == time_to_cycle_limit :
                 return [], []
            continue

        segment_start_time = current_time_hours
        add_log_entry(segment_start_time, segment_start_time + drive_duration_this_segment, "driving")

        current_time_hours += drive_duration_this_segment
        driving_hours_current_stint += drive_duration_this_segment
        on_duty_hours_current_stint += drive_duration_this_segment
        total_on_duty_cycle_hours += drive_duration_this_segment
        time_spent_on_leg2_driving += drive_duration_this_segment
        distance_driven_on_leg2 += drive_duration_this_segment * (leg2_distance_miles / leg2_duration_hours if leg2_duration_hours > 0 else 0)
    
    # Arrived at Dropoff Location
    dropoff_start_time = current_time_hours
    add_log_entry(dropoff_start_time, dropoff_start_time + DROPOFF_DURATION_HOURS, "on-duty not driving")
    add_stop_entry(dropoff_coords, "dropoff", DROPOFF_DURATION_HOURS)
    current_time_hours += DROPOFF_DURATION_HOURS
    total_on_duty_cycle_hours += DROPOFF_DURATION_HOURS

    if total_on_duty_cycle_hours > HOS_CYCLE_LIMIT:
        return [], []

    # For simplicity, all logs are for Day 1. A more complex simulation would track days.
    return [{"day": 1, "segments": logs_output}], stops_output
