from datetime import datetime

# ---- SAPE CONFIGURATION ----
WEIGHTS = {
    "car": 1.0,
    "bike": 0.5,
    "truck": 2.5,
    "density": 5
}

BUS_WEIGHT_RUSH = 4.0
BUS_WEIGHT_NORMAL = 2.0

DENSITY_SCORE = {
    "Low": 1,
    "Medium": 2,
    "High": 3
}

MIN_GREEN_TIME = 20
MAX_GREEN_TIME = 60
EMERGENCY_GREEN_TIME = 60

RUSH_HOUR_WINDOWS = [(8, 10), (17, 20)]  # (start_hour, end_hour), 24hr format


def is_rush_hour(current_time=None):
    """Check if current time falls in a rush hour window."""
    if current_time is None:
        current_time = datetime.now()
    hour = current_time.hour
    for start, end in RUSH_HOUR_WINDOWS:
        if start <= hour < end:
            return True
    return False


def calculate_tps(road_data, rush_hour):
    """
    road_data = {
        "cars": int, "bikes": int, "bus": int, "truck": int,
        "congestion": "Low"/"Medium"/"High"
    }
    """
    bus_weight = BUS_WEIGHT_RUSH if rush_hour else BUS_WEIGHT_NORMAL
    density_score = DENSITY_SCORE[road_data["congestion"]]

    tps = (
        road_data["cars"] * WEIGHTS["car"] +
        road_data["bikes"] * WEIGHTS["bike"] +
        road_data["bus"] * bus_weight +
        road_data["truck"] * WEIGHTS["truck"] +
        density_score * WEIGHTS["density"]
    )
    return round(tps, 2)


def calculate_green_times(all_roads_tps):
    """
    all_roads_tps = {"North": 95, "East": 80, "South": 45, "West": 30}
    Returns green time per road.
    """
    total_tps = sum(all_roads_tps.values())
    green_times = {}

    for road, tps in all_roads_tps.items():
        if total_tps == 0:
            green_times[road] = MIN_GREEN_TIME
        else:
            green_times[road] = round(
                MIN_GREEN_TIME + (tps / total_tps) * (MAX_GREEN_TIME - MIN_GREEN_TIME), 2
            )
    return green_times


def run_sape(roads_data, rush_hour=None):
    """
    Main SAPE entry point.
    roads_data = {
        "North": {"cars":.., "bikes":.., "bus":.., "truck":.., "ambulance": bool, "congestion": "Low"/"Medium"/"High"},
        "East": {...}, "South": {...}, "West": {...}
    }
    """
    if rush_hour is None:
        rush_hour = is_rush_hour()

    # ---- STAGE 1: Emergency Override ----
    for road, data in roads_data.items():
        if data.get("ambulance", False):
            print(f"\n🚨 EMERGENCY OVERRIDE: Ambulance detected on {road}!")
            green_times = {}
            for r in roads_data:
                green_times[r] = EMERGENCY_GREEN_TIME if r == road else MIN_GREEN_TIME
            return {
                "emergency_override": True,
                "override_road": road,
                "green_times": green_times,
                "tps": None
            }

    # ---- STAGE 2: Weighted TPS ----
    tps_results = {}
    for road, data in roads_data.items():
        tps_results[road] = calculate_tps(data, rush_hour)

    green_times = calculate_green_times(tps_results)

    return {
        "emergency_override": False,
        "override_road": None,
        "green_times": green_times,
        "tps": tps_results
    }

def calculate_congestion(vehicle_data):
    """
    Estimate congestion level from raw vehicle counts.
    vehicle_data = {"cars": int, "bikes": int, "bus": int, "truck": int}
    """
    total_vehicles = (
        vehicle_data["cars"] +
        vehicle_data["bikes"] +
        vehicle_data["bus"] +
        vehicle_data["truck"]
    )

    if total_vehicles <= 5:
        return "Low"
    elif total_vehicles <= 12:
        return "Medium"
    else:
        return "High"

# ---- TEST SCENARIO ----
if __name__ == "__main__":
    sample_data = {
        "North": {"cars": 30, "bikes": 12, "bus": 2, "truck": 1, "ambulance": False, "congestion": "High"},
        "East":  {"cars": 20, "bikes": 8,  "bus": 1, "truck": 2, "ambulance": False, "congestion": "Medium"},
        "South": {"cars": 10, "bikes": 5,  "bus": 0, "truck": 1, "ambulance": False, "congestion": "Low"},
        "West":  {"cars": 5,  "bikes": 3,  "bus": 0, "truck": 0, "ambulance": False, "congestion": "Low"},
    }

    result = run_sape(sample_data, rush_hour=True)
    print("\n--- SAPE Result ---")
    print(f"Emergency Override: {result['emergency_override']}")
    print(f"TPS per road: {result['tps']}")
    print(f"Green Times: {result['green_times']}")