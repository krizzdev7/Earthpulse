"""Climate indicator KPI cards component for EARTHPULSE.
Presents scientific indicator cards for T2M and PRECTOTCORR with backend Theil-Sen trend metrics,
baseline anomalies, and data provenance labeling.
"""

from typing import Dict, Any
import streamlit as st


def render_climate_indicator_cards(metrics: Dict[str, Any]):
    """Renders responsive modern scientific KPI cards for temperature and precipitation.

    Adheres strictly to scientific integrity:
    - Clearly marks whether data is synthetic demo or live NASA POWER.
    - Displays backend Theil-Sen trend rates and Kendall tau significance when available on live data.
    - Avoids calculating daily extremes from monthly data.
    - Does not display fabricated trends in demo mode.
    """
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

    # Formatting anomaly signs
    temp_sign = "+" if t2m_anomaly > 0 else ""
    precip_sign = "+" if precip_anomaly_pct > 0 else ""

    col1, col2, col3, col4 = st.columns(4)

    # 1. Temperature Card
    with col1:
        # Build trend indicator line if available
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

        st.markdown(
            f"""
            <div class="ep-metric-card temp">
                <div class="ep-card-title">
                    <span>T2M Mean Surface Temp</span>
                    <span class="ep-badge {source_badge_class}">{source_badge_text}</span>
                </div>
                <div class="ep-card-value">
                    {t2m_mean:.2f}<span class="unit">°C</span>
                </div>
                <div class="ep-card-subtext">
                    <span style="color: {'#FF6B6B' if t2m_anomaly > 0 else '#4FACFE'}; font-weight: 700;">
                        {temp_sign}{t2m_anomaly:.2f} °C
                    </span>
                    <span>vs {baseline_period} normal</span>
                </div>
                {trend_html}
            </div>
            """,
            unsafe_allow_html=True
        )

    # 2. Temperature Envelope Card
    with col2:
        st.markdown(
            f"""
            <div class="ep-metric-card temp">
                <div class="ep-card-title">
                    <span>T2M Monthly Envelope</span>
                    <span class="ep-badge {source_badge_class}">{source_badge_text}</span>
                </div>
                <div class="ep-card-value" style="font-size: 1.55rem; padding-top: 0.25rem;">
                    {t2m_min:.1f} <span style="font-size: 1.1rem; color: #64748B;">to</span> {t2m_max:.1f}<span class="unit">°C</span>
                </div>
                <div class="ep-card-subtext" style="margin-top: 0.5rem;">
                    <span>Monthly thermal boundary</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 3. Precipitation Mean & Trend Card
    with col3:
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

        st.markdown(
            f"""
            <div class="ep-metric-card precip">
                <div class="ep-card-title">
                    <span>Mean Annual Precip</span>
                    <span class="ep-badge {source_badge_class}">{source_badge_text}</span>
                </div>
                <div class="ep-card-value">
                    {precip_annual_mean:,.0f}<span class="unit">mm/yr</span>
                </div>
                <div class="ep-card-subtext">
                    <span style="color: {'#00E676' if precip_anomaly_pct >= 0 else '#F59E0B'}; font-weight: 700;">
                        {precip_sign}{precip_anomaly_pct:.1f}%
                    </span>
                    <span>vs {baseline_period} normal</span>
                </div>
                {rain_trend_html}
            </div>
            """,
            unsafe_allow_html=True
        )

    # 4. Peak Monthly Precipitation Card
    with col4:
        st.markdown(
            f"""
            <div class="ep-metric-card precip">
                <div class="ep-card-title">
                    <span>Peak Monthly Precip</span>
                    <span class="ep-badge {source_badge_class}">{source_badge_text}</span>
                </div>
                <div class="ep-card-value">
                    {precip_peak:,.1f}<span class="unit">mm</span>
                </div>
                <div class="ep-card-subtext">
                    <span>Highest single monthly deluge</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
