import pandas as pd

from me_dashboard.data import load_counties, load_framework
from me_dashboard.validation import check_completeness, check_results


def test_reference_has_all_47_counties():
    counties = load_counties()
    assert len(counties) == 47
    assert counties["county_code"].tolist() == list(range(1, 48))


def test_check_results_flags_bad_rows():
    _, indicators = load_framework()
    df = pd.DataFrame([
        dict(indicator_id="WASH-OC1", county_code=23, period="2025", disaggregation="all", value=140),
        dict(indicator_id="WASH-OP1", county_code=48, period="2025-Q1", disaggregation="all", value=3),
        dict(indicator_id="WASH-OP1", county_code=23, period="Q1 2025", disaggregation="all", value=3),
    ])
    issues = set(check_results(df, indicators, load_counties())["issue"])
    assert {"Percentage above 100", "Invalid county code (must be 1-47)", "Bad period format (use YYYY or YYYY-Qn)"} <= issues


def test_completeness_finds_missing_quarter():
    _, indicators = load_framework()
    indicators = indicators[indicators["id"] == "WASH-OP1"]
    df = pd.DataFrame([dict(indicator_id="WASH-OP1", county_code=23, period="2025-Q1", disaggregation="all", value=1)])
    missing = check_completeness(df, indicators, [23], "2025-Q2")
    assert missing["period"].tolist() == ["2025-Q2"]


def test_sample_data_loads_and_is_clean_except_known_gap():
    from me_dashboard.data import load_dataset

    ds = load_dataset()
    assert check_results(ds.results, ds.indicators, ds.counties).empty
    gaps = check_completeness(ds.results, ds.indicators, ds.programme["focus_counties"], "2026-Q3")
    assert gaps[["indicator_id", "county_code", "period"]].values.tolist() == [["WASH-OP2", 10, "2026-Q3"]]
