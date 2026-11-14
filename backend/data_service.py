"""
Data service module for fetching monthly climate data from the NASA POWER API.
"""

import calendar
import json
import math
from typing import Any, Dict, List, Optional
import requests

NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/monthly/point"
DEFAULT_TIMEOUT = 60

# Location registry for the get_climate_data() compatibility bridge
# Maps location_id -> (latitude, longitude, display_name)
LOCATION_REGISTRY: Dict[str, Dict[str, Any]] = {
    "kerala": {"latitude": 10.8505, "longitude": 76.2711, "name": "Kerala, India"},
    "thiruvananthapuram": {"latitude": 8.5241, "longitude": 76.9366, "name": "Thiruvananthapuram, Kerala"},
    "kochi": {"latitude": 9.9312, "longitude": 76.2673, "name": "Kochi, Kerala"},
    "kozhikode": {"latitude": 11.2588, "longitude": 75.7804, "name": "Kozhikode, Kerala"},
    "thrissur": {"latitude": 10.5276, "longitude": 76.2144, "name": "Thrissur, Kerala"},
    "kannur": {"latitude": 11.8745, "longitude": 75.3704, "name": "Kannur, Kerala"},
   "kerala_statewide": {
    "latitude": 10.8505,
    "longitude": 76.2711,
    "name": "Kerala Statewide, India"
},
}



def is_missing_value(val: Any) -> bool:
    """Check if a measurement value represents a missing or invalid data point."""
    if val is None:
        return True
    if isinstance(val, (int, float)):
        return val <= -999 or math.isnan(val)
    return False


def calculate_monthly_rainfall(precip_rate: Any, year: int, month: int) -> Optional[float]:
    """Calculate total monthly precipitation in mm from the daily rate.

    Args:
        precip_rate: Monthly mean daily precipitation rate in mm/day.
        year: Calendar year.
        month: Calendar month (1-12).

    Returns:
        Calculated monthly rainfall in mm, or None if the daily rate is missing.
    """
    if is_missing_value(precip_rate):
        return None
    days_in_month = calendar.monthrange(year, month)[1]
    return round(precip_rate * days_in_month, 2)


def fetch_climate_data(
    latitude: float,
    longitude: float,
    start_year: int = 2001,
    end_year: int = 2025,
) -> List[Dict[str, Any]]:
    """Fetch monthly temperature and precipitation data from NASA POWER API.

    Args:
        latitude: Latitude coordinate for the location.
        longitude: Longitude coordinate for the location.
        start_year: Beginning year of the query range (default: 2001).
        end_year: Ending year of the query range (default: 2025).

    Returns:
        List of structured monthly records containing 'month', 'temperature' (in °C),
        'precipitation' (mean daily rate in mm/day), and 'precipitation_mm'
        (calculated monthly rainfall in mm). Annual summary entries (ending in '13')
        are excluded.

    Raises:
        RuntimeError: If the HTTP request fails or the API response is invalid/unexpected.
    """
    params = {
        "parameters": "T2M,PRECTOTCORR",
        "community": "AG",
        "longitude": longitude,
        "latitude": latitude,
        "start": start_year,
        "end": end_year,
        "format": "JSON",
    }

    try:
        response = requests.get(
            NASA_POWER_URL,
            params=params,
            timeout=DEFAULT_TIMEOUT,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as error:
        raise RuntimeError(f"NASA API request failed: {error}") from error

    try:
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Response payload is not a valid JSON object")

        properties = payload.get("properties")
        if not isinstance(properties, dict):
            raise KeyError("Response missing 'properties'")

        data = properties.get("parameter")
        if not isinstance(data, dict):
            raise KeyError("Response missing 'parameter'")

        if "T2M" not in data or "PRECTOTCORR" not in data:
            raise KeyError("Missing required parameters ('T2M', 'PRECTOTCORR') in API response")

        temperatures = data["T2M"]
        rainfall = data["PRECTOTCORR"]

        if not isinstance(temperatures, dict) or not isinstance(rainfall, dict):
            raise TypeError("Expected parameter data to be dictionaries of monthly values")

        records: List[Dict[str, Any]] = []
        for month_key in temperatures:
            month_str = str(month_key).strip()

            # Exclude annual summary entries ending in '13' or labeled 'ANN'
            if month_str.endswith("13") or month_str.upper() == "ANN":
                continue

            # Parse year and month to determine exact calendar days
            try:
                if len(month_str) == 6 and month_str.isdigit():
                    year = int(month_str[:4])
                    month_num = int(month_str[4:6])
                elif "-" in month_str:
                    parts = month_str.split("-")
                    year = int(parts[0])
                    month_num = int(parts[1])
                else:
                    continue
            except (ValueError, IndexError):
                continue

            # Verify month is within valid calendar range 1-12
            if not (1 <= month_num <= 12):
                continue

            precip_rate = rainfall.get(month_key)
            precipitation_mm = calculate_monthly_rainfall(precip_rate, year, month_num)

            records.append({
                "month": month_key,
                "temperature": temperatures[month_key],
                "precipitation": precip_rate,
                "precipitation_mm": precipitation_mm,
            })

        return records
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Unexpected NASA response: {error}") from error


def get_climate_data(
    location_id: str,
    start_year: int = 2001,
    end_year: int = 2025,
) -> "pd.DataFrame":
    """Compatibility bridge: Fetch climate data by location ID.

    This bridge function accepts a named location identifier (e.g. 'kerala')
    and resolves it to lat/lon coordinates automatically, then calls
    fetch_climate_data() and returns a structured pandas DataFrame.

    Args:
        location_id: Location identifier key from LOCATION_REGISTRY
                     (e.g. 'kerala', 'kochi', 'kozhikode').
        start_year: Beginning year of the query range.
        end_year: Ending year of the query range.

    Returns:
        pandas DataFrame with columns:
            ['year', 'month', 'date', 'T2M', 'PRECTOTCORR', 'location']
        where T2M is monthly mean temperature (°C) and PRECTOTCORR is
        monthly total precipitation (mm).

    Raises:
        ValueError: If location_id is not found in LOCATION_REGISTRY.
        RuntimeError: If the NASA POWER API request fails.
    """
    import pandas as pd
    import numpy as np

    location_id_lower = location_id.strip().lower()
    if location_id_lower not in LOCATION_REGISTRY:
        available = ", ".join(sorted(LOCATION_REGISTRY.keys()))
        raise ValueError(
            f"Unknown location_id '{location_id}'. "
            f"Available locations: {available}"
        )

    loc = LOCATION_REGISTRY[location_id_lower]
    records = fetch_climate_data(
        latitude=loc["latitude"],
        longitude=loc["longitude"],
        start_year=start_year,
        end_year=end_year,
    )

    rows = []
    for r in records:
        month_str = str(r.get("month", "")).strip()
        try:
            if len(month_str) == 6 and month_str.isdigit():
                yr = int(month_str[:4])
                mo = int(month_str[4:6])
            elif "-" in month_str:
                parts = month_str.split("-")
                yr = int(parts[0])
                mo = int(parts[1])
            else:
                continue
        except (ValueError, IndexError):
            continue

        temp = r.get("temperature")
        t2m = float(temp) if temp is not None and not (isinstance(temp, float) and (math.isnan(temp) or temp <= -999)) else np.nan

        precip_mm = r.get("precipitation_mm")
        prectot = float(precip_mm) if precip_mm is not None and precip_mm >= 0 else np.nan

        rows.append({
            "year": yr,
            "month": mo,
            "date": pd.Timestamp(f"{yr}-{mo:02d}-01"),
            "T2M": t2m,
            "PRECTOTCORR": prectot,
            "location": loc["name"],
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("date").reset_index(drop=True)
    return df
