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

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

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

REJECTED_STAGES = ["Rejected - No Response", "Rejected After Screening"]


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH, parse_dates=["applied_on"])
    return df


def funnel_counts(df: pd.DataFrame) -> pd.DataFrame:
    """Count applications that reached AT LEAST each funnel stage."""
    reached = {"Applied": len(df)}
    progression = STAGE_ORDER[1:]  # stages after Applied
    remaining = df[~df["stage"].isin(["Applied"] + REJECTED_STAGES)]
    # crude but effective: an application's stage tells us the furthest point reached
    stage_rank = {s: i for i, s in enumerate(STAGE_ORDER)}
    for s in progression:
        count = (df["stage"].map(lambda x: stage_rank.get(x, -1)) >= stage_rank[s]).sum()
        reached[s] = count
    return pd.DataFrame({"stage": list(reached.keys()), "count": list(reached.values())})


def main():
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

    filtered = df[df["role_type"].isin(role_filter) & df["location"].isin(location_filter)]
    if remote_only:
        filtered = filtered[filtered["remote_option"] == True]

    if filtered.empty:
        st.warning("No applications match the selected filters.")
        return

    # ---------------- KPI row ----------------
    total_apps = len(filtered)
    responded = filtered[~filtered["stage"].isin(["Applied"])].shape[0]
    response_rate = responded / total_apps * 100 if total_apps else 0
    interviews = filtered[filtered["stage"].isin(["Technical Interview", "HR Interview", "Offer"])].shape[0]
    offers = filtered[filtered["stage"] == "Offer"].shape[0]
    avg_response_days = filtered["days_to_response"].dropna().mean()

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total Applications", total_apps)
    k2.metric("Response Rate", f"{response_rate:.0f}%")
    k3.metric("Interview Stage Reached", interviews)
    k4.metric("Offers", offers)
    k5.metric("Avg. Response Time", f"{avg_response_days:.0f} days" if pd.notna(avg_response_days) else "—")

    st.divider()

    # ---------------- Row 1: Funnel + Stage breakdown ----------------
    c1, c2 = st.columns([1.2, 1])

    with c1:
        st.subheader("Application Funnel")
        funnel_df = funnel_counts(filtered)
        fig = go.Figure(go.Funnel(
            y=funnel_df["stage"],
            x=funnel_df["count"],
            textinfo="value+percent initial",
            marker={"color": ["#4C78A8", "#72B7B2", "#54A24B", "#EECA3B", "#E45756"]},
        ))
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
            fig5 = px.bar(gap_counts.head(10), x="count", y="skill", orientation="h", color="count",
                          color_continuous_scale="Reds")
            fig5.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=350, coloraxis_showscale=False)
            st.plotly_chart(fig5, width="stretch")
        else:
            st.info("No skill gaps flagged for the current filter selection.")

    with c6:
        st.subheader("Response Rate by Company Type")
        comp = filtered.groupby("org_type").apply(
            lambda g: (~g["stage"].isin(["Applied"])).mean() * 100
        ).reset_index(name="response_rate")
        fig6 = px.bar(comp, x="org_type", y="response_rate", color="org_type",
                      labels={"response_rate": "Response Rate (%)", "org_type": "Company Type"})
        fig6.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=350, showlegend=False)
        st.plotly_chart(fig6, width="stretch")

    st.divider()

    # ---------------- Data table ----------------
    with st.expander("📋 View raw application data"):
        st.dataframe(
            filtered.sort_values("applied_on", ascending=False),
            width="stretch",
            hide_index=True,
        )

    st.caption(
        "Built by Vivek J Poojary · [Portfolio](https://vivekjpoojary.vercel.app) · "
        "[GitHub](https://github.com/Vivekjpoojary) · "
        "[LinkedIn](https://linkedin.com/in/vivekjpoojary)"
    )


if __name__ == "__main__":
    main()
