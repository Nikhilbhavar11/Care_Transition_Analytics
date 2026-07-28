import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="UAC Care Pipeline Analytics",
    page_icon="🏥",
    layout="wide"
)

# ── Load data ─────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv('data/processed_uac_data.csv', parse_dates=['date'])
    monthly = pd.read_csv('data/monthly_kpis.csv')
    return df, monthly

df, monthly_kpis = load_data()

# ── Sidebar filters ───────────────────────────────────────────
st.sidebar.title("🔧 Filters")
min_date, max_date = df['date'].min(), df['date'].max()
date_range = st.sidebar.date_input(
    "Select Date Range",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

regime_filter = st.sidebar.multiselect(
    "Filter by Regime",
    options=df['regime'].unique().tolist(),
    default=df['regime'].unique().tolist()
)

# Apply filters
mask = (
    (df['date'] >= pd.Timestamp(date_range[0])) &
    (df['date'] <= pd.Timestamp(date_range[1])) &
    (df['regime'].isin(regime_filter))
)
filtered_df = df[mask]

# ── Header ────────────────────────────────────────────────────
st.title("🏥 UAC Care Transition Efficiency & Placement Outcome Analytics")
st.markdown("**U.S. Department of Health and Human Services — Unaccompanied Children Program**")
st.markdown("---")

# ── KPI Metric Cards ──────────────────────────────────────────
st.subheader("📊 Key Performance Indicators")
col1, col2, col3, col4, col5 = st.columns(5)

avg_transfer = filtered_df['transfer_efficiency_ratio'].mean()
avg_discharge = filtered_df['discharge_effectiveness'].mean()
avg_throughput = filtered_df['pipeline_throughput'].mean()
avg_backlog = filtered_df['backlog_accumulation_rate'].mean()
avg_stability = filtered_df['outcome_stability_score_inverted'].mean()

col1.metric("Transfer Efficiency Ratio", f"{avg_transfer:.3f}",
            help="Transfers ÷ CBP Custody. Higher = faster CBP→HHS movement.")
col2.metric("Discharge Effectiveness", f"{avg_discharge:.4f}",
            help="Discharges ÷ HHS Care. Higher = more reunifications per day.")
col3.metric("Pipeline Throughput", f"{avg_throughput:.2f}x",
            help="Total exits ÷ Total entries. >1 = system clearing cases.")
col4.metric("Backlog Accumulation Rate", f"{avg_backlog:.1f}",
            help="7-day rolling avg net flow. Negative = backlog reducing.")
col5.metric("Outcome Stability Score", f"{avg_stability:.3f}",
            help="Higher = more consistent discharge outcomes (0-1 scale).")

st.markdown("---")

# ── Care Pipeline Flow ────────────────────────────────────────
st.subheader("🔄 Care Pipeline Flow Over Time")
fig_pipeline = go.Figure()
fig_pipeline.add_trace(go.Scatter(x=filtered_df['date'], y=filtered_df['cbp_custody'],
    name='CBP Custody', line=dict(color='orange')))
fig_pipeline.add_trace(go.Scatter(x=filtered_df['date'], y=filtered_df['hhs_care'],
    name='HHS Care Load', line=dict(color='steelblue')))
fig_pipeline.add_trace(go.Scatter(x=filtered_df['date'], y=filtered_df['hhs_discharged'],
    name='Daily Discharges', line=dict(color='green')))
fig_pipeline.add_vline(x='2025-02-01', line_dash='dash', line_color='red',
    annotation_text='Policy Shift', annotation_position='top left')
fig_pipeline.update_layout(height=400, hovermode='x unified',
    legend=dict(orientation='h', yanchor='bottom', y=1.02))
st.plotly_chart(fig_pipeline, use_container_width=True)

# ── KPI Trend Charts ──────────────────────────────────────────
st.subheader("📈 Monthly KPI Trends")
kpi_choice = st.selectbox("Select KPI to visualize:", [
    'avg_transfer_efficiency', 'avg_discharge_effectiveness',
    'avg_pipeline_throughput', 'avg_backlog_rate', 'avg_stability'
], format_func=lambda x: {
    'avg_transfer_efficiency': 'Transfer Efficiency Ratio',
    'avg_discharge_effectiveness': 'Discharge Effectiveness',
    'avg_pipeline_throughput': 'Pipeline Throughput',
    'avg_backlog_rate': 'Backlog Accumulation Rate',
    'avg_stability': 'Outcome Stability Score'
}[x])

fig_kpi = px.line(monthly_kpis, x='month', y=kpi_choice, markers=True,
    title=f"Monthly Trend: {kpi_choice.replace('avg_', '').replace('_', ' ').title()}")
fig_kpi.update_xaxes(type='category')  # ← yeh line add karo
fig_kpi.add_vline(x='2025-02', line_dash='dash', line_color='red',
    annotation_text='Policy Shift')
fig_kpi.update_layout(height=350)
st.plotly_chart(fig_kpi, use_container_width=True)

# ── Bottleneck & Backlog ───────────────────────────────────────
st.subheader("⚠️ Backlog Accumulation & Bottleneck Detection")
col_left, col_right = st.columns([2, 1])

with col_left:
    fig_backlog = px.line(filtered_df, x='date', y='backlog_accumulation_rate',
        title='Backlog Accumulation Rate (7-day rolling avg)',
        color_discrete_sequence=['darkred'])
    fig_backlog.add_hline(y=0, line_dash='dot', line_color='black')
    fig_backlog.add_vline(x='2025-02-01', line_dash='dash', line_color='red')
    fig_backlog.update_layout(height=350)
    st.plotly_chart(fig_backlog, use_container_width=True)

with col_right:
    st.markdown("#### 🚨 Detected Bottleneck Periods")
    df['is_backlog_day'] = df['net_flow'] > 0
    df['streak_id'] = (df['is_backlog_day'] != df['is_backlog_day'].shift()).cumsum()
    streaks = df[df['is_backlog_day']].groupby('streak_id').agg(
        start_date=('date', 'first'),
        end_date=('date', 'last'),
        length=('date', 'count'),
        total_excess=('net_flow', 'sum')
    )
    bottlenecks = streaks[streaks['length'] >= 5].sort_values('length', ascending=False)
    if len(bottlenecks) > 0:
        st.dataframe(bottlenecks.reset_index(drop=True), use_container_width=True)
        st.warning(f"⚠️ {len(bottlenecks)} sustained bottleneck period(s) detected (5+ days)")
    else:
        st.success("✅ No sustained bottleneck periods detected in selected range")

# ── Weekday Pattern ───────────────────────────────────────────
st.subheader("📅 Discharge Effectiveness by Day of Week")
weekday_data = filtered_df.groupby('day_of_week')['discharge_effectiveness'].mean().reindex(
    ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
).reset_index()
fig_weekday = px.bar(weekday_data, x='day_of_week', y='discharge_effectiveness',
    color='discharge_effectiveness', color_continuous_scale='Blues',
    title='Average Discharge Effectiveness by Day of Week')
fig_weekday.update_layout(height=350)
st.plotly_chart(fig_weekday, use_container_width=True)

# ── Outcome Stability ─────────────────────────────────────────
st.subheader("🎯 Outcome Stability Analysis")
fig_stability = px.line(filtered_df, x='date', y='outcome_stability_score_inverted',
    title='Outcome Stability Score Over Time (higher = more stable)',
    color_discrete_sequence=['purple'])
fig_stability.add_vline(x='2025-02-01', line_dash='dash', line_color='red',
    annotation_text='Policy Shift')
fig_stability.add_hrect(y0=0.8, y1=1.0, fillcolor='green', opacity=0.05,
    annotation_text='Stable Zone')
fig_stability.add_hrect(y0=0, y1=0.7, fillcolor='red', opacity=0.05,
    annotation_text='Volatile Zone')
fig_stability.update_layout(height=380)
st.plotly_chart(fig_stability, use_container_width=True)

# ── Footer ────────────────────────────────────────────────────
st.markdown("---")
st.caption("Data Source: U.S. Department of Health and Human Services — UAC Program | "
           "Analysis by: Care Transition Analytics | Built with Streamlit + Plotly")