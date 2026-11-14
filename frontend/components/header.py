"""Header and branding component for EARTHPULSE.
Displays NASA Space Apps Challenge branding, mission description, and active data mode banner.
"""

import streamlit as st


def render_header(is_demo: bool, source_label: str):
    """Renders the top branding header and prototype/demo warning banner when applicable."""
    header_html = f"""
    <div class="ep-header-container">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 1rem;">
            <div>
                <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.35rem;">
                    <span style="font-size: 1.8rem;">🌍</span>
                    <h1 class="ep-title" style="display: inline-block;">EARTHPULSE</h1>
                    <span class="ep-badge ep-badge-nasa">NASA Space Apps 2026</span>
                </div>
                <div class="ep-subtitle">NASA Earth System Trend Analyzer &bull; Regional Climate Dynamics</div>
            </div>
            <div style="text-align: right; margin-top: 0.2rem;">
                <span class="ep-badge {'ep-badge-demo' if is_demo else 'ep-badge-live'}">
                    {'● PROTOTYPE / DEMO MODE' if is_demo else '● LIVE NASA DATA'}
                </span>
                <div style="font-size: 0.76rem; color: #64748B; margin-top: 0.35rem;">
                    Source: <strong style="color: {'#FBBF24' if is_demo else '#34D399'};">{source_label}</strong>
                </div>
            </div>
        </div>
        <p style="color: #94A3B8; font-size: 0.92rem; line-height: 1.5; margin-top: 0.6rem; margin-bottom: 0;">
            EARTHPULSE provides high-resolution temporal analysis of Earth system parameters derived from 
            NASA satellite observations and assimilation models (NASA POWER). Initially evaluating regional temperature 
            (<strong>T2M</strong>) and precipitation (<strong>PRECTOTCORR</strong>) dynamics across Kerala, India.
        </p>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

    # If backend data is unavailable, clearly label the dashboard as a prototype
    if is_demo:
        demo_banner_html = """
        <div class="ep-demo-banner">
            <div>
                <strong>⚠️ DEMONSTRATION PROTOTYPE:</strong> 
                The backend data service (<code>data_service.py</code>) is currently unpopulated. 
                Displaying synthetic demonstration values for UI and visualization testing.
                <strong>Do not cite or use these values as actual NASA observations.</strong>
            </div>
            <div style="margin-left: 1rem; font-size: 0.78rem; opacity: 0.85; white-space: nowrap;">
                Status: Awaiting Backend API
            </div>
        </div>
        """
        st.markdown(demo_banner_html, unsafe_allow_html=True)
