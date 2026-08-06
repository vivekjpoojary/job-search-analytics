"""
Sanity tests for job search analytics dataset and funnel logic.
"""

import pytest
import pandas as pd
from pathlib import Path
from app import load_data, funnel_counts, STAGE_ORDER
from data.generate_data import generate_applications

DATA_PATH = Path(__file__).parent.parent / "data" / "applications.csv"


def test_applications_csv_exists_and_valid():
    assert DATA_PATH.exists(), "applications.csv must exist"
    df = pd.read_csv(DATA_PATH)
    assert not df.empty, "applications.csv should not be empty"
    required_cols = [
        "application_id", "company", "location", "remote_option",
        "org_type", "company_size", "role_type", "source",
        "applied_on", "stage", "days_to_response", "flagged_skill_gap"
    ]
    for col in required_cols:
        assert col in df.columns, f"Column {col} missing in dataset"


def test_funnel_counts_logic():
    df = load_data()
    funnel_df = funnel_counts(df)
    assert list(funnel_df["stage"]) == STAGE_ORDER
    # Reached counts must be monotonically non-increasing as we progress through stages
    counts = list(funnel_df["count"])
    for i in range(len(counts) - 1):
        assert counts[i] >= counts[i + 1], f"Stage {STAGE_ORDER[i]} count ({counts[i]}) < next stage count ({counts[i+1]})"


def test_generate_applications():
    df_gen = generate_applications(20)
    assert len(df_gen) == 20
    assert "application_id" in df_gen.columns
