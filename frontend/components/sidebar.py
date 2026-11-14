"""Sidebar configuration component for EARTHPULSE.
Manages modular location selection, temporal range filtering, and climate parameter controls.
"""

from dataclasses import dataclass
from typing import Dict, Any
import streamlit as st


@dataclass
class LocationConfig:
    """Configuration for a geographic analysis target."""
    id: str
    name: str
    region: str
    country: str
    latitude: float
    longitude: float
    description: str


# Modular Location Registry: Easily extensible for additional Indian states or global coordinates
LOCATIONS_REGISTRY: Dict[str, LocationConfig] = {
    "kerala_statewide": LocationConfig(
        id="kerala_statewide",
        name="Kerala (Statewide Regional Average)",
        region="South India",
        country="India",
        latitude=10.8505,
        longitude=76.2711,
        description="Composite spatial domain covering the Arabian Sea coast to the Western Ghats crestline."
    ),
    "kerala_wayanad": LocationConfig(
        id="kerala_wayanad",
        name="Wayanad District (Highland)",
        region="Western Ghats",
        country="India",
        latitude=11.6854,
        longitude=76.1320,
        description="Highland plateau characterized by cloud forests and high precipitation variability."
    ),
    "kerala_idukki": LocationConfig(
        id="kerala_idukki",
        name="Idukki District (High Ranges)",
        region="Western Ghats",
        country="India",
        latitude=9.8494,
        longitude=76.9804,
        description="Major catchment basin and hydroelectric reservoir corridor with steep orographic rainfall."
    ),
    "kerala_ernakulam": LocationConfig(
        id="kerala_ernakulam",
        name="Ernakulam / Kochi (Central Coastal)",
        region="Arabian Sea Coast",
        country="India",
        latitude=9.9816,
        longitude=76.2999,
        description="Lowland coastal plain and urban-industrial agglomeration influenced by marine sea breezes."
    ),
    "kerala_thiruvananthapuram": LocationConfig(
        id="kerala_thiruvananthapuram",
        name="Thiruvananthapuram (South Coast)",
        region="South Coastal",
        country="India",
        latitude=8.5241,
        longitude=76.9366,
        description="Southern coastal terminus with distinct dual-monsoon interaction patterns."
    ),
    "kerala_palakkad": LocationConfig(
        id="kerala_palakkad",
        name="Palakkad Gap (Inland Basin)",
        region="Inland Plains",
        country="India",
        latitude=10.7867,
        longitude=76.6548,
        description="Major geological gap in the Western Ghats with high diurnal thermal ranges and drier climate."
    ),
}


def render_sidebar() -> Dict[str, Any]:
    """Renders the sidebar controls and returns user selections."""
    st.sidebar.markdown(
        """
        <div style="padding-bottom: 0.8rem; border-bottom: 1px solid rgba(255, 255, 255, 0.08); margin-bottom: 1.2rem;">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span style="font-size: 1.4rem;">🛰️</span>
                <span style="font-size: 1.15rem; font-weight: 700; color: #F1F5F9; letter-spacing: -0.01em;">Analysis Controls</span>
            </div>
            <div style="font-size: 0.78rem; color: #64748B; margin-top: 0.2rem;">NASA POWER Parameter Suite</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 1. Modular Location Selector
    st.sidebar.markdown("**Target Domain**")
    loc_options = list(LOCATIONS_REGISTRY.keys())
    loc_labels = [LOCATIONS_REGISTRY[k].name for k in loc_options]

    selected_loc_res = st.sidebar.selectbox(
        "Select Location",
        options=range(len(loc_options)),
        format_func=lambda i: loc_labels[i],
        help="Geographic domain for NASA POWER spatial point or regional grid aggregation."
    )
    if isinstance(selected_loc_res, str):
        selected_location_id = selected_loc_res if selected_loc_res in LOCATIONS_REGISTRY else loc_options[0]
    else:
        idx = int(selected_loc_res) if 0 <= int(selected_loc_res) < len(loc_options) else 0
        selected_location_id = loc_options[idx]

    selected_location = LOCATIONS_REGISTRY[selected_location_id]

    # Location info pill
    st.sidebar.markdown(
        f"""
        <div style="background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 0.6rem 0.8rem; margin-top: -0.5rem; margin-bottom: 1.2rem; font-size: 0.78rem; color: #94A3B8;">
            <div><strong>Coordinates:</strong> {selected_location.latitude:.4f}° N, {selected_location.longitude:.4f}° E</div>
            <div><strong>Physiography:</strong> {selected_location.region}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 2. Date / Year Range Filters
    st.sidebar.markdown("**Temporal Analysis Window**")
    min_year = 1985
    max_year = 2025
    default_start = 1990
    default_end = 2024

    year_range = st.sidebar.slider(
        "Observation Years",
        min_value=min_year,
        max_value=max_year,
        value=(default_start, default_end),
        step=1,
        help="Select the multi-decadal time window for Earth system trend analysis."
    )
    start_year, end_year = year_range

    # Climatological baseline selector
    st.sidebar.markdown("**Climatological Baseline**")
    baseline_options = {
        "1981-2010": (1981, 2010),
        "1991-2020": (1991, 2020),
    }
    baseline_keys = list(baseline_options.keys())
    selected_baseline_res = st.sidebar.selectbox(
        "Reference Baseline Period",
        options=baseline_keys,
        index=0,
        help="Standard 30-year reference climatology used for calculating anomalies."
    )
    if isinstance(selected_baseline_res, int) and 0 <= selected_baseline_res < len(baseline_keys):
        selected_baseline_name = baseline_keys[selected_baseline_res]
    elif str(selected_baseline_res) in baseline_options:
        selected_baseline_name = str(selected_baseline_res)
    else:
        selected_baseline_name = baseline_keys[0]

    b_start, b_end = baseline_options[selected_baseline_name]

    # 3. Climate Variables (Initial MVP scope strictly T2M & PRECTOTCORR)
    st.sidebar.markdown("**Active Climate Variables**")
    show_t2m = st.sidebar.checkbox(
        "T2M (Air Temperature at 2m, °C)",
        value=True,
        help="Monthly mean surface air temperature."
    )
    show_precip = st.sidebar.checkbox(
        "PRECTOTCORR (Precipitation Corrected, mm)",
        value=True,
        help="Monthly cumulative precipitation."
    )

    # System Status footnote
    st.sidebar.markdown(
        """
        <div style="margin-top: 2rem; padding-top: 1rem; border-top: 1px solid rgba(255, 255, 255, 0.08); font-size: 0.74rem; color: #64748B;">
            <div><strong>NASA Space Apps 2026</strong></div>
            <div>Challenge: Earth System Trend Analyzer</div>
            <div style="margin-top: 0.3rem;">Frontend Architecture: Modular Streamlit</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    return {
        "location": selected_location,
        "start_year": start_year,
        "end_year": end_year,
        "baseline_start": b_start,
        "baseline_end": b_end,
        "baseline_name": selected_baseline_name,
        "show_t2m": show_t2m,
        "show_precip": show_precip,
    }
