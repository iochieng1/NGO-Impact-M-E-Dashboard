# Implementation Roadmap

A phased plan to take the scaffold from synthetic data to a system an NGO M&E
team uses every week. Durations assume one developer/analyst working with the
M&E lead.

## Phase 0: Scaffold (done)
- [x] Results framework in `config/indicators.yaml`
- [x] Kenya county reference table (47 counties, official codes)
- [x] Synthetic dataset and generator
- [x] Scorecard with RAG status, trends, reach and data-quality tabs
- [x] KoboToolbox ingestion stub
- [x] Unit tests

## Phase 1: Design with users (weeks 1–3)
- [ ] Workshop with the M&E lead and two county officers: confirm the
      indicators, definitions, baselines and targets
- [ ] Build XLSForms in Kobo (English + Kiswahili), pilot them in Kisumu
- [ ] Data Protection Impact Assessment; check ODPC registration status
- [ ] Agree the data-sharing approach with county governments

## Phase 2: Real data pipeline (weeks 4–8)
- [ ] Finish `ingest/kobo.py` mappings for each form → indicator
- [ ] Add a `scripts/ingest.py` that pulls, validates and writes `data/processed/`
- [ ] Point `load_dataset()` at `data/processed/` via an environment variable
- [ ] Move storage from CSV to PostgreSQL (or SQLite for a single office)
- [ ] Schedule the ingest (cron / GitHub Actions) daily

## Phase 3: Dashboard hardening (weeks 6–10)
- [ ] Login (Streamlit auth or a reverse proxy), with roles: HQ, county, donor/external
- [ ] Small-cell suppression (< 5) for external roles
- [ ] County choropleth map (add a Kenya county GeoJSON, e.g. from KNBS/IEBC
      boundaries, to `data/reference/`)
- [ ] Export: donor report tables (CSV/Excel) and PBO annual summary
- [ ] Sub-county / ward drill-down

## Phase 4: Rollout (weeks 10–14)
- [ ] Train county M&E officers (half-day per county, in person where connectivity is poor)
- [ ] Run the first quarterly review meeting from the dashboard
- [ ] First Data Quality Audit: re-check a 5–10% sample of records in the field

## Phase 5: Learn and extend (ongoing)
- [ ] Add a health component and pull from KHIS (DHIS2 API)
- [ ] SMS feedback integration for the accountability indicator
- [ ] Mid-term evaluation (2026) using the dashboard as the monitoring source

## Hosting options

| Option | Cost | Notes |
|---|---|---|
| Streamlit Community Cloud | Free | Only for synthetic/demo data; never real beneficiary data |
| Small VM (local Kenyan provider or cloud region) | Low | Full control; you handle backups and security |
| Organisation's existing server | Low | Easiest data-protection story if already approved |
