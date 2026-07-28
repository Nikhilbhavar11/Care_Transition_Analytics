# Care Transition Efficiency & Placement Outcome Analytics

## Project Overview
Analysis of the U.S. HHS Unaccompanied Children (UAC) Program care pipeline,
measuring transition efficiency, discharge effectiveness, and placement outcome
stability from January 2023 to December 2025.

## Project Structure

    Care_Transition_Analytics/
    ├── data/
    │   ├── HHS_Unaccompanied_Alien_Children_Program.csv
    │   ├── processed_uac_data.csv
    │   └── monthly_kpis.csv
    ├── notebooks/
    │   └── EDA_and_Analysis.ipynb
    ├── outputs/
    │   └── charts/
    ├── Reports/
    │   ├── research_paper.pdf
    │   └── executive_summary.pdf
    ├── app.py
    ├── requirements.txt
    └── README.md

## Setup & Installation

    pip install -r requirements.txt

## Running the Dashboard

    streamlit run app.py

## Key Findings

1. Structural Regime Shift (Feb 2025): All pipeline metrics dropped sharply
   following policy changes. CBP custody reduced by 90%, HHS care load fell
   from 8,000 to 2,000 children.

2. Transfer Efficiency Degraded: Pre-2025 average of 0.82 dropped to 0.35
   post-shift, indicating slower CBP to HHS transitions.

3. Discharge Effectiveness Collapsed: From 0.032 to 0.005, reunification
   rate fell by 85% post policy shift.

4. Outcome Stability Worsened: Despite lower caseload, discharge consistency
   dropped, suggesting operational fragility not just volume reduction.

5. Weekend Pattern: Saturday shows zero operations. Sunday shows highest
   discharge effectiveness due to catch-up processing.

## KPIs Tracked

| KPI | Description |
|-----|-------------|
| Transfer Efficiency Ratio | CBP to HHS transfer speed |
| Discharge Effectiveness | Daily reunification rate |
| Pipeline Throughput | Total exits divided by total entries |
| Backlog Accumulation Rate | 7-day rolling net flow |
| Outcome Stability Score | Consistency of placements |

## Data Source
U.S. Department of Health and Human Services — UAC Program Public Dataset

## Tools Used
- Python, Pandas, NumPy — data processing
- Matplotlib, Seaborn — static visualizations
- Plotly, Streamlit — interactive dashboard