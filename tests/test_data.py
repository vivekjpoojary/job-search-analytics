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
    filter_applications,
    funnel_counts,
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

        # Empty dataframe edge case
        empty_kpis = calculate_kpis(pd.DataFrame(columns=["stage", "days_to_response"]))
        self.assertEqual(empty_kpis["total_apps"], 0)
        self.assertTrue(math.isnan(empty_kpis["avg_response_days"]))

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


if __name__ == "__main__":
    unittest.main()
