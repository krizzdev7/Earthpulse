"""EARTHPULSE – NASA Earth System Trend Analyzer.
NASA Space Apps Challenge 2026.

Main Streamlit Application Entry Point.
"""

import streamlit as st

# Configure page layout and metadata first
st.set_page_config(
    page_title="EARTHPULSE | NASA Earth System Trend Analyzer",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

from frontend.styles import apply_custom_styles
from frontend.data_adapter import load_climate_dataset, compute_descriptive_metrics
from frontend.components.header import render_header
from frontend.components.sidebar import render_sidebar
from frontend.components.cards import render_climate_indicator_cards
from frontend.components.charts import (
    render_temperature_charts,
    render_precipitation_charts,
    render_climatology_cycle_chart,
)


def main():
    # 1. Apply Dark Scientific Theme Styles
    apply_custom_styles()

    # 2. Render Sidebar Controls & Retrieve Analysis Parameters
    params = render_sidebar()
    loc = params["location"]
    start_year = params["start_year"]
    end_year = params["end_year"]
    baseline_start = params["baseline_start"]
    baseline_end = params["baseline_end"]
    show_t2m = params["show_t2m"]
    show_precip = params["show_precip"]

    # 3. Load Dataset via Backend Adapter Bridge
    data_res = load_climate_dataset(
        location_id=loc.id,
        latitude=loc.latitude,
        longitude=loc.longitude,
        location_name=loc.name,
        start_year=start_year,
        end_year=end_year,
        baseline_start=baseline_start,
        baseline_end=baseline_end,
    )

    df = data_res.df
    is_demo = data_res.is_demo
    source_label = data_res.source_label
    baseline_stats = data_res.baseline_stats
    trend_results = data_res.trend_results

    # Filter data according to selected year range
    filtered_df = df[(df["year"] >= start_year) & (df["year"] <= end_year)].copy()

    # 4. Render Main Branding Header & Prototype Banner
    render_header(is_demo=is_demo, source_label=source_label, status_message=data_res.status_message)

    # 5. Selected Domain Meta Banner
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(19, 28, 46, 0.6); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 0.65rem 1rem; margin-bottom: 1.2rem; font-size: 0.85rem; color: #CBD5E1;">
            <div>
                <strong>Active Domain:</strong> <span style="color: #00D2FF;">{loc.name}</span> &bull; 
                <span>{loc.latitude:.4f}° N, {loc.longitude:.4f}° E</span>
            </div>
            <div>
                <strong>Window:</strong> <span style="color: #F8FAFC;">{start_year} – {end_year}</span> 
                ({end_year - start_year + 1} years) &bull;
                <strong>Baseline:</strong> <span style="color: #FFD166;">{baseline_stats['baseline_period']}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 6. Compute & Render Climate Indicator KPI Cards
    metrics = compute_descriptive_metrics(data_res)
    render_climate_indicator_cards(metrics)

    st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)

    # 7. Analysis Visualizations Section
    tab_titles = []
    if show_t2m:
        tab_titles.append("🌡️ Temperature Dynamics (T2M)")
    if show_precip:
        tab_titles.append("🌧️ Precipitation Dynamics (PRECTOTCORR)")
    tab_titles.append("🔄 Climatological Annual Cycle")
    tab_titles.append("📋 Trends, Provenance & Backend Status")

    tabs = st.tabs(tab_titles)
    current_tab_idx = 0

    # Temperature Tab
    if show_t2m:
        with tabs[current_tab_idx]:
            st.markdown(
                """
                <div style="font-size: 0.88rem; color: #94A3B8; margin-bottom: 0.8rem;">
                    Temporal evolution of monthly 2-meter air temperature (<strong>T2M</strong>) alongside a 
                    12-month rolling mean to filter out sub-annual seasonality and reveal multi-year thermal shifts.
                </div>
                """,
                unsafe_allow_html=True
            )
            annual_temp_series = None
            if trend_results and "annual_aggregation" in trend_results:
                annual_temp_series = trend_results["annual_aggregation"].get("temperature_series")
            render_temperature_charts(filtered_df, baseline_stats, is_demo, annual_temp_series=annual_temp_series)
        current_tab_idx += 1

    # Precipitation Tab
    if show_precip:
        with tabs[current_tab_idx]:
            st.markdown(
                """
                <div style="font-size: 0.88rem; color: #94A3B8; margin-bottom: 0.8rem;">
                    Precipitation patterns (<strong>PRECTOTCORR</strong>) showing monthly variability 
                    and cumulative annual rainfall volume using backend complete-year aggregation.
                </div>
                """,
                unsafe_allow_html=True
            )
            annual_records = None
            if trend_results and "annual_aggregation" in trend_results:
                annual_records = trend_results["annual_aggregation"].get("annual_records")
            render_precipitation_charts(filtered_df, baseline_stats, is_demo, annual_records=annual_records)
        current_tab_idx += 1

    # Climatological Annual Cycle Tab
    with tabs[current_tab_idx]:
        st.markdown(
            """
            <div style="font-size: 0.88rem; color: #94A3B8; margin-bottom: 0.8rem;">
                Mean annual climatological profile (January–December) representing seasonal dynamics 
                across available observations, highlighting Kerala's Southwest (Jun–Aug) and Northeast (Oct–Nov) monsoons.
            </div>
            """,
            unsafe_allow_html=True
        )
        monthly_climatology = None
        if trend_results:
            monthly_climatology = trend_results.get("monthly_climatology")
        render_climatology_cycle_chart(filtered_df, is_demo, monthly_climatology=monthly_climatology)
    current_tab_idx += 1

    # Backend Integration & Data Provenance Tab
    with tabs[current_tab_idx]:
        # Statistical Trends Section
        if trend_results:
            t_trend = trend_results.get("temperature_trend")
            r_trend = trend_results.get("rainfall_trend")

            st.markdown(
                """
                <div class="ep-section-box">
                    <div class="ep-section-header">
                        <span>📈 Theil-Sen Statistical Trend Analysis</span>
                    </div>
                    <p style="color: #94A3B8; font-size: 0.88rem; line-height: 1.5; margin-bottom: 1rem;">
                        Rigorous non-parametric statistical evaluation using Theil-Sen robust linear slope estimation 
                        and Kendall's rank correlation test across complete calendar years.
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

            col_t, col_r = st.columns(2)

            with col_t:
                if t_trend:
                    t_dir = t_trend.get("trend_direction", "no detected trend")
                    t_slope = t_trend.get("slope_per_decade")
                    t_tau = t_trend.get("kendall_tau")
                    t_pval = t_trend.get("p_value")
                    t_sig = t_trend.get("is_statistically_significant", False)
                    t_obs = t_trend.get("observations", 0)

                    slope_str = f"{t_slope:+.3f} °C/decade" if t_slope is not None else "N/A"
                    tau_str = f"{t_tau:+.3f}" if t_tau is not None else "N/A"
                    pval_str = f"{t_pval:.4f}" if t_pval is not None else "N/A"

                    st.markdown(
                        f"""
                        <div style="background: rgba(19, 28, 46, 0.7); border: 1px solid rgba(255, 107, 107, 0.3); border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
                            <div style="font-size: 0.85rem; font-weight: 700; color: #FF6B6B; text-transform: uppercase;">Surface Temperature (T2M)</div>
                            <div style="font-size: 1.25rem; font-weight: 800; color: #F8FAFC; margin-top: 0.3rem;">
                                {slope_str}
                            </div>
                            <div style="font-size: 0.82rem; color: #94A3B8; margin-top: 0.5rem; line-height: 1.6;">
                                <div><strong>Direction:</strong> <span style="text-transform: capitalize; color: #CBD5E1;">{t_dir}</span></div>
                                <div><strong>Kendall Rank Tau:</strong> {tau_str} &bull; <strong>p-value:</strong> {pval_str}</div>
                                <div><strong>Significance (α=0.05):</strong> <span style="color: {'#34D399' if t_sig else '#94A3B8'}; font-weight: 700;">{'Statistically Significant' if t_sig else 'Not Significant'}</span></div>
                                <div><strong>Complete Observations:</strong> {t_obs} years</div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            with col_r:
                if r_trend:
                    r_dir = r_trend.get("trend_direction", "no detected trend")
                    r_slope = r_trend.get("slope_per_decade")
                    r_tau = r_trend.get("kendall_tau")
                    r_pval = r_trend.get("p_value")
                    r_sig = r_trend.get("is_statistically_significant", False)
                    r_obs = r_trend.get("observations", 0)

                    r_slope_str = f"{r_slope:+.1f} mm/decade" if r_slope is not None else "N/A"
                    r_tau_str = f"{r_tau:+.3f}" if r_tau is not None else "N/A"
                    r_pval_str = f"{r_pval:.4f}" if r_pval is not None else "N/A"

                    st.markdown(
                        f"""
                        <div style="background: rgba(19, 28, 46, 0.7); border: 1px solid rgba(0, 230, 118, 0.3); border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
                            <div style="font-size: 0.85rem; font-weight: 700; color: #00E676; text-transform: uppercase;">Precipitation Total (PRECTOTCORR)</div>
                            <div style="font-size: 1.25rem; font-weight: 800; color: #F8FAFC; margin-top: 0.3rem;">
                                {r_slope_str}
                            </div>
                            <div style="font-size: 0.82rem; color: #94A3B8; margin-top: 0.5rem; line-height: 1.6;">
                                <div><strong>Direction:</strong> <span style="text-transform: capitalize; color: #CBD5E1;">{r_dir}</span></div>
                                <div><strong>Kendall Rank Tau:</strong> {r_tau_str} &bull; <strong>p-value:</strong> {r_pval_str}</div>
                                <div><strong>Significance (α=0.05):</strong> <span style="color: {'#34D399' if r_sig else '#94A3B8'}; font-weight: 700;">{'Statistically Significant' if r_sig else 'Not Significant'}</span></div>
                                <div><strong>Complete Observations:</strong> {r_obs} years</div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            # Incomplete-year warnings
            incomplete_years = trend_results.get("annual_aggregation", {}).get("incomplete_years", {})
            if incomplete_years:
                excluded_list = ", ".join(str(y) for y in sorted(incomplete_years.keys()))
                st.markdown(
                    f"""
                    <div style="background: rgba(245, 158, 11, 0.1); border-left: 3px solid #F59E0B; border-radius: 6px; padding: 0.65rem 1rem; margin-bottom: 1rem; font-size: 0.82rem; color: #FBBF24;">
                        <strong>ℹ️ Incomplete Years Excluded from Annual Trends:</strong> 
                        Years {excluded_list} had fewer than 12 valid monthly observations and were excluded from annual aggregations 
                        in strict accordance with scientific climate standards.
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            # Attribution & Causation Disclaimer
            disclaimer_text = trend_results.get("disclaimer")
            if disclaimer_text:
                st.markdown(
                    f"""
                    <div style="background: rgba(14, 22, 38, 0.8); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 0.85rem 1.1rem; margin-bottom: 1.2rem; font-size: 0.82rem; color: #94A3B8; line-height: 1.5;">
                        <span style="color: #CBD5E1; font-weight: 700;">⚖️ Scientific Attribution Disclaimer:</span> 
                        {disclaimer_text}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # Provenance & Backend Connection Status Box
        st.markdown(
            f"""
            <div class="ep-section-box">
                <div class="ep-section-header">
                    <span>🔌 Backend Data Service & Provenance</span>
                </div>
                <div style="font-size: 0.85rem; color: #CBD5E1; line-height: 1.6;">
                    <div><strong>Service Pipeline:</strong> <code>backend.data_service.fetch_climate_data()</code> &bull; <code>backend.trend_analysis.analyze_climate_trends()</code></div>
                    <div><strong>Connection Status:</strong> <span style="color: {'#FBBF24' if is_demo else '#34D399'}; font-weight: 600;">{data_res.status_message}</span></div>
                    <div><strong>NASA POWER Parameters:</strong> <code>T2M</code> (Air Temp at 2m), <code>PRECTOTCORR</code> (Precipitation Corrected)</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("**Observation Dataset Preview**")
        preview_df = filtered_df[["year", "month", "T2M", "PRECTOTCORR"]].copy()
        st.dataframe(
            preview_df.head(24),
            use_container_width=True,
            hide_index=True
        )

        # Download CSV button
        csv_data = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Filtered Data (CSV)",
            data=csv_data,
            file_name=f"earthpulse_{loc.id}_{start_year}_{end_year}.csv",
            mime="text/csv",
        )

    # Footer
    st.markdown(
        """
        <div style="text-align: center; margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid rgba(255, 255, 255, 0.08); font-size: 0.8rem; color: #64748B;">
            EARTHPULSE &bull; NASA Space Apps Challenge 2026 &bull; Frontend MVP &bull; Developed with Streamlit & Plotly
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
