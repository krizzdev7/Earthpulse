"""Plotly chart visualizations for EARTHPULSE.
Provides interactive, dark-themed visualizations for T2M (temperature) and PRECTOTCORR (precipitation).
"""

from typing import Dict, Any
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st


# Dark scientific layout template config
DARK_THEME_BASE = dict(
    paper_bgcolor="rgba(14, 22, 38, 0.95)",
    plot_bgcolor="rgba(11, 15, 25, 0.95)",
    font=dict(color="#CBD5E1", family="Plus Jakarta Sans, sans-serif", size=12),
    margin=dict(l=55, r=35, t=55, b=45),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        font=dict(size=11, color="#94A3B8"),
        bgcolor="rgba(0,0,0,0)"
    ),
)


def _apply_dark_axes(fig: go.Figure):
    """Applies consistent dark scientific gridlines and fonts to all axes."""
    fig.update_xaxes(
        gridcolor="rgba(255, 255, 255, 0.07)",
        showline=True,
        linecolor="rgba(255, 255, 255, 0.15)",
        tickfont=dict(color="#94A3B8"),
    )
    fig.update_yaxes(
        gridcolor="rgba(255, 255, 255, 0.07)",
        showline=True,
        linecolor="rgba(255, 255, 255, 0.15)",
        tickfont=dict(color="#94A3B8"),
    )


def render_temperature_charts(df: pd.DataFrame, baseline_stats: Dict[str, float], is_demo: bool):
    """Renders interactive temperature (T2M) multi-decadal time series and rolling trends."""
    source_tag = "[DEMO]" if is_demo else "[NASA POWER]"

    # Prepare rolling 12-month average for trend detection
    df_sorted = df.sort_values("date").copy()
    df_sorted["T2M_Rolling12"] = df_sorted["T2M"].rolling(window=12, min_periods=6).mean()

    fig = go.Figure()

    # Raw monthly values (subtle line with dots)
    fig.add_trace(go.Scatter(
        x=df_sorted["date"],
        y=df_sorted["T2M"],
        mode="lines",
        name=f"Monthly T2M {source_tag}",
        line=dict(color="rgba(0, 210, 255, 0.4)", width=1),
        hovertemplate="<b>Date:</b> %{x|%b %Y}<br><b>T2M:</b> %{y:.2f} °C<extra></extra>",
    ))

    # 12-month moving average (bold highlight line)
    fig.add_trace(go.Scatter(
        x=df_sorted["date"],
        y=df_sorted["T2M_Rolling12"],
        mode="lines",
        name="12-Month Moving Average",
        line=dict(color="#FF6B6B", width=2.5),
        hovertemplate="<b>12-Month Mean:</b> %{y:.2f} °C<extra></extra>",
    ))

    # Climatological baseline reference line
    b_mean = baseline_stats["baseline_t2m_mean"]
    b_period = baseline_stats["baseline_period"]
    fig.add_hline(
        y=b_mean,
        line_dash="dash",
        line_color="rgba(255, 209, 102, 0.7)",
        annotation_text=f"Baseline Mean ({b_period}): {b_mean:.2f} °C",
        annotation_position="bottom right",
        annotation_font_color="#FFD166",
        annotation_font_size=10,
    )

    fig.update_layout(
        title=dict(
            text=f"Surface Air Temperature Dynamics (T2M) — {source_tag}",
            font=dict(size=15, color="#F8FAFC", family="Plus Jakarta Sans"),
            x=0.01,
            y=0.96
        ),
        xaxis_title="Timeline",
        yaxis_title="Temperature at 2m (°C)",
        hovermode="x unified",
        **DARK_THEME_BASE
    )
    _apply_dark_axes(fig)

    st.plotly_chart(fig, use_container_width=True)


def render_precipitation_charts(df: pd.DataFrame, baseline_stats: Dict[str, float], is_demo: bool):
    """Renders interactive precipitation (PRECTOTCORR) dynamics and annual cumulative distributions."""
    source_tag = "[DEMO]" if is_demo else "[NASA POWER]"

    # Subplots: Top = Monthly rainfall timeline; Bottom = Annual cumulative rainfall
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=False,
        vertical_spacing=0.15,
        subplot_titles=(
            f"Monthly Precipitation Time Series (PRECTOTCORR) — {source_tag}",
            f"Annual Cumulative Precipitation (mm/year) — {source_tag}"
        )
    )

    df_sorted = df.sort_values("date").copy()

    # 1. Monthly precipitation bar chart with gradient fill
    fig.add_trace(
        go.Bar(
            x=df_sorted["date"],
            y=df_sorted["PRECTOTCORR"],
            name=f"Monthly Rainfall (mm)",
            marker=dict(
                color=df_sorted["PRECTOTCORR"],
                colorscale=[[0, "#0E3A53"], [0.4, "#00B0FF"], [1.0, "#00E676"]],
                showscale=False
            ),
            hovertemplate="<b>Date:</b> %{x|%b %Y}<br><b>Rainfall:</b> %{y:,.1f} mm<extra></extra>",
        ),
        row=1,
        col=1
    )

    # 2. Annual Cumulative Totals
    annual_df = df_sorted.groupby("year")["PRECTOTCORR"].sum().reset_index()
    baseline_annual = baseline_stats["baseline_annual_precip"]

    fig.add_trace(
        go.Bar(
            x=annual_df["year"],
            y=annual_df["PRECTOTCORR"],
            name="Annual Total (mm)",
            marker=dict(
                color=["#00E676" if val >= baseline_annual else "#F59E0B" for val in annual_df["PRECTOTCORR"]],
            ),
            hovertemplate="<b>Year:</b> %{x}<br><b>Annual Rainfall:</b> %{y:,.0f} mm<extra></extra>",
        ),
        row=2,
        col=1
    )

    # Baseline reference on annual chart
    fig.add_hline(
        y=baseline_annual,
        line_dash="dash",
        line_color="#00D2FF",
        annotation_text=f"Baseline Annual: {baseline_annual:,.0f} mm",
        annotation_position="top right",
        annotation_font_color="#00D2FF",
        annotation_font_size=10,
        row=2,
        col=1
    )

    fig.update_layout(
        height=620,
        showlegend=False,
        **DARK_THEME_BASE
    )
    _apply_dark_axes(fig)
    fig.update_yaxes(title_text="Rainfall (mm/mo)", row=1, col=1)
    fig.update_yaxes(title_text="Annual (mm/yr)", row=2, col=1)
    fig.update_xaxes(title_text="Date", row=1, col=1)
    fig.update_xaxes(title_text="Year", row=2, col=1)

    st.plotly_chart(fig, use_container_width=True)


def render_climatology_cycle_chart(df: pd.DataFrame, is_demo: bool):
    """Renders the mean annual climatological cycle (January through December).

    Highlights seasonal phenomena such as Kerala's Southwest (Jun-Aug) and Northeast (Oct-Nov) monsoons.
    """
    source_tag = "[DEMO]" if is_demo else "[NASA POWER]"

    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    monthly_cycle = df.groupby("month").agg({
        "T2M": "mean",
        "PRECTOTCORR": "mean"
    }).reindex(range(1, 13)).reset_index()
    monthly_cycle["Month_Name"] = month_names

    # Dual axis plot: Rainfall on left bar axis, Temperature on right line axis
    fig = go.Figure()

    # Rainfall bars
    fig.add_trace(go.Bar(
        x=monthly_cycle["Month_Name"],
        y=monthly_cycle["PRECTOTCORR"],
        name="Mean Precipitation (mm)",
        yaxis="y",
        marker=dict(color="rgba(0, 210, 255, 0.65)"),
        hovertemplate="<b>%{x}:</b> %{y:.1f} mm<extra></extra>",
    ))

    # Temperature line
    fig.add_trace(go.Scatter(
        x=monthly_cycle["Month_Name"],
        y=monthly_cycle["T2M"],
        name="Mean Air Temp (°C)",
        yaxis="y2",
        mode="lines+markers",
        line=dict(color="#FF6B6B", width=3),
        marker=dict(size=7, color="#FFA07A"),
        hovertemplate="<b>%{x}:</b> %{y:.2f} °C<extra></extra>",
    ))

    fig.update_layout(
        title=dict(
            text=f"Mean Climatological Annual Cycle (Dual-Axis) — {source_tag}",
            font=dict(size=14, color="#F8FAFC", family="Plus Jakarta Sans"),
            x=0.01,
            y=0.96
        ),
        xaxis=dict(
            title="Month",
            gridcolor="rgba(255, 255, 255, 0.07)",
            tickfont=dict(color="#94A3B8")
        ),
        yaxis=dict(
            title=dict(text="Mean Precipitation (mm)", font=dict(color="#00D2FF")),
            tickfont=dict(color="#00D2FF"),
            gridcolor="rgba(255, 255, 255, 0.07)",
        ),
        yaxis2=dict(
            title=dict(text="Mean Temperature (°C)", font=dict(color="#FF6B6B")),
            tickfont=dict(color="#FF6B6B"),
            overlaying="y",
            side="right",
            showgrid=False
        ),
        **DARK_THEME_BASE
    )

    st.plotly_chart(fig, use_container_width=True)
