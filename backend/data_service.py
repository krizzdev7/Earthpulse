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
