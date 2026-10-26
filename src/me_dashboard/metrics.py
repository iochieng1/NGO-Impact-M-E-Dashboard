"""Indicator calculations: progress against target and RAG status."""

from __future__ import annotations

import pandas as pd

# Share of the baseline->target distance that must be covered by the time
# elapsed in the year for an indicator to be "on track".
ON_TRACK = 0.9
AT_RISK = 0.6


def period_key(period: str) -> tuple[int, int]:
    """Sort key for periods like '2025-Q3' or '2025' (annual = Q4)."""
    year, _, quarter = period.partition("-Q")
    return int(year), int(quarter or 4)


def headline_values(results: pd.DataFrame) -> pd.DataFrame:
    """Collapse disaggregated rows (e.g. by sex) to one value per indicator/county/period.

    Counts are summed across disaggregates. Rates and averages are expected to
    be reported with an explicit 'all' row, which is used when present.
    """
    totals = results[results["disaggregation"] == "all"]
    split = results[results["disaggregation"] != "all"]
    have_total = set(zip(totals["indicator_id"], totals["county_code"], totals["period"]))
    missing = split[
        [k not in have_total for k in zip(split["indicator_id"], split["county_code"], split["period"])]
    ]
    summed = missing.groupby(["indicator_id", "county_code", "period"], as_index=False)["value"].sum()
    return pd.concat([totals[["indicator_id", "county_code", "period", "value"]], summed], ignore_index=True)


def cumulative_or_latest(values: pd.DataFrame, indicators: pd.DataFrame, year: int) -> pd.DataFrame:
    """Value to compare with an annual target.

    Output counts are cumulative within the year; rates, averages and annual
    indicators use the most recent reported period.
    """
    df = values[values["period"].str.startswith(str(year))].merge(
        indicators[["id", "unit", "level"]], left_on="indicator_id", right_on="id"
    )
    df["_key"] = df["period"].map(period_key)
    is_flow = (df["unit"] == "count") & (df["level"] == "output")

    flows = df[is_flow].groupby(["indicator_id", "county_code"], as_index=False).agg(
        value=("value", "sum"), last_period=("_key", "max")
    )
    stocks = (
        df[~is_flow]
        .sort_values("_key")
        .groupby(["indicator_id", "county_code"], as_index=False)
        .agg(value=("value", "last"), last_period=("_key", "max"))
    )
    out = pd.concat([flows, stocks], ignore_index=True)
    out["last_period"] = out["last_period"].map(lambda k: f"{k[0]}-Q{k[1]}")
    return out


def progress(achieved: float, baseline: float, target: float) -> float:
    """Fraction of the baseline->target distance achieved. Works for either direction."""
    if target == baseline:
        return 1.0 if achieved == target else 0.0
    return (achieved - baseline) / (target - baseline)


def rag_status(pct: float, expected: float = 1.0) -> str:
    """Red/Amber/Green given progress and the share of the year elapsed."""
    if pd.isna(pct):
        return "No data"
    ratio = pct / expected if expected else pct
    if ratio >= ON_TRACK:
        return "On track"
    if ratio >= AT_RISK:
        return "At risk"
    return "Off track"


def scorecard(results: pd.DataFrame, targets: pd.DataFrame, indicators: pd.DataFrame, year: int) -> pd.DataFrame:
    """One row per indicator x county with achieved value, target, progress and RAG."""
    achieved = cumulative_or_latest(headline_values(results), indicators, year)
    t = targets[targets["year"] == year]
    df = t.merge(achieved, on=["indicator_id", "county_code"], how="left")

    def expected_share(row) -> float:
        if pd.isna(row["last_period"]):
            return 1.0
        # Quarterly indicators are judged against the share of the year elapsed
        # (a simplification: linear pacing towards the annual target).
        quarter = period_key(row["last_period"])[1]
        return quarter / 4 if row["frequency"] == "quarterly" else 1.0

    df = df.merge(
        indicators[["id", "name", "sector", "level", "unit", "frequency"]], left_on="indicator_id", right_on="id"
    )
    df["is_flow"] = (df["unit"] == "count") & (df["level"] == "output")
    # Cumulative counts start from zero each year; rates start from baseline.
    df["start"] = df["baseline"].where(~df["is_flow"], 0)
    df["progress"] = [
        progress(a, s, tg) if pd.notna(a) else float("nan")
        for a, s, tg in zip(df["value"], df["start"], df["target"])
    ]
    df["expected"] = df.apply(expected_share, axis=1)
    df["status"] = [rag_status(p, e) for p, e in zip(df["progress"], df["expected"])]
    return df.drop(columns=["id", "is_flow", "start", "frequency"])
