"""Pull form submissions from KoboToolbox (API v2).

Most Kenyan NGOs collect field data with KoboToolbox or ODK Collect because the
apps work offline and sync when enumerators reach network coverage. This module
downloads submissions and maps them into the dashboard's long results format.

Configure with environment variables (never commit tokens):
    KOBO_SERVER     e.g. https://kf.kobotoolbox.org or https://eu.kobotoolbox.org
    KOBO_TOKEN      API token from Account Settings > Security
"""

from __future__ import annotations

import os

import pandas as pd
import requests

DEFAULT_SERVER = "https://kf.kobotoolbox.org"


def fetch_submissions(asset_uid: str, server: str | None = None, token: str | None = None) -> pd.DataFrame:
    server = (server or os.environ.get("KOBO_SERVER", DEFAULT_SERVER)).rstrip("/")
    token = token or os.environ["KOBO_TOKEN"]
    url = f"{server}/api/v2/assets/{asset_uid}/data/"
    params = {"format": "json", "limit": 1000, "start": 0}
    rows: list[dict] = []
    while True:
        resp = requests.get(url, headers={"Authorization": f"Token {token}"}, params=params, timeout=60)
        resp.raise_for_status()
        page = resp.json()
        rows.extend(page["results"])
        if not page.get("next"):
            break
        params["start"] += params["limit"]
    return pd.json_normalize(rows)


def water_point_form_to_results(submissions: pd.DataFrame) -> pd.DataFrame:
    """Example mapping for a water-point functionality form -> WASH-OP1.

    Adjust the field names to match your XLSForm. Expected fields:
    county_code, completion_date, is_functional (yes/no).
    """
    df = submissions.copy()
    df = df[df["is_functional"] == "yes"]
    date = pd.to_datetime(df["completion_date"])
    df["period"] = date.dt.year.astype(str) + "-Q" + date.dt.quarter.astype(str)
    out = df.groupby(["county_code", "period"], as_index=False).size().rename(columns={"size": "value"})
    return out.assign(indicator_id="WASH-OP1", disaggregation="all", source="kobo:water_point_check")[
        ["indicator_id", "county_code", "period", "disaggregation", "value", "source"]
    ]
