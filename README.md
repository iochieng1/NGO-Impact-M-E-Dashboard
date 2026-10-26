# NGO Impact M&E Dashboard: Kenya Case Study

A lightweight Monitoring & Evaluation (M&E) dashboard for NGO programmes.
It tracks indicators against a logframe, shows progress by county with
on-track / at-risk / off-track status, reports reach by sex, age and
disability, and flags data-quality problems before they reach a donor report.

The case study is **Imarisha Jamii**, a hypothetical integrated WASH,
girls' education and livelihoods programme in six Kenyan counties
(Turkana, Marsabit, Kitui, Kilifi, Kisumu and Nairobi), running 2025–2027.
**All data in `data/sample/` is synthetic.**

## Features

| Tab | What it shows |
|---|---|
| **Scorecard** | Progress against annual targets per indicator and county (heatmap + table) with RAG status. Quarterly indicators are paced against time elapsed |
| **Trends** | Quarter-by-quarter values per county for any indicator |
| **Reach** | Unique people reached by county and sector; sex disaggregation; disability |
| **Data quality** | Invalid county codes, bad periods, % > 100, duplicates, missing quarterly reports |
| **Results framework** | The logframe as loaded from `config/indicators.yaml` |

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python scripts/generate_sample_data.py   # optional: sample data is already committed
pytest -q
streamlit run app.py
```

Or use `make install data test run`.

## Project structure

```
├── app.py                         Streamlit dashboard
├── config/indicators.yaml         Results framework (logframe). Edit this first
├── data/
│   ├── reference/kenya_counties.csv   47 counties with official codes
│   ├── sample/                    Synthetic results, targets, beneficiaries
│   └── raw/                       Real field data (git-ignored)
├── src/me_dashboard/
│   ├── data.py                    Loading and joining
│   ├── metrics.py                 Progress, pacing, RAG status, scorecard
│   ├── validation.py              Data-quality checks
│   └── ingest/kobo.py             KoboToolbox API v2 client + example mapping
├── scripts/generate_sample_data.py
├── tests/
└── docs/
    ├── kenya-case-study.md        Context, policy alignment, data protection, roles
    ├── implementation-roadmap.md  Phased plan from scaffold to production
    └── data-dictionary.md         File and column definitions
```

## Adapting it to your programme

1. Replace the indicators in `config/indicators.yaml` with your logframe.
2. Set `focus_counties` to your county codes (see `data/reference/kenya_counties.csv`).
3. Supply `targets.csv`, `indicator_results.csv` and `beneficiaries.csv` in the
   format described in [docs/data-dictionary.md](docs/data-dictionary.md), or
   build them from KoboToolbox with `src/me_dashboard/ingest/kobo.py`
   (set `KOBO_TOKEN`; see `.env.example`).
4. Read [docs/kenya-case-study.md](docs/kenya-case-study.md) before you collect
   real data. It covers the Data Protection Act 2019 requirements.

## Kenya case study in brief

- **Alignment:** every indicator is tagged to SDGs, Vision 2030 / MTP IV and
  County Integrated Development Plans, so results can be shared with county
  governments and reported to the PBO Regulatory Authority.
- **Devolution-aware:** the 47 counties are the main unit of analysis, using
  official county codes to match government data (KNBS, NEMIS, KHIS).
- **Built for low connectivity:** offline Kobo/ODK collection; missing
  reports show as "No data" rather than "Off track".
- **Privacy by design:** pseudonymous IDs only, raw data kept out of git,
  small-cell suppression planned for external views.

## Roadmap

See [docs/implementation-roadmap.md](docs/implementation-roadmap.md). Next
steps: real Kobo forms, a database backend, login with roles, a county
choropleth map and donor report exports.

## License

MIT. See [LICENSE](LICENSE).
