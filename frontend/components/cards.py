"""Climate indicator KPI cards component for EARTHPULSE.
Presents scientific indicator cards for T2M and PRECTOTCORR with backend Theil-Sen trend metrics,
baseline anomalies, and data provenance labeling.
"""

from typing import Dict, Any
import numpy as np
import streamlit as st


def render_climate_indicator_cards(
    metrics: Dict[str, Any],
    show_t2m: bool = True,
    show_precip: bool = True
):
    """Renders responsive modern scientific KPI cards for temperature and precipitation.

    Adheres strictly to scientific integrity:
    - Clearly marks whether data is synthetic demo or live NASA POWER.
    - Displays backend Theil-Sen trend rates and Kendall tau significance when available on live data.
    - Avoids calculating daily extremes from monthly data.
    - Does not display fabricated trends in demo mode.
    - Handles empty or all-missing data points cleanly with 'N/A'.
    """
    if not show_t2m and not show_precip:
        st.info("ℹ️ Select at least one climate variable (T2M or PRECTOTCORR) in the sidebar to view indicator cards.")
        return

    is_demo = metrics["is_demo"]
    source_badge_text = "DEMO" if is_demo else "NASA POWER"
    source_badge_class = "ep-badge-demo" if is_demo else "ep-badge-live"

    t2m_mean = metrics["t2m_mean"]
    t2m_min = metrics["t2m_min"]
    t2m_max = metrics["t2m_max"]
    t2m_anomaly = metrics["t2m_anomaly"]

    precip_annual_mean = metrics["precip_annual_mean"]
    precip_peak = metrics["precip_peak_monthly"]
    precip_anomaly_pct = metrics["precip_anomaly_pct"]
    baseline_period = metrics["baseline_period"]

    temp_trend = metrics.get("temp_trend")
    rain_trend = metrics.get("rain_trend")

    # Format values safely
    t2m_mean_str = f"{t2m_mean:.2f}" if (t2m_mean is not None and not np.isnan(t2m_mean)) else "N/A"
    t2m_min_str = f"{t2m_min:.1f}" if (t2m_min is not None and not np.isnan(t2m_min)) else "N/A"
    t2m_max_str = f"{t2m_max:.1f}" if (t2m_max is not None and not np.isnan(t2m_max)) else "N/A"

    if t2m_anomaly is not None and not np.isnan(t2m_anomaly):
        temp_sign = "+" if t2m_anomaly > 0 else ""
        temp_anomaly_str = f"{temp_sign}{t2m_anomaly:.2f} °C vs {baseline_period} normal"
        temp_anomaly_color = "#FF6B6B" if t2m_anomaly > 0 else "#4FACFE"
    else:
        temp_anomaly_str = "No baseline deviation"
        temp_anomaly_color = "#94A3B8"

    precip_mean_str = f"{precip_annual_mean:,.0f}" if (precip_annual_mean is not None and not np.isnan(precip_annual_mean)) else "N/A"
    precip_peak_str = f"{precip_peak:,.1f}" if (precip_peak is not None and not np.isnan(precip_peak)) else "N/A"

    if precip_anomaly_pct is not None and not np.isnan(precip_anomaly_pct):
        precip_sign = "+" if precip_anomaly_pct > 0 else ""
        precip_anomaly_str = f"{precip_sign}{precip_anomaly_pct:.1f}% vs {baseline_period} normal"
        precip_anomaly_color = "#00E676" if precip_anomaly_pct >= 0 else "#F59E0B"
    else:
        precip_anomaly_str = "No baseline deviation"
        precip_anomaly_color = "#94A3B8"

    # Card 1 & 2: Temperature HTML
    temp_card_1 = ""
    temp_card_2 = ""
    if show_t2m:
        trend_html = ""
        if temp_trend and not is_demo and temp_trend.get("slope_per_decade") is not None:
            slope = temp_trend["slope_per_decade"]
            p_val = temp_trend.get("p_value", 1.0)
            is_sig = temp_trend.get("is_statistically_significant", False)
            sig_color = "#34D399" if is_sig else "#94A3B8"
            sig_label = "sig" if is_sig else "n.s."
            trend_html = f"""
            <div style="font-size: 0.78rem; color: #CBD5E1; margin-top: 0.2rem;">
                <strong>Theil-Sen:</strong> {slope:+.2f} °C/dec 
                <span style="color: {sig_color}; font-weight: 600;">(p={p_val:.3f}, {sig_label})</span>
            </div>
            """

        temp_card_1 = f"""
        <div class="ep-metric-card temp">
            <div class="ep-card-title">
                <span>T2M Mean Surface Temp</span>
                <span class="ep-badge {source_badge_class}">{source_badge_text}</span>
            </div>
            <div class="ep-card-value">
                {t2m_mean_str}<span class="unit">°C</span>
            </div>
            <div class="ep-card-subtext">
                <span style="color: {temp_anomaly_color}; font-weight: 700;">
                    {temp_anomaly_str}
                </span>
            </div>
            {trend_html}
        </div>
        """

        temp_card_2 = f"""
        <div class="ep-metric-card temp">
            <div class="ep-card-title">
                <span>T2M Monthly Envelope</span>
                <span class="ep-badge {source_badge_class}">{source_badge_text}</span>
            </div>
            <div class="ep-card-value" style="font-size: 1.55rem; padding-top: 0.25rem;">
                {t2m_min_str} <span style="font-size: 1.1rem; color: #64748B;">to</span> {t2m_max_str}<span class="unit">°C</span>
            </div>
            <div class="ep-card-subtext" style="margin-top: 0.5rem;">
                <span>Monthly thermal boundary</span>
            </div>
        </div>
        """

    # Card 3 & 4: Precipitation HTML
    precip_card_1 = ""
    precip_card_2 = ""
    if show_precip:
        rain_trend_html = ""
        if rain_trend and not is_demo and rain_trend.get("slope_per_decade") is not None:
            r_slope = rain_trend["slope_per_decade"]
            r_pval = rain_trend.get("p_value", 1.0)
            r_sig = rain_trend.get("is_statistically_significant", False)
            r_sig_color = "#34D399" if r_sig else "#94A3B8"
            r_sig_label = "sig" if r_sig else "n.s."
            rain_trend_html = f"""
            <div style="font-size: 0.78rem; color: #CBD5E1; margin-top: 0.2rem;">
                <strong>Theil-Sen:</strong> {r_slope:+.1f} mm/dec 
                <span style="color: {r_sig_color}; font-weight: 600;">(p={r_pval:.3f}, {r_sig_label})</span>
            </div>
            """

        precip_card_1 = f"""
        <div class="ep-metric-card precip">
            <div class="ep-card-title">
                <span>Mean Annual Precip</span>
                <span class="ep-badge {source_badge_class}">{source_badge_text}</span>
            </div>
            <div class="ep-card-value">
                {precip_mean_str}<span class="unit">mm/yr</span>
            </div>
            <div class="ep-card-subtext">
                <span style="color: {precip_anomaly_color}; font-weight: 700;">
                    {precip_anomaly_str}
                </span>
            </div>
            {rain_trend_html}
        </div>
        """

        precip_card_2 = f"""
        <div class="ep-metric-card precip">
            <div class="ep-card-title">
                <span>Peak Monthly Precip</span>
                <span class="ep-badge {source_badge_class}">{source_badge_text}</span>
            </div>
            <div class="ep-card-value">
                {precip_peak_str}<span class="unit">mm</span>
            </div>
            <div class="ep-card-subtext">
                <span>Highest single monthly deluge</span>
            </div>
        </div>
        """

    # Responsive column allocation
    if show_t2m and show_precip:
        cols = st.columns(4)
        with cols[0]:
            st.markdown(temp_card_1, unsafe_allow_html=True)
        with cols[1]:
            st.markdown(temp_card_2, unsafe_allow_html=True)
        with cols[2]:
            st.markdown(precip_card_1, unsafe_allow_html=True)
        with cols[3]:
            st.markdown(precip_card_2, unsafe_allow_html=True)
    elif show_t2m and not show_precip:
        cols = st.columns(2)
        with cols[0]:
            st.markdown(temp_card_1, unsafe_allow_html=True)
        with cols[1]:
            st.markdown(temp_card_2, unsafe_allow_html=True)
    elif show_precip and not show_t2m:
        cols = st.columns(2)
        with cols[0]:
            st.markdown(precip_card_1, unsafe_allow_html=True)
        with cols[1]:
            st.markdown(precip_card_2, unsafe_allow_html=True)
