"""
Job Search Analytics Dashboard
--------------------------------
A Power BI / Tableau-style interactive dashboard, built in Python, that
analyzes a fresher tech job search: application funnel, response times,
skill-gap frequency, and role/location trends.

Run locally:
    pip install -r requirements.txt
    streamlit run app.py
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Job Search Analytics Dashboard",
    page_icon="📊",
    layout="wide",
)

DATA_PATH = Path(__file__).parent / "data" / "applications.csv"

STAGE_ORDER = [
    "Applied",
    "Online Assessment",
    "Technical Interview",
    "HR Interview",
    "Offer",
]

def inject_custom_css():
    """Inject custom CSS rules for metric cards and modern styling."""
    st.markdown(
        """
        <style>
        .stMetric {
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        }
        .stMetric label {
            font-weight: 600;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data
def load_data() -> pd.DataFrame:
    """Load application records from CSV file with parsed datetime columns."""
    df = pd.read_csv(DATA_PATH, parse_dates=["applied_on"])
    return df



def filter_applications(
    df: pd.DataFrame,
    roles: List[str],
    locations: List[str],
    remote_only: bool = False,
    date_range: Optional[Tuple[pd.Timestamp, pd.Timestamp]] = None,
) -> pd.DataFrame:
    """Filter job applications DataFrame based on role, location, remote flag, and date range."""
    filtered = df[df["role_type"].isin(roles) & df["location"].isin(locations)]
    if remote_only:
        filtered = filtered[filtered["remote_option"] == True]
    if date_range and len(date_range) == 2:
        start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        filtered = filtered[(filtered["applied_on"] >= start_date) & (filtered["applied_on"] <= end_date)]
    return filtered


def calculate_kpis(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate key performance indicators from filtered applications."""
    total_apps = len(df)
    if total_apps == 0:
        return {
            "total_apps": 0,
            "response_rate": 0.0,
            "interviews": 0,
            "offers": 0,
            "avg_response_days": float("nan"),
        }

    responded = df[~df["stage"].isin(["Applied"])].shape[0]
    response_rate = (responded / total_apps) * 100
    interviews = df[df["stage"].isin(["Technical Interview", "HR Interview", "Offer"])].shape[0]
    offers = df[df["stage"] == "Offer"].shape[0]
    avg_response_days = df["days_to_response"].dropna().mean()

    return {
        "total_apps": total_apps,
        "response_rate": response_rate,
        "interviews": interviews,
        "offers": offers,
        "avg_response_days": avg_response_days,
    }


def funnel_counts(df: pd.DataFrame) -> pd.DataFrame:
    """Count applications that reached AT LEAST each funnel stage."""
    reached = {"Applied": len(df)}
    progression = STAGE_ORDER[1:]  # stages after Applied
    stage_rank = {s: i for i, s in enumerate(STAGE_ORDER)}
    for s in progression:
        count = (df["stage"].map(lambda x: stage_rank.get(x, -1)) >= stage_rank[s]).sum()
        reached[s] = count
    return pd.DataFrame({"stage": list(reached.keys()), "count": list(reached.values())})


def calculate_company_response_rates(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate response rate percentage grouped by company organization type."""
    if df.empty:
        return pd.DataFrame(columns=["org_type", "response_rate"])
    records = []
    for org_type, group in df.groupby("org_type"):
        rate = (~group["stage"].isin(["Applied"])).mean() * 100
        records.append({"org_type": org_type, "response_rate": rate})
    return pd.DataFrame(records)


def calculate_salary_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate mean and median estimated CTC (in LPA) grouped by role type."""
    if df.empty or "estimated_ctc_lpa" not in df.columns:
        return pd.DataFrame(columns=["role_type", "mean_ctc", "median_ctc"])
    grouped = df.groupby("role_type")["estimated_ctc_lpa"].agg(
        mean_ctc="mean", median_ctc="median"
    ).reset_index()
    return grouped.round(2)



def main():
    inject_custom_css()
    df = load_data()


    st.title("📊 Job Search Analytics Dashboard")
    st.caption(
        "Applying data analytics to my own job search — built with Python, "
        "Pandas, and Plotly. Data is synthetic (randomly generated) for "
        "demo/portfolio purposes."
    )

    # ---------------- Sidebar filters ----------------
    st.sidebar.header("Filters")
    role_filter = st.sidebar.multiselect(
        "Role type", sorted(df["role_type"].unique()), default=list(df["role_type"].unique())
    )
    location_filter = st.sidebar.multiselect(
        "Location", sorted(df["location"].unique()), default=list(df["location"].unique())
    )
    remote_only = st.sidebar.checkbox("Remote only", value=False)

    min_date = df["applied_on"].min().date()
    max_date = df["applied_on"].max().date()
    date_range = st.sidebar.date_input(
        "Application Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    filtered = filter_applications(
        df,
        roles=role_filter,
        locations=location_filter,
        remote_only=remote_only,
        date_range=date_range if isinstance(date_range, (list, tuple)) and len(date_range) == 2 else None,
    )

    if filtered.empty:
        st.warning("No applications match the selected filters.")
        return

    # ---------------- KPI row ----------------
    kpis = calculate_kpis(filtered)
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total Applications", kpis["total_apps"])
    k2.metric("Response Rate", f"{kpis['response_rate']:.0f}%")
    k3.metric("Interview Stage Reached", kpis["interviews"])
    k4.metric("Offers", kpis["offers"])
    avg_resp = kpis["avg_response_days"]
    k5.metric("Avg. Response Time", f"{avg_resp:.0f} days" if pd.notna(avg_resp) else "—")

    st.divider()

    # ---------------- Row 1: Funnel + Stage breakdown ----------------
    c1, c2 = st.columns([1.2, 1])

    with c1:
        st.subheader("Application Funnel")
        funnel_df = funnel_counts(filtered)
        fig = go.Figure(
            go.Funnel(
                y=funnel_df["stage"],
                x=funnel_df["count"],
                textinfo="value+percent initial",
                marker={"color": ["#4C78A8", "#72B7B2", "#54A24B", "#EECA3B", "#E45756"]},
            )
        )
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=380)
        st.plotly_chart(fig, width="stretch")

    with c2:
        st.subheader("Outcome Breakdown")
        stage_counts = filtered["stage"].value_counts().reset_index()
        stage_counts.columns = ["stage", "count"]
        fig2 = px.pie(stage_counts, names="stage", values="count", hole=0.45)
        fig2.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=380, showlegend=True)
        st.plotly_chart(fig2, width="stretch")

    # ---------------- Row 2: Timeline + Role type ----------------
    c3, c4 = st.columns(2)

    with c3:
        st.subheader("Applications Over Time")
        timeline = filtered.groupby(filtered["applied_on"].dt.to_period("W")).size().reset_index(name="count")
        timeline["applied_on"] = timeline["applied_on"].dt.start_time
        fig3 = px.bar(timeline, x="applied_on", y="count", labels={"applied_on": "Week", "count": "Applications"})
        fig3.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=350)
        st.plotly_chart(fig3, width="stretch")

    with c4:
        st.subheader("Applications by Role Type")
        role_counts = filtered["role_type"].value_counts().reset_index()
        role_counts.columns = ["role_type", "count"]
        fig4 = px.bar(role_counts, x="count", y="role_type", orientation="h", color="role_type")
        fig4.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=350, showlegend=False)
        st.plotly_chart(fig4, width="stretch")

    # ---------------- Row 3: Skill gaps + Company type ----------------
    c5, c6 = st.columns(2)

    with c5:
        st.subheader("Most Frequently Flagged Skill Gaps")
        gaps = filtered["flagged_skill_gap"].dropna()
        if not gaps.empty:
            gap_counts = gaps.value_counts().reset_index()
            gap_counts.columns = ["skill", "count"]
            fig5 = px.bar(
                gap_counts.head(10),
                x="count",
                y="skill",
                orientation="h",
                color="count",
                color_continuous_scale="Reds",
            )
            fig5.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=350, coloraxis_showscale=False)
            st.plotly_chart(fig5, width="stretch")
        else:
            st.info("No skill gaps flagged for the current filter selection.")

    with c6:
        st.subheader("Response Rate by Company Type")
        comp = calculate_company_response_rates(filtered)
        fig6 = px.bar(
            comp,
            x="org_type",
            y="response_rate",
            color="org_type",
            labels={"response_rate": "Response Rate (%)", "org_type": "Company Type"},
        )
        fig6.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=350, showlegend=False)
        st.plotly_chart(fig6, width="stretch")

    # ---------------- Row 4: Salary (CTC) Expectations ----------------
    if "estimated_ctc_lpa" in filtered.columns:
        st.subheader("Estimated CTC Range (LPA) by Role Type")
        salary_df = calculate_salary_stats(filtered)
        fig7 = px.bar(
            salary_df,
            x="role_type",
            y="mean_ctc",
            color="role_type",
            text="mean_ctc",
            labels={"mean_ctc": "Average CTC (LPA)", "role_type": "Role Type"},
        )
        fig7.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=350, showlegend=False)
        st.plotly_chart(fig7, width="stretch")


    st.divider()

    # ---------------- Data table ----------------
    with st.expander("📋 View raw application data"):
        sorted_df = filtered.sort_values("applied_on", ascending=False)
        st.dataframe(
            sorted_df,
            width="stretch",
            hide_index=True,
        )
        csv_data = sorted_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Filtered Data as CSV",
            data=csv_data,
            file_name="filtered_job_applications.csv",
            mime="text/csv",
        )

    st.caption(
        "Built by Vivek J Poojary · [Portfolio](https://vivekjpoojary.vercel.app) · "
        "[GitHub](https://github.com/Vivekjpoojary) · "
        "[LinkedIn](https://linkedin.com/in/vivekjpoojary)"
    )


if __name__ == "__main__":
    main()
