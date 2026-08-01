"""
app.py

LineIQ — a small OEE (Overall Equipment Effectiveness) analytics
dashboard for manufacturing lines, built with Streamlit + pandas +
Plotly.

Run with: streamlit run app.py
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from oee import compute_oee_columns, weighted_average_oee
from data_generator import generate_production_log

WORLD_CLASS_OEE = 0.85

st.set_page_config(page_title="LineIQ — OEE Analytics", page_icon="📊", layout="wide")


@st.cache_data
def load_data():
    shifts_df, downtime_df = generate_production_log()
    shifts_df = compute_oee_columns(shifts_df)
    shifts_df["date"] = pd.to_datetime(shifts_df["date"])
    downtime_df["date"] = pd.to_datetime(downtime_df["date"])
    return shifts_df, downtime_df


shifts_df, downtime_df = load_data()

# ---------------------------------------------------------------- sidebar
st.sidebar.title("📊 LineIQ")
st.sidebar.caption("OEE analytics for manufacturing lines")

min_date, max_date = shifts_df["date"].min(), shifts_df["date"].max()
date_range = st.sidebar.date_input(
    "Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
else:
    start_date, end_date = min_date, max_date

all_lines = sorted(shifts_df["line_name"].unique())
selected_lines = st.sidebar.multiselect("Production lines", all_lines, default=all_lines)

all_shifts = ["MORNING", "AFTERNOON", "NIGHT"]
selected_shifts = st.sidebar.multiselect("Shifts", all_shifts, default=all_shifts)

st.sidebar.divider()
st.sidebar.caption(
    "Data is synthetic, generated on load with a fixed seed — this is a "
    "portfolio demo, not a real factory's numbers."
)

mask = (
    (shifts_df["date"] >= start_date)
    & (shifts_df["date"] <= end_date)
    & (shifts_df["line_name"].isin(selected_lines))
    & (shifts_df["shift"].isin(selected_shifts))
)
filtered = shifts_df[mask]

dt_mask = (
    (downtime_df["date"] >= start_date)
    & (downtime_df["date"] <= end_date)
    & (downtime_df["line_name"].isin(selected_lines))
    & (downtime_df["shift"].isin(selected_shifts))
)
filtered_downtime = downtime_df[dt_mask]

# ---------------------------------------------------------------- header
st.title("Production Efficiency (OEE) Dashboard")
st.caption(
    "OEE = Availability × Performance × Quality — the standard manufacturing "
    "metric for how much of a line's theoretical capacity is actually "
    "converted into good product."
)

if filtered.empty:
    st.warning("No data for the selected filters. Widen the date range or reselect lines/shifts.")
    st.stop()

metrics = weighted_average_oee(filtered)

# ---------------------------------------------------------------- KPI cards
col1, col2, col3, col4 = st.columns(4)


def kpi_card(col, label, value, help_text):
    pct = value * 100
    color = "🟢" if value >= WORLD_CLASS_OEE else ("🟡" if value >= 0.60 else "🔴")
    col.metric(label, f"{pct:.1f}%", help=help_text)
    col.caption(f"{color} vs. 85% world-class benchmark" if label == "OEE" else "")


kpi_card(col1, "OEE", metrics["oee"], "Availability × Performance × Quality")
kpi_card(col2, "Availability", metrics["availability"], "Run time ÷ planned production time")
kpi_card(col3, "Performance", metrics["performance"], "Actual output ÷ theoretical max output while running")
kpi_card(col4, "Quality", metrics["quality"], "Good units ÷ total units produced")

st.divider()

# ---------------------------------------------------------------- trend + comparison
left, right = st.columns([2, 1])

with left:
    st.subheader("OEE trend over time")
    daily = (
        filtered.groupby("date")
        .apply(lambda g: pd.Series(weighted_average_oee(g)))
        .reset_index()
    )
    fig = px.line(daily, x="date", y="oee", markers=True)
    fig.add_hline(y=WORLD_CLASS_OEE, line_dash="dash", line_color="green",
                   annotation_text="World-class (85%)")
    fig.update_yaxes(tickformat=".0%", range=[0, 1])
    fig.update_layout(height=350, margin=dict(t=10, b=10))
    st.plotly_chart(fig, width='stretch')

with right:
    st.subheader("OEE by line")
    by_line = (
        filtered.groupby("line_name")
        .apply(lambda g: pd.Series(weighted_average_oee(g)))
        .reset_index()
        .sort_values("oee", ascending=True)
    )
    fig2 = px.bar(by_line, x="oee", y="line_name", orientation="h")
    fig2.add_vline(x=WORLD_CLASS_OEE, line_dash="dash", line_color="green")
    fig2.update_xaxes(tickformat=".0%", range=[0, 1])
    fig2.update_layout(height=350, margin=dict(t=10, b=10), yaxis_title="", xaxis_title="OEE")
    st.plotly_chart(fig2, width='stretch')

st.divider()

# ---------------------------------------------------------------- pareto + shift comparison
left2, right2 = st.columns([2, 1])

with left2:
    st.subheader("Downtime by reason (Pareto)")
    st.caption("Where is lost time actually going? The classic 80/20 view of the 'six big losses'.")
    if filtered_downtime.empty:
        st.info("No downtime events in the selected filters.")
    else:
        by_reason = (
            filtered_downtime.groupby("reason")["minutes"].sum().sort_values(ascending=False).reset_index()
        )
        by_reason["cumulative_pct"] = by_reason["minutes"].cumsum() / by_reason["minutes"].sum()

        fig3 = go.Figure()
        fig3.add_bar(x=by_reason["reason"], y=by_reason["minutes"], name="Minutes lost")
        fig3.add_trace(go.Scatter(
            x=by_reason["reason"], y=by_reason["cumulative_pct"] * by_reason["minutes"].max(),
            name="Cumulative %", yaxis="y2", mode="lines+markers", line=dict(color="firebrick"),
        ))
        fig3.update_layout(
            height=350, margin=dict(t=10, b=10),
            yaxis=dict(title="Minutes lost"),
            yaxis2=dict(overlaying="y", side="right", range=[0, by_reason["minutes"].max()],
                        tickvals=[i * by_reason["minutes"].max() / 5 for i in range(6)],
                        ticktext=[f"{i*20}%" for i in range(6)], title="Cumulative %"),
        )
        st.plotly_chart(fig3, width='stretch')

with right2:
    st.subheader("OEE by shift")
    by_shift = (
        filtered.groupby("shift")
        .apply(lambda g: pd.Series(weighted_average_oee(g)))
        .reset_index()
    )
    fig4 = px.bar(by_shift, x="shift", y="oee")
    fig4.add_hline(y=WORLD_CLASS_OEE, line_dash="dash", line_color="green")
    fig4.update_yaxes(tickformat=".0%", range=[0, 1])
    fig4.update_layout(height=350, margin=dict(t=10, b=10), xaxis_title="", yaxis_title="OEE")
    st.plotly_chart(fig4, width='stretch')

st.divider()

# ---------------------------------------------------------------- raw data
with st.expander("Show underlying shift-level data"):
    st.dataframe(
        filtered[[
            "date", "line_name", "shift", "planned_minutes", "run_time_minutes",
            "total_units", "good_units", "defective_units",
            "availability", "performance", "quality", "oee",
        ]].sort_values("date", ascending=False),
        width='stretch',
    )
