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
        start_year=start_year,
        end_year=end_year,
        baseline_start=baseline_start,
        baseline_end=baseline_end,
    )

    df = data_res.df
    is_demo = data_res.is_demo
    source_label = data_res.source_label
    baseline_stats = data_res.baseline_stats

    # Filter data according to selected year range
    filtered_df = df[(df["year"] >= start_year) & (df["year"] <= end_year)].copy()

    # 4. Render Main Branding Header & Prototype Banner
    render_header(is_demo=is_demo, source_label=source_label)

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
    tab_titles.append("📋 Data Provenance & Backend Status")

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
            render_temperature_charts(filtered_df, baseline_stats, is_demo)
        current_tab_idx += 1

    # Precipitation Tab
    if show_precip:
        with tabs[current_tab_idx]:
            st.markdown(
                """
                <div style="font-size: 0.88rem; color: #94A3B8; margin-bottom: 0.8rem;">
                    Precipitation patterns (<strong>PRECTOTCORR</strong>) showing monthly variability 
                    and cumulative annual rainfall volume against standard baseline normals.
                </div>
                """,
                unsafe_allow_html=True
            )
            render_precipitation_charts(filtered_df, baseline_stats, is_demo)
        current_tab_idx += 1

    # Climatological Annual Cycle Tab
    with tabs[current_tab_idx]:
        st.markdown(
            """
            <div style="font-size: 0.88rem; color: #94A3B8; margin-bottom: 0.8rem;">
                Mean annual climatological profile (January–December) representing seasonal dynamics 
                across the selected observation window. Highlights tropical monsoon seasonality.
            </div>
            """,
            unsafe_allow_html=True
        )
        render_climatology_cycle_chart(filtered_df, is_demo)
    current_tab_idx += 1

    # Backend Integration & Data Provenance Tab
    with tabs[current_tab_idx]:
        st.markdown(
            f"""
            <div class="ep-section-box">
                <div class="ep-section-header">
                    <span>🔌 Frontend-Backend Integration Interface</span>
                </div>
                <p style="color: #94A3B8; font-size: 0.88rem; line-height: 1.6;">
                    The EARTHPULSE frontend is built decoupled from the backend. When backend engineers implement
                    <code>data_service.py</code>, the application will automatically ingest live NASA POWER data without 
                    requiring frontend refactoring.
                </p>
                <div style="background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.08); border-radius: 6px; padding: 0.8rem; font-family: monospace; font-size: 0.8rem; color: #A5F3FC;">
                    # Required backend function in data_service.py:<br>
                    def fetch_climate_data(location_id: str, start_year: int, end_year: int) -> pd.DataFrame:<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;'''Returns DataFrame with ['year', 'month', 'date', 'T2M', 'PRECTOTCORR']'''
                </div>
                <div style="margin-top: 1rem; font-size: 0.85rem; color: #CBD5E1;">
                    <strong>Current Backend Status:</strong> 
                    <span style="color: {'#FBBF24' if is_demo else '#34D399'};">{data_res.status_message}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("**Active Observation Dataset Preview**")
        st.dataframe(
            filtered_df[["year", "month", "T2M", "PRECTOTCORR"]].head(24),
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
