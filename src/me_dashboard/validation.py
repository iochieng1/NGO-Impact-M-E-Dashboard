"""Data-quality checks run before results reach the dashboard.

Each check returns a DataFrame of offending rows with an 'issue' column, so the
dashboard can list them and field teams can fix them at source.
"""

from __future__ import annotations

import re

import pandas as pd

from .metrics import period_key

PERIOD_RE = re.compile(r"^\d{4}(-Q[1-4])?$")
VALID_DISAGG = {"all", "female", "male"}


def _flag(df: pd.DataFrame, mask, issue: str) -> pd.DataFrame:
    return df[mask].assign(issue=issue)


def check_results(results: pd.DataFrame, indicators: pd.DataFrame, counties: pd.DataFrame) -> pd.DataFrame:
    units = indicators.set_index("id")["unit"]
    unit = results["indicator_id"].map(units)
    issues = [
        _flag(results, ~results["indicator_id"].isin(indicators["id"]), "Unknown indicator id"),
        _flag(results, ~results["county_code"].isin(counties["county_code"]), "Invalid county code (must be 1-47)"),
        _flag(results, ~results["period"].astype(str).str.match(PERIOD_RE), "Bad period format (use YYYY or YYYY-Qn)"),
        _flag(results, ~results["disaggregation"].isin(VALID_DISAGG), "Unknown disaggregation"),
        _flag(results, results["value"].isna(), "Missing value"),
        _flag(results, results["value"] < 0, "Negative value"),
        _flag(results, (unit == "percent") & (results["value"] > 100), "Percentage above 100"),
        _flag(
            results,
            results.duplicated(["indicator_id", "county_code", "period", "disaggregation"], keep=False),
            "Duplicate report",
        ),
    ]
    return pd.concat(issues, ignore_index=True)


def check_completeness(
    results: pd.DataFrame, indicators: pd.DataFrame, focus_counties: list[int], up_to: str
) -> pd.DataFrame:
    """List quarterly indicator/county/period combinations with no report yet."""
    quarterly = indicators.loc[indicators["frequency"] == "quarterly", "id"]
    last_year, last_q = period_key(up_to)
    first_year = min(period_key(p)[0] for p in results["period"]) if len(results) else last_year
    periods = [
        f"{y}-Q{q}"
        for y in range(first_year, last_year + 1)
        for q in range(1, 5)
        if (y, q) <= (last_year, last_q)
    ]
    expected = pd.MultiIndex.from_product(
        [quarterly, focus_counties, periods], names=["indicator_id", "county_code", "period"]
    ).to_frame(index=False)
    reported = results[["indicator_id", "county_code", "period"]].drop_duplicates()
    merged = expected.merge(reported, how="left", indicator=True)
    return merged[merged["_merge"] == "left_only"].drop(columns="_merge").assign(issue="Report not submitted")
