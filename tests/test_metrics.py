import math

import pandas as pd

from me_dashboard.metrics import headline_values, period_key, progress, rag_status


def test_period_key_orders_annual_after_quarters():
    assert sorted(["2025", "2025-Q1", "2024-Q4"], key=period_key) == ["2024-Q4", "2025-Q1", "2025"]


def test_progress_handles_both_directions():
    assert progress(60, 40, 80) == 0.5
    assert progress(30, 50, 10) == 0.5  # decrease indicator, e.g. stunting rate
    assert progress(5, 5, 5) == 1.0


def test_rag_status_scales_by_time_elapsed():
    assert rag_status(0.45, expected=0.5) == "On track"
    assert rag_status(0.35, expected=0.5) == "At risk"
    assert rag_status(0.1, expected=0.5) == "Off track"
    assert rag_status(math.nan) == "No data"


def test_headline_sums_disaggregates_only_when_no_total():
    df = pd.DataFrame([
        dict(indicator_id="A", county_code=1, period="2025-Q1", disaggregation="female", value=3),
        dict(indicator_id="A", county_code=1, period="2025-Q1", disaggregation="male", value=2),
        dict(indicator_id="B", county_code=1, period="2025-Q1", disaggregation="all", value=50),
        dict(indicator_id="B", county_code=1, period="2025-Q1", disaggregation="female", value=60),
    ])
    out = headline_values(df).set_index("indicator_id")["value"]
    assert out["A"] == 5
    assert out["B"] == 50
