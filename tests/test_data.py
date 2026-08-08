"""
Sanity tests for job search analytics dataset, funnel logic, filters, KPI metrics, and generator.
"""

import math
import unittest
from pathlib import Path
import pandas as pd

from app import (
    STAGE_ORDER,
    calculate_company_response_rates,
    calculate_kpis,
    calculate_salary_stats,
    calculate_source_performance,
    filter_applications,
    funnel_counts,
    generate_insights,
    identify_stale_applications,
    load_data,
)
from data.generate_data import generate_applications

DATA_PATH = Path(__file__).parent.parent / "data" / "applications.csv"


class TestJobSearchAnalytics(unittest.TestCase):

    def test_applications_csv_exists_and_valid(self):
        self.assertTrue(DATA_PATH.exists(), "applications.csv must exist")
        df = pd.read_csv(DATA_PATH)
        self.assertFalse(df.empty, "applications.csv should not be empty")
        required_cols = [
            "application_id",
            "company",
            "location",
            "remote_option",
            "org_type",
            "company_size",
            "role_type",
            "source",
            "applied_on",
            "stage",
            "days_to_response",
            "flagged_skill_gap",
        ]
        for col in required_cols:
            self.assertIn(col, df.columns, f"Column {col} missing in dataset")

    def test_funnel_counts_logic(self):
        df = load_data()
        funnel_df = funnel_counts(df)
        self.assertEqual(list(funnel_df["stage"]), STAGE_ORDER)
        # Reached counts must be monotonically non-increasing as we progress through stages
        counts = list(funnel_df["count"])
        for i in range(len(counts) - 1):
            self.assertGreaterEqual(
                counts[i],
                counts[i + 1],
                f"Stage {STAGE_ORDER[i]} count ({counts[i]}) < next stage count ({counts[i+1]})",
            )

    def test_filter_applications(self):
        df = load_data()
        all_roles = list(df["role_type"].unique())
        all_locations = list(df["location"].unique())

        # Test remote filtering
        remote_df = filter_applications(
            df, roles=all_roles, locations=all_locations, remote_only=True
        )
        self.assertTrue((remote_df["remote_option"] == True).all())

        # Test role subset filtering
        subset_role = [all_roles[0]]
        role_df = filter_applications(
            df, roles=subset_role, locations=all_locations, remote_only=False
        )
        self.assertTrue((role_df["role_type"] == subset_role[0]).all())

        # Test search term filtering
        search_df = filter_applications(
            df, roles=all_roles, locations=all_locations, search_term="TCS"
        )
        self.assertTrue(all("TCS" in str(c) for c in search_df["company"]))


    def test_calculate_kpis(self):
        sample_data = pd.DataFrame(
            [
                {"stage": "Applied", "days_to_response": None},
                {"stage": "Technical Interview", "days_to_response": 5},
                {"stage": "Offer", "days_to_response": 15},
            ]
        )
        kpis = calculate_kpis(sample_data)
        self.assertEqual(kpis["total_apps"], 3)
        self.assertAlmostEqual(kpis["response_rate"], (2 / 3) * 100)
        self.assertEqual(kpis["interviews"], 2)
        self.assertEqual(kpis["offers"], 1)
        self.assertEqual(kpis["avg_response_days"], 10.0)
        self.assertEqual(kpis["median_response_days"], 10.0)
        self.assertAlmostEqual(kpis["p90_response_days"], 14.0)

        # Empty dataframe edge case
        empty_kpis = calculate_kpis(pd.DataFrame(columns=["stage", "days_to_response"]))
        self.assertEqual(empty_kpis["total_apps"], 0)
        self.assertTrue(math.isnan(empty_kpis["avg_response_days"]))
        self.assertTrue(math.isnan(empty_kpis["median_response_days"]))


    def test_calculate_company_response_rates(self):
        sample_data = pd.DataFrame(
            [
                {"org_type": "Startup", "stage": "Applied"},
                {"org_type": "Startup", "stage": "Offer"},
                {"org_type": "MNC", "stage": "Applied"},
            ]
        )
        comp_df = calculate_company_response_rates(sample_data)
        self.assertIn("org_type", comp_df.columns)
        self.assertIn("response_rate", comp_df.columns)
        startup_rate = comp_df[comp_df["org_type"] == "Startup"]["response_rate"].values[0]
        mnc_rate = comp_df[comp_df["org_type"] == "MNC"]["response_rate"].values[0]
        self.assertEqual(startup_rate, 50.0)
        self.assertEqual(mnc_rate, 0.0)

    def test_calculate_salary_stats(self):
        sample_data = pd.DataFrame(
            [
                {"role_type": "Data Science", "estimated_ctc_lpa": 8.0},
                {"role_type": "Data Science", "estimated_ctc_lpa": 10.0},
                {"role_type": "SWE", "estimated_ctc_lpa": 6.0},
            ]
        )
        salary_df = calculate_salary_stats(sample_data)
        self.assertIn("role_type", salary_df.columns)
        self.assertIn("mean_ctc", salary_df.columns)
        ds_mean = salary_df[salary_df["role_type"] == "Data Science"]["mean_ctc"].values[0]
        self.assertEqual(ds_mean, 9.0)

    def test_generate_insights(self):
        sample_df = pd.DataFrame(
            [
                {"org_type": "Startup", "stage": "Offer", "flagged_skill_gap": "Docker"},
                {"org_type": "Startup", "stage": "Technical Interview", "flagged_skill_gap": "Docker"},
                {"org_type": "MNC", "stage": "Applied", "flagged_skill_gap": None},
            ]
        )
        insights = generate_insights(sample_df)
        self.assertTrue(len(insights) >= 2)
        self.assertTrue(any("Startup" in item for item in insights))
        self.assertTrue(any("Docker" in item for item in insights))

        empty_insights = generate_insights(pd.DataFrame())
        self.assertEqual(len(empty_insights), 1)



    def test_calculate_source_performance(self):
        sample_df = pd.DataFrame(
            [
                {"source": "LinkedIn", "stage": "Applied"},
                {"source": "LinkedIn", "stage": "Technical Interview"},
                {"source": "Naukri", "stage": "Applied"},
            ]
        )
        perf_df = calculate_source_performance(sample_df)
        self.assertIn("source", perf_df.columns)
        self.assertIn("response_rate", perf_df.columns)
        self.assertIn("interview_rate", perf_df.columns)
        linkedin_row = perf_df[perf_df["source"] == "LinkedIn"].iloc[0]
        self.assertEqual(linkedin_row["response_rate"], 50.0)
        self.assertEqual(linkedin_row["interview_rate"], 50.0)

    def test_identify_stale_applications(self):
        sample_df = pd.DataFrame(
            [
                {"application_id": "APP-001", "stage": "Applied", "applied_on": "2026-07-01"},
                {"application_id": "APP-002", "stage": "Applied", "applied_on": "2026-07-30"},
                {"application_id": "APP-003", "stage": "Technical Interview", "applied_on": "2026-06-01"},
            ]
        )
        stale_df = identify_stale_applications(
            sample_df, days_threshold=20, reference_date=pd.Timestamp("2026-08-01")
        )
        self.assertEqual(len(stale_df), 1)
        self.assertEqual(stale_df.iloc[0]["application_id"], "APP-001")

    def test_generate_applications(self):
        df_gen = generate_applications(20)
        self.assertEqual(len(df_gen), 20)
        self.assertIn("application_id", df_gen.columns)
        valid_stages = {
            "Applied",
            "Rejected - No Response",
            "Rejected After Screening",
            "Online Assessment",
            "Technical Interview",
            "HR Interview",
            "Offer",
        }
        self.assertTrue(set(df_gen["stage"].unique()).issubset(valid_stages))

    def test_generate_applications_with_seed(self):
        df1 = generate_applications(15, seed=123)
        df2 = generate_applications(15, seed=123)
        pd.testing.assert_frame_equal(df1, df2)


if __name__ == "__main__":
    unittest.main()

