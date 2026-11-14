"""Data Adapter module for EARTHPULSE.
Acts as a bridge between the frontend and backend services (data_service.py / trend_analysis.py).

INTEGRATION CONTRACT:
Backend developers should implement:
    data_service.fetch_climate_data(location_id: str, start_year: int, end_year: int) -> pd.DataFrame
with required columns:
    - 'year' (int)
    - 'month' (int: 1-12)
    - 'date' (pd.Timestamp or 'YYYY-MM')
    - 'T2M' (float, Temperature at 2m in °C)
    - 'PRECTOTCORR' (float, Precipitation Corrected in mm/month)

If backend services are not implemented or return empty results, this adapter
provides synthetic demonstration data explicitly labeled as a PROTOTYPE.
"""

from dataclasses import dataclass
import importlib
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd


@dataclass
class ClimateDataResult:
    """Encapsulates the dataset and provenance metadata."""
    df: pd.DataFrame
    is_demo: bool
    source_label: str
    status_message: str
    baseline_stats: Dict[str, float]


def load_climate_dataset(
    location_id: str,
    start_year: int,
    end_year: int,
    baseline_start: int = 1981,
    baseline_end: int = 2010
) -> ClimateDataResult:
    """Attempts to fetch data from backend `data_service.py`.

    Falls back to synthetic demonstration data if backend is unpopulated or missing.
    """
    backend_data = None
    is_demo = True
    source_label = "SYNTHETIC DEMO"
    status_message = "Backend data service is not populated. Displaying synthetic demonstration data."

    # Attempt to import backend-owned data_service dynamically
    try:
        data_service = importlib.import_module("data_service")
        # Check if backend provides fetch_climate_data or get_climate_data
        fetch_fn = getattr(data_service, "fetch_climate_data", None) or getattr(data_service, "get_climate_data", None)
        if callable(fetch_fn):
            res = fetch_fn(location_id=location_id, start_year=start_year, end_year=end_year)
            if isinstance(res, pd.DataFrame) and not res.empty and "T2M" in res.columns and "PRECTOTCORR" in res.columns:
                backend_data = res
                is_demo = False
                source_label = "NASA POWER (Live Backend)"
                status_message = "Connected to backend data service."
    except Exception as exc:
        # Backend not ready or errored; fallback to demo mode
        status_message = f"Backend unavailable ({type(exc).__name__}). Using synthetic demonstration data."

    if backend_data is not None:
        df = backend_data.copy()
        if "date" not in df.columns and "year" in df.columns and "month" in df.columns:
            df["date"] = pd.to_datetime(df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2) + "-01")
    else:
        df = _generate_synthetic_kerala_data(start_year=start_year, end_year=end_year)

    # Compute baseline reference climatology (e.g. 1981-2010)
    baseline_df = df[(df["year"] >= baseline_start) & (df["year"] <= baseline_end)]
    if baseline_df.empty:
        baseline_df = df  # fallback if selected range doesn't cover baseline

    baseline_t2m_mean = float(baseline_df["T2M"].mean())
    baseline_annual_precip = float(baseline_df.groupby("year")["PRECTOTCORR"].sum().mean())

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
    )


def compute_descriptive_metrics(result: ClimateDataResult) -> Dict[str, Any]:
    """Computes strictly empirical descriptive statistics from the dataset.

    NOTE: Adheres strictly to scientific integrity:
    - Does NOT invent daily extreme rainfall days from monthly totals.
    - Does NOT fabricate unverified warming trend claims.
    """
    df = result.df
    b_stats = result.baseline_stats

    # Temperature metrics
    t2m_mean = float(df["T2M"].mean())
    t2m_min = float(df["T2M"].min())
    t2m_max = float(df["T2M"].max())
    t2m_anomaly = t2m_mean - b_stats["baseline_t2m_mean"]

    # Precipitation metrics (monthly aggregation)
    annual_precip_series = df.groupby("year")["PRECTOTCORR"].sum()
    precip_annual_mean = float(annual_precip_series.mean())
    precip_peak_monthly = float(df["PRECTOTCORR"].max())

    baseline_precip = b_stats["baseline_annual_precip"]
    if baseline_precip > 0:
        precip_anomaly_pct = ((precip_annual_mean - baseline_precip) / baseline_precip) * 100.0
    else:
        precip_anomaly_pct = 0.0

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
    }


def _generate_synthetic_kerala_data(start_year: int, end_year: int) -> pd.DataFrame:
    """Generates synthetic, physically plausible monthly data for Kerala demonstration.

    Calibrated to Kerala's tropical monsoon climate:
    - Mean monthly T2M: ~26°C to 31°C (warmer in March-May pre-monsoon, cooler in July-August monsoon).
    - PRECTOTCORR: Heavy June-August Southwest monsoon, moderate October-November Northeast monsoon,
      dry December-February.
    """
    # Deterministic seed for reproducible testing
    rng = np.random.default_rng(seed=2026)

    records = []
    # Monthly climatological profiles for Kerala
    # Months 1 to 12: Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec
    monthly_temp_norm = [26.8, 27.9, 29.2, 29.8, 29.2, 27.1, 26.4, 26.7, 27.2, 27.3, 27.2, 26.9]
    monthly_precip_norm = [12.0, 16.0, 35.0, 110.0, 240.0, 650.0, 680.0, 410.0, 230.0, 290.0, 160.0, 35.0]

    for yr in range(start_year, end_year + 1):
        # Subtle realistic multi-decadal drift for demo realism (without asserting it as factual NASA data)
        yr_offset = (yr - 1980) * 0.012

        for m_idx in range(12):
            month = m_idx + 1
            # Temperature with monthly profile + subtle variation
            base_temp = monthly_temp_norm[m_idx] + yr_offset
            temp_noise = rng.normal(0, 0.45)
            t2m = round(float(base_temp + temp_noise), 2)

            # Precipitation with monsoon skew
            base_precip = monthly_precip_norm[m_idx]
            # Interannual monsoon variability
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
