"""Generate a synthetic dataset for the Imarisha Jamii case study.

All numbers are invented for demonstration. Baselines are shaped so that arid
northern counties (Turkana, Marsabit) start lower than Kisumu or Nairobi, which
mirrors the pattern in national surveys, but they are NOT official statistics.

    python scripts/generate_sample_data.py [--out data/sample] [--seed 42]
"""

from __future__ import annotations

import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

COUNTIES = {3: "Kilifi", 10: "Marsabit", 15: "Kitui", 23: "Turkana", 42: "Kisumu", 47: "Nairobi"}
# Relative starting point per county: 0 = hardest-to-reach, 1 = best-served.
CONTEXT = {3: 0.5, 10: 0.15, 15: 0.45, 23: 0.1, 42: 0.75, 47: 0.85}

QUARTERS = [f"{y}-Q{q}" for y in (2025, 2026) for q in (1, 2, 3, 4)][:7]  # through 2026-Q3
YEARS = (2025, 2026, 2027)

# Missing report, so the completeness check has something to show.
SKIP = {("WASH-OP2", 10, "2026-Q3")}


def targets(rng: random.Random) -> list[dict]:
    rows = []
    for code, c in CONTEXT.items():
        water_base = round(30 + 50 * c + rng.uniform(-3, 3), 1)
        girls_base = round(55 + 35 * c + rng.uniform(-3, 3), 1)
        savings_base = round(400 + 1600 * c, -1)
        feedback_base = 55.0
        for i, year in enumerate(YEARS, start=1):
            rows += [
                dict(indicator_id="WASH-OC1", year=year, baseline=water_base, target=min(95, water_base + 6 * i)),
                dict(indicator_id="WASH-OP1", year=year, baseline=0, target=round(12 - 6 * c) + 2),
                dict(indicator_id="WASH-OP2", year=year, baseline=0, target=8),
                dict(indicator_id="EDU-OC1", year=year, baseline=girls_base, target=min(98, girls_base + 4 * i)),
                dict(indicator_id="EDU-OP1", year=year, baseline=0, target=600),
                dict(indicator_id="LIV-OC1", year=year, baseline=savings_base, target=savings_base * (1 + 0.2 * i)),
                dict(indicator_id="LIV-OP1", year=year, baseline=0, target=1500),
                dict(indicator_id="CC-OC1", year=year, baseline=feedback_base, target=min(90, feedback_base + 12 * i)),
            ]
            for r in rows[-8:]:
                r["county_code"] = code
    return rows


def results(rng: random.Random, tgt: list[dict]) -> list[dict]:
    lookup = {(t["indicator_id"], t["county_code"], t["year"]): t for t in tgt}
    rows = []

    def add(ind, code, period, value, disagg="all"):
        if (ind, code, period) in SKIP:
            return
        rows.append(
            dict(indicator_id=ind, county_code=code, period=period, disaggregation=disagg,
                 value=round(value, 1), source="synthetic")
        )

    for code, c in CONTEXT.items():
        # Performance factor: some counties under-deliver (insecurity, drought, etc.).
        perf = rng.uniform(0.55, 1.15) if c > 0.2 else rng.uniform(0.45, 0.9)
        for n, period in enumerate(QUARTERS):
            year, q = int(period[:4]), int(period[-1])
            t = lambda ind: lookup[(ind, code, year)]  # noqa: E731
            add("WASH-OP1", code, period, max(0, round(t("WASH-OP1")["target"] / 4 * perf + rng.uniform(-1, 1))))
            add("WASH-OP2", code, period, max(0, round(2 * perf + rng.uniform(-1, 1))))
            for sex, share in (("female", 0.7), ("male", 0.3)):
                add("EDU-OP1", code, period, round(150 * perf * share * rng.uniform(0.8, 1.2)), sex)
            for sex, share in (("female", 0.75), ("male", 0.25)):
                add("LIV-OP1", code, period, round(375 * perf * share * rng.uniform(0.8, 1.2)), sex)
            sv = t("LIV-OC1")
            add("LIV-OC1", code, period, sv["baseline"] * (1 + 0.05 * (n + 1) * perf) * rng.uniform(0.95, 1.05))
            fb = t("CC-OC1")
            add("CC-OC1", code, period, min(100, fb["baseline"] + 3 * (n + 1) * perf + rng.uniform(-4, 4)))
        # Annual outcome survey (2025 only so far; 2026 survey runs in Q4).
        for ind in ("WASH-OC1", "EDU-OC1"):
            t25 = lookup[(ind, code, 2025)]
            add(ind, code, "2025", t25["baseline"] + (t25["target"] - t25["baseline"]) * perf + rng.uniform(-1, 1))
    return rows


def beneficiaries(rng: random.Random) -> list[dict]:
    rows, start = [], date(2025, 1, 6)
    sectors = [("wash", None), ("education", 0.7), ("livelihoods", 0.75)]
    for code in COUNTIES:
        for sector, female_share in sectors:
            for _ in range(rng.randint(250, 600)):
                female = rng.random() < (female_share or 0.52)
                age = "10-17" if sector == "education" else rng.choice(["18-24", "25-35", "36-59", "60+"])
                rows.append(dict(
                    beneficiary_id=f"IJ-{len(rows) + 1:06d}",  # pseudonymous; names stay in the field system
                    county_code=code, sector=sector,
                    sex="female" if female else "male", age_band=age,
                    disability=rng.random() < 0.04,
                    enrolled_on=(start + timedelta(days=rng.randint(0, 630))).isoformat(),
                ))
    return rows


def write(path: Path, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows):>5} rows -> {path.relative_to(ROOT)}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=ROOT / "data" / "sample")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    args.out.mkdir(parents=True, exist_ok=True)
    tgt = targets(rng)
    write(args.out / "targets.csv", tgt)
    write(args.out / "indicator_results.csv", results(rng, tgt))
    write(args.out / "beneficiaries.csv", beneficiaries(rng))


if __name__ == "__main__":
    main()
