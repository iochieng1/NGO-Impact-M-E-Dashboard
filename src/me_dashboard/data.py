"""Load reference data, the indicator framework and programme results."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "config"
REFERENCE_DIR = ROOT / "data" / "reference"
SAMPLE_DIR = ROOT / "data" / "sample"


@dataclass
class Dataset:
    """Everything the dashboard needs, already joined to county names."""

    programme: dict
    counties: pd.DataFrame
    indicators: pd.DataFrame
    targets: pd.DataFrame
    results: pd.DataFrame
    beneficiaries: pd.DataFrame


def load_counties() -> pd.DataFrame:
    return pd.read_csv(REFERENCE_DIR / "kenya_counties.csv")


def load_framework(path: Path = CONFIG_DIR / "indicators.yaml") -> tuple[dict, pd.DataFrame]:
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    indicators = pd.DataFrame(cfg["indicators"])
    return cfg["programme"], indicators


def load_dataset(data_dir: Path = SAMPLE_DIR) -> Dataset:
    """Load a dataset directory containing results, targets and beneficiaries CSVs."""
    programme, indicators = load_framework()
    counties = load_counties()
    names = counties[["county_code", "county"]]

    results = pd.read_csv(data_dir / "indicator_results.csv").merge(names, on="county_code", how="left")
    targets = pd.read_csv(data_dir / "targets.csv").merge(names, on="county_code", how="left")
    beneficiaries = pd.read_csv(
        data_dir / "beneficiaries.csv", parse_dates=["enrolled_on"]
    ).merge(names, on="county_code", how="left")

    return Dataset(programme, counties, indicators, targets, results, beneficiaries)
