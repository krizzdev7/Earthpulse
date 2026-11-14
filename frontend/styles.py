"""Custom CSS and styling definitions for the EARTHPULSE dashboard.
Provides a modern, scientific dark-theme aesthetic with glassmorphism and NASA accents.
"""

import streamlit as st


def apply_custom_styles():
    """Injects custom CSS to give EARTHPULSE a sleek, modern scientific appearance."""
    custom_css = """
    <style>
    /* Google Fonts import */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    /* Global Typography & Background Adjustments */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    code, pre, .font-mono {
        font-family: 'JetBrains Mono', monospace;
    }

    /* Main container clean spacing */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2.5rem !important;
        max-width: 1400px;
    }

    /* Card Containers */
    .ep-metric-card {
        background: linear-gradient(135deg, rgba(19, 28, 46, 0.8) 0%, rgba(15, 23, 38, 0.95) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1.25rem 1.2rem;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
        backdrop-filter: blur(8px);
        transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
        position: relative;
        overflow: hidden;
    }

    .ep-metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(0, 210, 255, 0.3);
        box-shadow: 0 12px 28px rgba(0, 210, 255, 0.1);
    }

    .ep-metric-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #00D2FF 0%, #3a7bd5 100%);
        opacity: 0.8;
    }

    .ep-metric-card.temp::before {
        background: linear-gradient(90deg, #FF6B6B 0%, #FFA07A 100%);
    }

    .ep-metric-card.precip::before {
        background: linear-gradient(90deg, #00E676 0%, #00B0FF 100%);
    }

    .ep-metric-card.anomaly::before {
        background: linear-gradient(90deg, #FFD166 0%, #F77F00 100%);
    }

    .ep-card-title {
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #94A3B8;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }

    .ep-card-value {
        font-size: 1.9rem;
        font-weight: 800;
        color: #F8FAFC;
        line-height: 1.2;
        letter-spacing: -0.02em;
        margin-bottom: 0.35rem;
    }

    .ep-card-value .unit {
        font-size: 1rem;
        font-weight: 500;
        color: #94A3B8;
        margin-left: 0.2rem;
    }

    .ep-card-subtext {
        font-size: 0.82rem;
        color: #94A3B8;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }

    /* Badges */
    .ep-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.22rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }

    .ep-badge-nasa {
        background: rgba(0, 210, 255, 0.12);
        color: #00D2FF;
        border: 1px solid rgba(0, 210, 255, 0.3);
    }

    .ep-badge-demo {
        background: rgba(245, 158, 11, 0.15);
        color: #FBBF24;
        border: 1px solid rgba(245, 158, 11, 0.35);
    }

    .ep-badge-live {
        background: rgba(16, 185, 129, 0.15);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.35);
    }

    /* Demo Mode Banner */
    .ep-demo-banner {
        background: linear-gradient(90deg, rgba(30, 27, 20, 0.9) 0%, rgba(38, 28, 18, 0.9) 100%);
        border: 1px solid rgba(245, 158, 11, 0.4);
        border-left: 4px solid #F59E0B;
        border-radius: 8px;
        padding: 0.85rem 1.2rem;
        margin-bottom: 1.5rem;
        color: #FEF3C7;
        font-size: 0.88rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 4px 16px rgba(245, 158, 11, 0.08);
    }

    .ep-demo-banner strong {
        color: #FBBF24;
        font-weight: 700;
    }

    /* Header Container */
    .ep-header-container {
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 1.2rem;
        margin-bottom: 1.5rem;
    }

    .ep-title {
        font-size: 2.3rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        background: linear-gradient(90deg, #FFFFFF 0%, #00D2FF 70%, #90CAF9 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        line-height: 1.2;
    }

    .ep-subtitle {
        font-size: 1rem;
        color: #94A3B8;
        font-weight: 500;
        margin-top: 0.25rem;
        margin-bottom: 0.6rem;
    }

    /* Sidebar Clean Styling */
    section[data-testid="stSidebar"] {
        background-color: #0E1524 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.07) !important;
    }

    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stSlider label {
        color: #CBD5E1 !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
    }

    /* Scientific Section Containers */
    .ep-section-box {
        background: rgba(19, 28, 46, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1.5rem;
    }

    .ep-section-header {
        font-size: 1.15rem;
        font-weight: 700;
        color: #F1F5F9;
        margin-bottom: 0.8rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* Plotly Chart Container */
    .stPlotlyChart {
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.06);
        background: #0E1626;
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)
