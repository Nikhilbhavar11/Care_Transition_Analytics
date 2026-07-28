import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

st.set_page_config(
    page_title="UAC Care Pipeline Analytics",
    page_icon="🏥",
    layout="wide"
)

st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    .metric-label { font-size: 0.75rem !important; }
    .stMetric { background-color: #1e1e2e; border-radius: 8px; padding: 12px; }
    </style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    df = pd.read_csv('data/processed_uac_data.csv', parse_dates=['date'])
    monthly = pd.read_csv('data/monthly_kpis.csv')
    return df, monthly

df, monthly_kpis = load_data()

st.sidebar.title("Filters")
min_date, max_date = df['date'].min(), df['date'].max()
date_range = st.sidebar.date_input(
    "Date Range",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

regime_filter = st.sidebar.multiselect(
    "Policy Regime",
    options=df['regime'].unique().tolist(),
    default=df['regime'].unique().tolist(),
    format_func=lambda x: "Pre-2025 Shift" if x == "pre_2025_shift" else "Post-2025 Shift"
)

st.sidebar.markdown("---")
st.sidebar.markdown("**About**")
st.sidebar.markdown("This dashboard analyzes the U.S. HHS Unaccompanied Children Program care pipeline from Jan 2023 to Dec 2025, tracking transition efficiency and placement outcomes.")

if len(date_range) == 2:
    mask = (
        (df['date'] >= pd.Timestamp(date_range[0])) &
        (df['date'] <= pd.Timestamp(date_range[1])) &
        (df['regime'].isin(regime_filter))
    )
else:
    mask = df['regime'].isin(regime_filter)

filtered_df = df[mask]

st.title("UAC Care Transition Efficiency & Placement Outcome Analytics")
st.markdown("**U.S. Department of Health and Human Services — Unaccompanied Children Program**")
st.markdown("---")

if filtered_df.empty:
    st.warning("No data available for the selected filters. Please adjust the date range or regime selection.")
    st.stop()

st.subheader("Key Performance Indicators")

avg_transfer = filtered_df['transfer_efficiency_ratio'].mean()
avg_discharge = filtered_df['discharge_effectiveness'].mean()
avg_throughput = filtered_df['pipeline_throughput'].mean()
avg_backlog = filtered_df['backlog_accumulation_rate'].mean()
avg_stability = filtered_df['outcome_stability_score_inverted'].mean()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric(
    "Transfer Efficiency Ratio",
    f"{avg_transfer:.3f}",
    help="Transfers ÷ CBP Custody. Higher = faster CBP to HHS movement."
)
col2.metric(
    "Discharge Effectiveness",
    f"{avg_discharge:.4f}",
    help="Discharges ÷ HHS Care. Higher = more reunifications per day."
)
col3.metric(
    "Pipeline Throughput",
    f"{avg_throughput:.2f}x",
    help="Total exits ÷ Total entries. Above 1x means system is clearing cases."
)
col4.metric(
    "Backlog Accumulation Rate",
    f"{avg_backlog:.1f}",
    help="7-day rolling average net flow. Negative = backlog reducing."
)
col5.metric(
    "Outcome Stability Score",
    f"{avg_stability:.3f}",
    help="Higher = more consistent discharge outcomes. Scale: 0 to 1."
)

st.markdown("---")

st.subheader("Care Pipeline Flow Over Time")
fig_pipeline = go.Figure()
fig_pipeline.add_trace(go.Scatter(
    x=filtered_df['date'], y=filtered_df['cbp_custody'],
    name='CBP Custody', line=dict(color='#f4a261', width=1.2)
))
fig_pipeline.add_trace(go.Scatter(
    x=filtered_df['date'], y=filtered_df['hhs_care'],
    name='HHS Care Load', line=dict(color='#4895ef', width=1.5)
))
fig_pipeline.add_trace(go.Scatter(
    x=filtered_df['date'], y=filtered_df['hhs_discharged'],
    name='Daily Discharges', line=dict(color='#2dc653', width=1.2)
))
fig_pipeline.add_vline(
    x='2025-02-01',
    line_dash='dash',
    line_color='red',
    annotation_text='Policy Shift (Feb 2025)',
    annotation_position='top left',
    annotation_font_color='red'
)
fig_pipeline.update_layout(
    height=420,
    hovermode='x unified',
    legend=dict(orientation='h', yanchor='bottom', y=1.02),
    margin=dict(l=40, r=20, t=40, b=40),
    xaxis_title="Date",
    yaxis_title="Number of Children"
)
st.plotly_chart(fig_pipeline, use_container_width=True)

st.markdown("---")

st.subheader("Monthly KPI Trends")

kpi_label_map = {
    'avg_transfer_efficiency': 'Transfer Efficiency Ratio',
    'avg_discharge_effectiveness': 'Discharge Effectiveness',
    'avg_pipeline_throughput': 'Pipeline Throughput',
    'avg_backlog_rate': 'Backlog Accumulation Rate',
    'avg_stability': 'Outcome Stability Score'
}

kpi_choice = st.selectbox(
    "Select KPI to visualize:",
    options=list(kpi_label_map.keys()),
    format_func=lambda x: kpi_label_map[x]
)

fig_kpi = px.line(
    monthly_kpis,
    x='month',
    y=kpi_choice,
    markers=True,
    title=f"Monthly Trend — {kpi_label_map[kpi_choice]}"
)
fig_kpi.update_xaxes(type='category', tickangle=90)

months_list = monthly_kpis['month'].tolist()
if '2025-02' in months_list:
    shift_idx = months_list.index('2025-02')
    fig_kpi.add_shape(
        type='line',
        x0=shift_idx, x1=shift_idx,
        y0=0, y1=1,
        xref='x', yref='paper',
        line=dict(color='red', dash='dash', width=1.5)
    )
    fig_kpi.add_annotation(
        x=shift_idx, y=1,
        xref='x', yref='paper',
        text='Policy Shift',
        showarrow=False,
        yanchor='bottom',
        font=dict(color='red', size=11)
    )

fig_kpi.update_layout(
    height=380,
    margin=dict(l=40, r=20, t=50, b=80),
    xaxis_title="Month",
    yaxis_title=kpi_label_map[kpi_choice]
)
st.plotly_chart(fig_kpi, use_container_width=True)

st.markdown("---")

st.subheader("Backlog Accumulation & Bottleneck Detection")
col_left, col_right = st.columns([2, 1])

with col_left:
    fig_backlog = px.line(
        filtered_df,
        x='date',
        y='backlog_accumulation_rate',
        title='Backlog Accumulation Rate (7-day rolling average)',
        color_discrete_sequence=['#c1121f']
    )
    fig_backlog.add_hline(y=0, line_dash='dot', line_color='white', line_width=1)
    fig_backlog.add_vline(
        x='2025-02-01',
        line_dash='dash',
        line_color='red',
        annotation_text='Policy Shift',
        annotation_font_color='red'
    )
    fig_backlog.update_layout(
        height=380,
        xaxis_title="Date",
        yaxis_title="Net Flow (Children)",
        margin=dict(l=40, r=20, t=50, b=40)
    )
    st.plotly_chart(fig_backlog, use_container_width=True)

with col_right:
    st.markdown("#### Detected Bottleneck Periods")
    st.markdown("Periods of 5+ consecutive days where intake exceeded exits.")

    working_df = df.copy()
    working_df['is_backlog_day'] = working_df['net_flow'] > 0
    working_df['streak_id'] = (
        working_df['is_backlog_day'] != working_df['is_backlog_day'].shift()
    ).cumsum()

    streaks = working_df[working_df['is_backlog_day']].groupby('streak_id').agg(
        start_date=('date', 'first'),
        end_date=('date', 'last'),
        duration_days=('date', 'count'),
        total_excess_children=('net_flow', 'sum')
    )
    bottlenecks = streaks[streaks['duration_days'] >= 5].sort_values(
        'duration_days', ascending=False
    ).reset_index(drop=True)

    bottlenecks['start_date'] = pd.to_datetime(bottlenecks['start_date']).dt.strftime('%Y-%m-%d')
    bottlenecks['end_date'] = pd.to_datetime(bottlenecks['end_date']).dt.strftime('%Y-%m-%d')

    if len(bottlenecks) > 0:
        st.dataframe(bottlenecks, use_container_width=True, hide_index=True)
        st.warning(f"{len(bottlenecks)} sustained bottleneck period(s) detected (5+ consecutive days)")
    else:
        st.success("No sustained bottleneck periods detected in the selected date range.")

st.markdown("---")

st.subheader("Discharge Effectiveness by Day of Week")
weekday_data = (
    filtered_df.groupby('day_of_week')['discharge_effectiveness']
    .mean()
    .reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
    .reset_index()
)

fig_weekday = px.bar(
    weekday_data,
    x='day_of_week',
    y='discharge_effectiveness',
    color='discharge_effectiveness',
    color_continuous_scale='Blues',
    title='Average Discharge Effectiveness by Day of Week'
)
fig_weekday.update_layout(
    height=370,
    xaxis_title="Day of Week",
    yaxis_title="Discharge Effectiveness",
    margin=dict(l=40, r=20, t=50, b=40),
    coloraxis_showscale=False
)
st.plotly_chart(fig_weekday, use_container_width=True)

st.markdown("---")

st.subheader("Outcome Stability Analysis")
fig_stability = px.line(
    filtered_df,
    x='date',
    y='outcome_stability_score_inverted',
    title='Outcome Stability Score Over Time (higher = more stable)',
    color_discrete_sequence=['#9d4edd']
)
fig_stability.add_vline(
    x='2025-02-01',
    line_dash='dash',
    line_color='red',
    annotation_text='Policy Shift',
    annotation_font_color='red'
)
fig_stability.add_hrect(
    y0=0.8, y1=1.0,
    fillcolor='green', opacity=0.06,
    annotation_text='Stable Zone',
    annotation_position='top right',
    annotation_font_color='green'
)
fig_stability.add_hrect(
    y0=0, y1=0.7,
    fillcolor='red', opacity=0.06,
    annotation_text='Volatile Zone',
    annotation_position='bottom right',
    annotation_font_color='red'
)
fig_stability.update_layout(
    height=400,
    xaxis_title="Date",
    yaxis_title="Stability Score (0–1)",
    yaxis=dict(range=[0, 1.05]),
    margin=dict(l=40, r=20, t=50, b=40)
)
st.plotly_chart(fig_stability, use_container_width=True)

st.markdown("---")
st.caption(
    "Data Source: U.S. Department of Health and Human Services — UAC Program  |  "
    "Period: January 2023 – December 2025  |  Built with Streamlit & Plotly"
)