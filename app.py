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
from typing import Any, Dict, List, Optional, Tuple
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
    search_term: Optional[str] = None,
) -> pd.DataFrame:
    """Filter job applications DataFrame based on role, location, remote flag, date range, and search query."""
    filtered = df[df["role_type"].isin(roles) & df["location"].isin(locations)]
    if remote_only:
        filtered = filtered[filtered["remote_option"] == True]
    if date_range and len(date_range) == 2:
        start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        filtered = filtered[(filtered["applied_on"] >= start_date) & (filtered["applied_on"] <= end_date)]
    if search_term and search_term.strip():
        term = search_term.strip().lower()
        company_match = filtered["company"].astype(str).str.lower().str.contains(term)
        skill_match = filtered["flagged_skill_gap"].astype(str).str.lower().str.contains(term)
        filtered = filtered[company_match | skill_match]
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
            "median_response_days": float("nan"),
            "p90_response_days": float("nan"),
        }

    responded = df[~df["stage"].isin(["Applied"])].shape[0]
    response_rate = (responded / total_apps) * 100
    interviews = df[df["stage"].isin(["Technical Interview", "HR Interview", "Offer"])].shape[0]
    offers = df[df["stage"] == "Offer"].shape[0]
    valid_resp = df["days_to_response"].dropna()
    avg_response_days = valid_resp.mean() if not valid_resp.empty else float("nan")
    median_response_days = valid_resp.median() if not valid_resp.empty else float("nan")
    p90_response_days = valid_resp.quantile(0.9) if not valid_resp.empty else float("nan")

    return {
        "total_apps": total_apps,
        "response_rate": response_rate,
        "interviews": interviews,
        "offers": offers,
        "avg_response_days": avg_response_days,
        "median_response_days": median_response_days,
        "p90_response_days": p90_response_days,
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


def calculate_stage_conversion_rates(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate step-by-step conversion rates between consecutive funnel stages."""
    if df.empty:
        return pd.DataFrame(
            columns=["transition", "from_stage", "to_stage", "from_count", "to_count", "conversion_rate"]
        )

    funnel = funnel_counts(df)
    stages = list(funnel["stage"])
    counts = list(funnel["count"])

    records = []
    for i in range(len(stages) - 1):
        from_stage = stages[i]
        to_stage = stages[i + 1]
        from_cnt = counts[i]
        to_cnt = counts[i + 1]
        rate = round((to_cnt / from_cnt) * 100, 1) if from_cnt > 0 else 0.0
        transition = f"{from_stage} ➔ {to_stage}"
        records.append(
            {
                "transition": transition,
                "from_stage": from_stage,
                "to_stage": to_stage,
                "from_count": from_cnt,
                "to_count": to_cnt,
                "conversion_rate": rate,
            }
        )

    return pd.DataFrame(records)



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


def calculate_source_performance(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate application count, response rate, and interview conversion rate by application source."""
    if df.empty or "source" not in df.columns:
        return pd.DataFrame(columns=["source", "total_apps", "response_rate", "interview_rate"])
    records = []
    for source, group in df.groupby("source"):
        total = len(group)
        responded = (~group["stage"].isin(["Applied"])).sum()
        interviews = (group["stage"].isin(["Technical Interview", "HR Interview", "Offer"])).sum()
        records.append({
            "source": source,
            "total_apps": total,
            "response_rate": round((responded / total) * 100, 1),
            "interview_rate": round((interviews / total) * 100, 1),
        })
    return pd.DataFrame(records).sort_values("total_apps", ascending=False)


def identify_stale_applications(
    df: pd.DataFrame,
    days_threshold: int = 21,
    reference_date: Optional[pd.Timestamp] = None,
) -> pd.DataFrame:
    """Identify applications stuck in 'Applied' state for longer than days_threshold."""
    if df.empty or "stage" not in df.columns or "applied_on" not in df.columns:
        return pd.DataFrame()
    applied_only = df[df["stage"] == "Applied"].copy()
    if applied_only.empty:
        return pd.DataFrame()
    ref_dt = pd.to_datetime(reference_date) if reference_date is not None else pd.to_datetime(df["applied_on"].max())
    applied_only["applied_on"] = pd.to_datetime(applied_only["applied_on"])
    applied_only["days_waiting"] = (ref_dt - applied_only["applied_on"]).dt.days
    stale = applied_only[applied_only["days_waiting"] >= days_threshold].sort_values("days_waiting", ascending=False)
    return stale


def calculate_application_velocity(
    df: pd.DataFrame, reference_date: Optional[pd.Timestamp] = None
) -> Dict[str, Any]:
    """Calculate application submission velocity metrics including 7-day total, 30-day total, WoW change, and peak submission day."""
    if df.empty or "applied_on" not in df.columns:
        return {
            "apps_last_7d": 0,
            "apps_prev_7d": 0,
            "apps_last_30d": 0,
            "wow_change_pct": 0.0,
            "peak_day_of_week": "N/A",
            "avg_weekly_velocity": 0.0,
        }

    applied_dates = pd.to_datetime(df["applied_on"])
    ref_dt = pd.to_datetime(reference_date) if reference_date is not None else applied_dates.max()

    cutoff_7d = ref_dt - pd.Timedelta(days=7)
    cutoff_14d = ref_dt - pd.Timedelta(days=14)
    cutoff_30d = ref_dt - pd.Timedelta(days=30)

    count_7d = int(((applied_dates >= cutoff_7d) & (applied_dates <= ref_dt)).sum())
    count_prev_7d = int(((applied_dates >= cutoff_14d) & (applied_dates < cutoff_7d)).sum())
    count_30d = int(((applied_dates >= cutoff_30d) & (applied_dates <= ref_dt)).sum())

    if count_prev_7d > 0:
        wow_change_pct = round(((count_7d - count_prev_7d) / count_prev_7d) * 100, 1)
    elif count_7d > 0:
        wow_change_pct = 100.0
    else:
        wow_change_pct = 0.0

    day_names = applied_dates.dt.day_name()
    peak_day = day_names.value_counts().index[0] if not day_names.empty else "N/A"

    date_span = (applied_dates.max() - applied_dates.min()).days
    weeks = max(1.0, date_span / 7.0)
    avg_weekly_velocity = round(len(df) / weeks, 1)

    return {
        "apps_last_7d": count_7d,
        "apps_prev_7d": count_prev_7d,
        "apps_last_30d": count_30d,
        "wow_change_pct": wow_change_pct,
        "peak_day_of_week": peak_day,
        "avg_weekly_velocity": avg_weekly_velocity,
    }


def generate_insights(df: pd.DataFrame) -> List[str]:
    """Generate dynamic data-driven insights and action points based on applications."""
    insights = []
    if df.empty:
        return ["No application data available for the current selection."]

    comp_rates = calculate_company_response_rates(df)
    if not comp_rates.empty:
        best_org = comp_rates.sort_values("response_rate", ascending=False).iloc[0]
        insights.append(
            f"🎯 Highest response rate is from **{best_org['org_type']}** ({best_org['response_rate']:.1f}%)."
        )

    velocity = calculate_application_velocity(df)
    if velocity["apps_last_7d"] > 0:
        trend_str = f"+{velocity['wow_change_pct']}%" if velocity['wow_change_pct'] >= 0 else f"{velocity['wow_change_pct']}%"
        insights.append(
            f"🚀 Application velocity: **{velocity['apps_last_7d']} apps in last 7 days** ({trend_str} vs previous 7d). Peak day: **{velocity['peak_day_of_week']}**."
        )

    source_perf = calculate_source_performance(df)
    if not source_perf.empty:
        best_source = source_perf.sort_values("response_rate", ascending=False).iloc[0]
        insights.append(
            f"📌 Most responsive application channel is **{best_source['source']}** ({best_source['response_rate']:.1f}% response rate)."
        )

    gaps = df["flagged_skill_gap"].dropna()
    if not gaps.empty:
        top_gap = gaps.value_counts().index[0]
        gap_count = gaps.value_counts().iloc[0]
        insights.append(
            f"⚡ Top missing skill flagged in rejections/interviews is **{top_gap}** ({gap_count} occurrences)."
        )

    offers = (df["stage"] == "Offer").sum()
    interviews = df["stage"].isin(["Technical Interview", "HR Interview", "Offer"]).sum()
    if interviews > 0:
        conv_rate = (offers / interviews) * 100
        insights.append(
            f"📈 Interview-to-Offer conversion rate is **{conv_rate:.1f}%** ({offers} offers from {interviews} interview stages)."
        )

    stale_df = identify_stale_applications(df)
    if not stale_df.empty:
        insights.append(
            f"⏳ **{len(stale_df)} pending applications** have been awaiting feedback for over 21 days."
        )

    return insights





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
    search_query = st.sidebar.text_input("🔍 Search Company / Skill", placeholder="e.g. TCS, Docker, AWS")
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
        search_term=search_query,
    )


    if filtered.empty:
        st.warning("No applications match the selected filters.")
        return

    # ---------------- KPI row ----------------
    kpis = calculate_kpis(filtered)
    velocity = calculate_application_velocity(filtered)

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Total Applications", kpis["total_apps"])
    k2.metric("Response Rate", f"{kpis['response_rate']:.0f}%")
    k3.metric("Interviews Reached", kpis["interviews"])
    k4.metric("Offers", kpis["offers"])
    avg_resp = kpis["avg_response_days"]
    med_resp = kpis["median_response_days"]
    k5.metric("Avg. Response Time", f"{avg_resp:.0f} days" if pd.notna(avg_resp) else "—")
    k6.metric("Median Response Time", f"{med_resp:.0f} days" if pd.notna(med_resp) else "—")

    v1, v2, v3, v4 = st.columns(4)
    v1.metric(
        "Velocity (Last 7d)",
        velocity["apps_last_7d"],
        delta=f"{velocity['wow_change_pct']}% WoW" if velocity["apps_prev_7d"] > 0 else None,
    )
    v2.metric("Volume (Last 30d)", velocity["apps_last_30d"])
    v3.metric("Weekly Pace", f"{velocity['avg_weekly_velocity']} / wk")
    v4.metric("Peak Submission Day", velocity["peak_day_of_week"])



    # Key Insights Section
    insights = generate_insights(filtered)
    if insights:
        with st.expander("💡 Key Automated Insights & Recommendations", expanded=True):
            for item in insights:
                st.markdown(f"- {item}")

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
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=320)
        st.plotly_chart(fig, width="stretch")

        conv_df = calculate_stage_conversion_rates(filtered)
        if not conv_df.empty:
            with st.expander("🔍 Step-by-Step Conversion Rates", expanded=False):
                st.dataframe(
                    conv_df[["transition", "from_count", "to_count", "conversion_rate"]].rename(
                        columns={
                            "transition": "Stage Transition",
                            "from_count": "Entering Count",
                            "to_count": "Advancing Count",
                            "conversion_rate": "Conversion %",
                        }
                    ),
                    width="stretch",
                    hide_index=True,
                )


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

    # ---------------- Row 4: Source Performance + Salary Expectations ----------------
    c7, c8 = st.columns(2)

    with c7:
        st.subheader("Performance by Application Channel")
        source_df = calculate_source_performance(filtered)
        if not source_df.empty:
            fig7 = px.bar(
                source_df,
                x="source",
                y=["response_rate", "interview_rate"],
                barmode="group",
                labels={"value": "Percentage (%)", "source": "Platform / Channel", "variable": "Metric"},
            )
            fig7.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=350)
            st.plotly_chart(fig7, width="stretch")
        else:
            st.info("No source data available for current selection.")

    with c8:
        if "estimated_ctc_lpa" in filtered.columns:
            st.subheader("Estimated CTC Range (LPA) by Role Type")
            salary_df = calculate_salary_stats(filtered)
            fig8 = px.bar(
                salary_df,
                x="role_type",
                y="mean_ctc",
                color="role_type",
                text="mean_ctc",
                labels={"mean_ctc": "Average CTC (LPA)", "role_type": "Role Type"},
            )
            fig8.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=350, showlegend=False)
            st.plotly_chart(fig8, width="stretch")

    # ---------------- SLA Warning Section ----------------
    stale_apps = identify_stale_applications(filtered, days_threshold=21)
    if not stale_apps.empty:
        with st.expander(f"⏳ Pending Application SLA Warning ({len(stale_apps)} apps awaiting response > 21 days)", expanded=False):
            st.warning("Applications submitted over 21 days ago without feedback update:")
            st.dataframe(
                stale_apps[["application_id", "company", "role_type", "source", "applied_on", "days_waiting"]],
                width="stretch",
                hide_index=True,
            )

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
