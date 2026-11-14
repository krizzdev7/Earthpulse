"""Data Adapter module for EARTHPULSE.
Acts as a resilient integration bridge between the Streamlit frontend and backend services
(backend/data_service.py and backend/trend_analysis.py).

INTEGRATION CONTRACT:
Backend compatibility bridge (Option A, currently being implemented on data-analysis):
    - backend.data_service.get_climate_data(location_id: str, start_year: int, end_year: int) -> pd.DataFrame
      Expected DataFrame columns: ['year', 'month', 'date', 'T2M', 'PRECTOTCORR']
      (or ['year', 'month', 'temperature', 'precipitation_mm'])

Existing backend function:
    - backend.data_service.fetch_climate_data(latitude: float, longitude: float, start_year: int, end_year: int) -> List[Dict]

Trend Analysis:
    - backend.trend_analysis.analyze_climate_trends(records: List[Dict], location_name: str) -> Dict

If backend bridge is not yet available in the local branch or NASA POWER API encounters network/timeout errors,
this adapter cleanly falls back to synthetic demonstration data explicitly labeled as PROTOTYPE.
"""

from dataclasses import dataclass
import importlib
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import streamlit as st


@dataclass
class ClimateDataResult:
    """Encapsulates the dataset, statistical trend analysis, and provenance metadata."""
    df: pd.DataFrame
    is_demo: bool
    source_label: str
    status_message: str
    baseline_stats: Dict[str, float]
    trend_results: Optional[Dict[str, Any]] = None
    raw_records: Optional[List[Dict[str, Any]]] = None
    bridge_used: str = "none"  # "get_climate_data", "fetch_climate_data", or "none"


def _parse_record_date(month_val: Any) -> Optional[Tuple[int, int]]:
    """Parses year and month from record 'month' field (e.g. '202101', 202101, '2021-01')."""
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


def _normalize_climate_dataframe(df_in: pd.DataFrame) -> pd.DataFrame:
    """Normalizes an incoming backend DataFrame to the standard frontend schema:
    Columns: ['year', 'month', 'date', 'T2M', 'PRECTOTCORR']

    - Preserves missing values (<= -999, None, NaN) as np.nan (NEVER converts to 0.0).
    - Preserves temperature in Celsius.
    - Preserves precipitation in monthly millimetres.
    - Excludes '13' or 'ANN' summary entries.
    """
    df = df_in.copy()
    col_map = {}

    # Identify temperature column
    for col in df.columns:
        c_lower = str(col).lower()
        if c_lower in ("t2m", "temperature", "temp", "temp_c", "air_temp"):
            col_map[col] = "T2M"
            break

    # Identify precipitation column
    for col in df.columns:
        c_lower = str(col).lower()
        if c_lower in ("prectotcorr", "precipitation_mm", "precipitation", "precip", "rainfall_mm", "rainfall"):
            col_map[col] = "PRECTOTCORR"
            break

    df = df.rename(columns=col_map)

    # Ensure year and month columns exist
    if "year" not in df.columns or "month" not in df.columns:
        if "date" in df.columns:
            date_col = pd.to_datetime(df["date"], errors="coerce")
            df["year"] = date_col.dt.year
            df["month"] = date_col.dt.month
        elif "month" in df.columns:
            # Month might be 'YYYYMM' format
            parsed_dates = [_parse_record_date(m) for m in df["month"]]
            df["year"] = [p[0] if p else np.nan for p in parsed_dates]
            df["month"] = [p[1] if p else np.nan for p in parsed_dates]

    # Filter out annual summaries (month == 13)
    if "month" in df.columns:
        df = df[df["month"] != 13]
        df = df[df["month"].between(1, 12, inclusive="both")]

    # Clean missing values for T2M
    if "T2M" in df.columns:
        df["T2M"] = pd.to_numeric(df["T2M"], errors="coerce")
        df.loc[df["T2M"] <= -999, "T2M"] = np.nan
    else:
        df["T2M"] = np.nan

    # Clean missing values for PRECTOTCORR (must be non-negative)
    if "PRECTOTCORR" in df.columns:
        df["PRECTOTCORR"] = pd.to_numeric(df["PRECTOTCORR"], errors="coerce")
        df.loc[df["PRECTOTCORR"] < 0, "PRECTOTCORR"] = np.nan
    else:
        df["PRECTOTCORR"] = np.nan

    # Ensure date column
    if "date" not in df.columns or df["date"].isnull().any():
        df["date"] = pd.to_datetime(
            df["year"].astype(int).astype(str) + "-" + df["month"].astype(int).astype(str).str.zfill(2) + "-01",
            errors="coerce"
        )

    required_cols = ["year", "month", "date", "T2M", "PRECTOTCORR"]
    return df[required_cols].sort_values("date").reset_index(drop=True)


def _convert_backend_records_to_df(records: List[Dict[str, Any]]) -> pd.DataFrame:
    """Converts backend monthly records into the standard frontend DataFrame schema.

    - Preserves missing values (<= -999, None, NaN) as np.nan.
    - Maps precipitation_mm (total monthly depth in mm) to PRECTOTCORR.
    - Maps temperature (°C) to T2M.
    """
    rows = []
    for r in records:
        parsed = _parse_record_date(r.get("month"))
        if parsed is None:
            continue
        year, month_num = parsed

        # Temperature handling (Celsius)
        temp = r.get("temperature")
        if temp is None or (isinstance(temp, (int, float, np.number)) and (temp <= -999 or np.isnan(temp))):
            t2m_val = np.nan
        else:
            t2m_val = round(float(temp), 2)

        # Monthly rainfall total handling (mm)
        precip_mm = r.get("precipitation_mm")
        if precip_mm is None or (isinstance(precip_mm, (int, float, np.number)) and (precip_mm < 0 or np.isnan(precip_mm))):
            precip_val = np.nan
        else:
            precip_val = round(float(precip_mm), 2)

        rows.append({
            "year": year,
            "month": month_num,
            "date": pd.Timestamp(f"{year}-{month_num:02d}-01"),
            "T2M": t2m_val,
            "PRECTOTCORR": precip_val,
        })

    if not rows:
        return pd.DataFrame(columns=["year", "month", "date", "T2M", "PRECTOTCORR"])

    df = pd.DataFrame(rows)
    return df.sort_values("date").reset_index(drop=True)


@st.cache_data(ttl=3600, show_spinner="Querying NASA POWER climate observations...")
def _cached_fetch_backend_data(
    location_id: str,
    latitude: float,
    longitude: float,
    start_year: int,
    end_year: int
) -> Dict[str, Any]:
    """Cached bridge caller supporting Option A (get_climate_data) and fallback (fetch_climate_data)."""
    data_service = importlib.import_module("backend.data_service")

    # 1. Option A: Check for get_climate_data(location_id, start_year, end_year) -> pd.DataFrame
    get_fn = getattr(data_service, "get_climate_data", None)
    if callable(get_fn):
        try:
            res_df = get_fn(location_id=location_id, start_year=start_year, end_year=end_year)
            if isinstance(res_df, pd.DataFrame) and not res_df.empty:
                return {"type": "dataframe", "data": res_df, "bridge": "get_climate_data"}
        except TypeError:
            # Fallback if get_climate_data has alternate argument names
            res_df = get_fn(location_id, start_year, end_year)
            if isinstance(res_df, pd.DataFrame) and not res_df.empty:
                return {"type": "dataframe", "data": res_df, "bridge": "get_climate_data"}

    # 2. Existing function: fetch_climate_data(latitude, longitude, start_year, end_year) -> List[Dict]
    fetch_fn = getattr(data_service, "fetch_climate_data", None)
    if callable(fetch_fn):
        records = fetch_fn(latitude=latitude, longitude=longitude, start_year=start_year, end_year=end_year)
        if records and len(records) > 0:
            return {"type": "records", "data": records, "bridge": "fetch_climate_data"}

    raise AttributeError("No callable climate data retrieval function found in backend.data_service")


def load_climate_dataset(
    location_id: str,
    latitude: float,
    longitude: float,
    location_name: str,
    start_year: int,
    end_year: int,
    baseline_start: int = 1981,
    baseline_end: int = 2010,
    force_demo: bool = False
) -> ClimateDataResult:
    """Fetches climate observations from backend data service and computes trend analysis.

    Falls back to synthetic demonstration data if:
    - force_demo is True
    - backend compatibility bridge is not yet present in the branch
    - NASA POWER API throws network, timeout, or payload errors
    """
    raw_records: Optional[List[Dict[str, Any]]] = None
    trend_results: Optional[Dict[str, Any]] = None
    is_demo = True
    source_label = "SYNTHETIC DEMO"
    status_message = "Backend compatibility bridge pending. Displaying synthetic demonstration data."
    bridge_used = "none"
    df: Optional[pd.DataFrame] = None

    if not force_demo:
        try:
            fetch_res = _cached_fetch_backend_data(
                location_id=location_id,
                latitude=latitude,
                longitude=longitude,
                start_year=start_year,
                end_year=end_year
            )
            bridge_used = fetch_res["bridge"]

            if fetch_res["type"] == "dataframe":
                df = _normalize_climate_dataframe(fetch_res["data"])
                # Generate record representation for trend_analysis module
                raw_records = []
                for _, row in df.iterrows():
                    raw_records.append({
                        "month": f"{int(row['year'])}{int(row['month']):02d}",
                        "temperature": row["T2M"] if not np.isnan(row["T2M"]) else None,
                        "precipitation": round(row["PRECTOTCORR"] / 30.0, 2) if not np.isnan(row["PRECTOTCORR"]) else None,
                        "precipitation_mm": row["PRECTOTCORR"] if not np.isnan(row["PRECTOTCORR"]) else None,
                    })
                is_demo = False
                source_label = "NASA POWER (Live Observation)"
                status_message = f"Connected via {bridge_used}() (Domain: {location_name})"

            elif fetch_res["type"] == "records":
                raw_records = fetch_res["data"]
                df = _convert_backend_records_to_df(raw_records)
                is_demo = False
                source_label = "NASA POWER (Live Observation)"
                status_message = f"Connected via {bridge_used}() (Lat: {latitude:.4f}° N, Lon: {longitude:.4f}° E)"

        except (ImportError, ModuleNotFoundError):
            status_message = "Backend modules pending merge into frontend branch. Displaying synthetic demonstration data."
        except AttributeError as a_err:
            status_message = f"Backend bridge status: {a_err}. Displaying synthetic demonstration data."
        except RuntimeError as err:
            status_message = f"NASA POWER API Error ({err}). Fallback to demonstration data."
        except Exception as exc:
            status_message = f"Backend notice ({type(exc).__name__}: {exc}). Fallback to demo data."

    if not is_demo and df is not None and raw_records:
        # Attempt to run backend trend analysis
        try:
            trend_module = importlib.import_module("backend.trend_analysis")
            analyze_fn = getattr(trend_module, "analyze_climate_trends")
            trend_results = analyze_fn(raw_records, location_name=location_name)
        except Exception:
            trend_results = None
    else:
        df = _generate_synthetic_kerala_data(start_year=start_year, end_year=end_year)
        # Attempt to run trend analysis on synthetic records if module is available
        try:
            trend_module = importlib.import_module("backend.trend_analysis")
            analyze_fn = getattr(trend_module, "analyze_climate_trends")
            synth_records = []
            for _, row in df.iterrows():
                synth_records.append({
                    "month": f"{int(row['year'])}{int(row['month']):02d}",
                    "temperature": row["T2M"],
                    "precipitation": round(row["PRECTOTCORR"] / 30.0, 2),
                    "precipitation_mm": row["PRECTOTCORR"],
                })
            trend_results = analyze_fn(synth_records, location_name=location_name)
        except Exception:
            trend_results = None

    # Compute baseline reference climatology (e.g. 1981-2010)
    baseline_df = df[(df["year"] >= baseline_start) & (df["year"] <= baseline_end)]
    if baseline_df.empty or baseline_df["T2M"].dropna().empty:
        baseline_df = df  # fallback if selected range doesn't cover baseline

    valid_temps = baseline_df["T2M"].dropna()
    baseline_t2m_mean = float(valid_temps.mean()) if not valid_temps.empty else 27.5

    annual_precip_by_yr = baseline_df.groupby("year")["PRECTOTCORR"].sum().dropna()
    baseline_annual_precip = float(annual_precip_by_yr.mean()) if not annual_precip_by_yr.empty else 2800.0

    baseline_stats = {
        "baseline_t2m_mean": baseline_t2m_mean,
        "baseline_annual_precip": baseline_annual_precip,
        "baseline_period": f"{baseline_start}–{baseline_end}",
    }

    return ClimateDataResult(
        df=df,
        is_demo=is_demo,
        source_label=source_label,
        status_message=status_message,
        baseline_stats=baseline_stats,
        trend_results=trend_results,
        raw_records=raw_records,
        bridge_used=bridge_used,
    )


def compute_descriptive_metrics(result: ClimateDataResult) -> Dict[str, Any]:
    """Computes descriptive summary metrics, integrating backend trend results if present."""
    df = result.df
    b_stats = result.baseline_stats
    trends = result.trend_results

    # Temperature metrics
    valid_temps = df["T2M"].dropna()
    t2m_mean = float(valid_temps.mean()) if not valid_temps.empty else np.nan
    t2m_min = float(valid_temps.min()) if not valid_temps.empty else np.nan
    t2m_max = float(valid_temps.max()) if not valid_temps.empty else np.nan
    t2m_anomaly = (t2m_mean - b_stats["baseline_t2m_mean"]) if not np.isnan(t2m_mean) else np.nan

    # Precipitation metrics
    annual_precip_series = df.groupby("year")["PRECTOTCORR"].sum().dropna()
    precip_annual_mean = float(annual_precip_series.mean()) if not annual_precip_series.empty else np.nan
    valid_precip = df["PRECTOTCORR"].dropna()
    precip_peak_monthly = float(valid_precip.max()) if not valid_precip.empty else np.nan

    baseline_precip = b_stats["baseline_annual_precip"]
    if baseline_precip > 0 and not np.isnan(precip_annual_mean):
        precip_anomaly_pct = ((precip_annual_mean - baseline_precip) / baseline_precip) * 100.0
    else:
        precip_anomaly_pct = 0.0

    # Extract backend Theil-Sen statistical trends if available
    temp_trend_data = None
    rain_trend_data = None
    incomplete_years_data = None
    disclaimer = None

    if trends:
        temp_trend_data = trends.get("temperature_trend")
        rain_trend_data = trends.get("rainfall_trend")
        incomplete_years_data = trends.get("annual_aggregation", {}).get("incomplete_years")
        disclaimer = trends.get("disclaimer")

    return {
        "t2m_mean": t2m_mean,
        "t2m_min": t2m_min,
        "t2m_max": t2m_max,
        "t2m_anomaly": t2m_anomaly,
        "precip_annual_mean": precip_annual_mean,
        "precip_peak_monthly": precip_peak_monthly,
        "precip_anomaly_pct": precip_anomaly_pct,
        "is_demo": result.is_demo,
        "source_label": result.source_label,
        "baseline_period": b_stats["baseline_period"],
        "temp_trend": temp_trend_data,
        "rain_trend": rain_trend_data,
        "incomplete_years": incomplete_years_data,
        "disclaimer": disclaimer,
        "trend_results": trends,
        "bridge_used": result.bridge_used,
    }


def _generate_synthetic_kerala_data(start_year: int, end_year: int) -> pd.DataFrame:
    """Generates synthetic monthly climate demonstration data for Kerala."""
    rng = np.random.default_rng(seed=2026)

    records = []
    monthly_temp_norm = [26.8, 27.9, 29.2, 29.8, 29.2, 27.1, 26.4, 26.7, 27.2, 27.3, 27.2, 26.9]
    monthly_precip_norm = [12.0, 16.0, 35.0, 110.0, 240.0, 650.0, 680.0, 410.0, 230.0, 290.0, 160.0, 35.0]

    for yr in range(start_year, end_year + 1):
        yr_offset = (yr - 1980) * 0.012

        for m_idx in range(12):
            month = m_idx + 1
            base_temp = monthly_temp_norm[m_idx] + yr_offset
            temp_noise = rng.normal(0, 0.45)
            t2m = round(float(base_temp + temp_noise), 2)

            base_precip = monthly_precip_norm[m_idx]
            precip_factor = rng.lognormal(mean=0.0, sigma=0.25)
            precip = round(float(max(0.0, base_precip * precip_factor)), 1)

            date_str = f"{yr}-{month:02d}-01"
            records.append({
                "year": yr,
                "month": month,
                "date": pd.Timestamp(date_str),
                "T2M": t2m,
                "PRECTOTCORR": precip,
            })

    return pd.DataFrame(records)
