"""
Trend analysis module for EARTHPULSE climate data.

Provides statistical trend analysis using Theil-Sen slope estimation and
the Kendall rank correlation test, along with annual aggregation and
monthly climatology calculations.
"""

import calendar
import os
from typing import Any, Dict, List, Optional, Sequence, Tuple

# Restrict thread creation for OpenBLAS on Windows sandboxes
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import numpy as np
import scipy.stats as stats

CAUSATION_DISCLAIMER = (
    "Statistical trend analysis identifies historical monotonic tendencies over the "
    "observed period but does not prove or attribute climate change causation. "
    "Attribution requires physical climate modeling and greenhouse gas forcing analysis."
)

MIN_OBSERVATIONS_FOR_TREND = 3


def is_valid_measurement(val: Any, allow_negative: bool = True) -> bool:
    """Check if a measurement value is valid (non-null, non-missing, numeric)."""
    if val is None:
        return False
    if isinstance(val, (int, float, np.number)):
        if np.isnan(val):
            return False
        if val <= -999:
            return False
        if not allow_negative and val < 0:
            return False
        return True
    return False


def parse_record_date(month_val: Any) -> Optional[Tuple[int, int]]:
    """Parse year and month from record 'month' field."""
    month_str = str(month_val).strip()
    if month_str.endswith("13") or month_str.upper() == "ANN":
        return None

    try:
        if len(month_str) == 6 and month_str.isdigit():
            year = int(month_str[:4])
            month_num = int(month_str[4:6])
        elif "-" in month_str:
            parts = month_str.split("-")
            year = int(parts[0])
            month_num = int(parts[1])
        else:
            return None
    except (ValueError, IndexError):
        return None

    if 1 <= month_num <= 12:
        return year, month_num
    return None


def aggregate_annual_climate(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate monthly records into annual mean temperature and total rainfall."""
    year_temps: Dict[int, Dict[int, float]] = {}
    year_rain: Dict[int, Dict[int, float]] = {}

    for r in records:
        parsed = parse_record_date(r.get("month"))
        if parsed is None:
            continue
        year, month_num = parsed

        if year not in year_temps:
            year_temps[year] = {}
            year_rain[year] = {}

        temp = r.get("temperature")
        if is_valid_measurement(temp, allow_negative=True):
            year_temps[year][month_num] = float(temp)

        precip = r.get("precipitation_mm")
        if is_valid_measurement(precip, allow_negative=False):
            year_rain[year][month_num] = float(precip)

    all_years = sorted(set(year_temps.keys()) | set(year_rain.keys()))

    temp_years: List[int] = []
    temp_values: List[float] = []
    rain_years: List[int] = []
    rain_values: List[float] = []
    annual_records: List[Dict[str, Any]] = []
    incomplete_years: Dict[int, Dict[str, Any]] = {}

    for yr in all_years:
        temps_for_yr = year_temps.get(yr, {})
        rain_for_yr = year_rain.get(yr, {})

        has_12_temps = len(temps_for_yr) == 12
        has_12_rain = len(rain_for_yr) == 12

        mean_temp: Optional[float] = None
        total_rain: Optional[float] = None

        if has_12_temps:
            mean_temp = round(float(np.mean(list(temps_for_yr.values()))), 2)
            temp_years.append(yr)
            temp_values.append(mean_temp)

        if has_12_rain:
            total_rain = round(float(np.sum(list(rain_for_yr.values()))), 2)
            rain_years.append(yr)
            rain_values.append(total_rain)

        if not (has_12_temps and has_12_rain):
            incomplete_years[yr] = {
                "valid_temperature_months": len(temps_for_yr),
                "valid_rainfall_months": len(rain_for_yr),
                "temperature_complete": has_12_temps,
                "rainfall_complete": has_12_rain,
            }

        if has_12_temps or has_12_rain:
            annual_records.append({
                "year": yr,
                "mean_temperature": mean_temp,
                "annual_rainfall": total_rain,
            })

    return {
        "annual_records": annual_records,
        "temperature_series": {"years": temp_years, "values": temp_values},
        "rainfall_series": {"years": rain_years, "values": rain_values},
        "incomplete_years": incomplete_years,
    }


def calculate_trend(
    years: Sequence[int],
    values: Sequence[float],
    metric_name: str = "temperature",
    alpha: float = 0.05,
) -> Dict[str, Any]:
    """Calculate long-term trend using Theil-Sen slope and Kendall rank correlation."""
    unit_yr = "°C/year" if metric_name == "temperature" else "mm/year"
    unit_dec = "°C/decade" if metric_name == "temperature" else "mm/decade"

    valid_pairs = [
        (int(y), float(v))
        for y, v in zip(years, values)
        if is_valid_measurement(v, allow_negative=(metric_name == "temperature"))
    ]

    n_obs = len(valid_pairs)

    base_result: Dict[str, Any] = {
        "metric": metric_name,
        "unit_per_year": unit_yr,
        "unit_per_decade": unit_dec,
        "trend_direction": "no detected trend",
        "slope_per_year": None,
        "slope_per_decade": None,
        "kendall_tau": None,
        "p_value": None,
        "observations": n_obs,
        "years": [p[0] for p in valid_pairs],
        "is_statistically_significant": False,
        "disclaimer": CAUSATION_DISCLAIMER,
    }

    if n_obs < MIN_OBSERVATIONS_FOR_TREND:
        return base_result

    x = np.array([p[0] for p in valid_pairs], dtype=np.float64)
    y = np.array([p[1] for p in valid_pairs], dtype=np.float64)

    if np.all(np.isclose(y, y[0])):
        base_result.update({
            "trend_direction": "no detected trend",
            "slope_per_year": 0.0,
            "slope_per_decade": 0.0,
            "kendall_tau": 0.0,
            "p_value": 1.0,
            "is_statistically_significant": False,
        })
        return base_result

    try:
        theil_res = stats.theilslopes(y, x)
        slope_per_year = float(theil_res.slope)
        slope_per_decade = slope_per_year * 10.0
    except Exception:
        slope_per_year = 0.0
        slope_per_decade = 0.0

    try:
        tau_res = stats.kendalltau(x, y)
        tau = float(tau_res.statistic) if not np.isnan(tau_res.statistic) else 0.0
        p_val = float(tau_res.pvalue) if not np.isnan(tau_res.pvalue) else 1.0
    except Exception:
        tau = 0.0
        p_val = 1.0

    is_significant = bool(p_val < alpha)
    if is_significant:
        if slope_per_year > 0 and tau > 0:
            direction = "increasing"
        elif slope_per_year < 0 and tau < 0:
            direction = "decreasing"
        else:
            direction = "no detected trend"
    else:
        direction = "no detected trend"

    base_result.update({
        "trend_direction": direction,
        "slope_per_year": round(slope_per_year, 4),
        "slope_per_decade": round(slope_per_decade, 4),
        "kendall_tau": round(tau, 4),
        "p_value": round(p_val, 6),
        "is_statistically_significant": is_significant,
    })

    return base_result


def calculate_monthly_climatology(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Calculate multi-year monthly climatology across available years."""
    month_temps: Dict[int, List[float]] = {m: [] for m in range(1, 13)}
    month_rains: Dict[int, List[float]] = {m: [] for m in range(1, 13)}

    for r in records:
        parsed = parse_record_date(r.get("month"))
        if parsed is None:
            continue
        _, month_num = parsed

        temp = r.get("temperature")
        if is_valid_measurement(temp, allow_negative=True):
            month_temps[month_num].append(float(temp))

        precip_mm = r.get("precipitation_mm")
        if is_valid_measurement(precip_mm, allow_negative=False):
            month_rains[month_num].append(float(precip_mm))

    climatology: List[Dict[str, Any]] = []
    for m in range(1, 13):
        temps = month_temps[m]
        rains = month_rains[m]
        mean_temp = round(float(np.mean(temps)), 2) if temps else None
        mean_rain = round(float(np.mean(rains)), 2) if rains else None

        climatology.append({
            "month": m,
            "month_name": calendar.month_name[m],
            "mean_temperature": mean_temp,
            "mean_precipitation_mm": mean_rain,
            "temperature_observations": len(temps),
            "precipitation_observations": len(rains),
        })

    return climatology


def analyze_climate_trends(
    records: List[Dict[str, Any]],
    location_name: str = "Location",
    alpha: float = 0.05,
) -> Dict[str, Any]:
    """Perform complete climate trend analysis and climatology from monthly records."""
    aggregation = aggregate_annual_climate(records)

    temp_series = aggregation["temperature_series"]
    rain_series = aggregation["rainfall_series"]

    temp_trend = calculate_trend(
        years=temp_series["years"],
        values=temp_series["values"],
        metric_name="temperature",
        alpha=alpha,
    )

    rain_trend = calculate_trend(
        years=rain_series["years"],
        values=rain_series["values"],
        metric_name="rainfall",
        alpha=alpha,
    )

    climatology = calculate_monthly_climatology(records)

    return {
        "location": location_name,
        "annual_aggregation": aggregation,
        "temperature_trend": temp_trend,
        "rainfall_trend": rain_trend,
        "monthly_climatology": climatology,
        "disclaimer": CAUSATION_DISCLAIMER,
    }
