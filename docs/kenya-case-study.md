# Kenya Case Study: Implementing an NGO M&E Dashboard

This document explains how the dashboard would be run in practice by an NGO
working in Kenya. It uses a hypothetical programme, **Imarisha Jamii**
("Strengthen the Community"), so that every design choice is tied to a
concrete situation. Substitute your own programme, counties and logframe.

> Check every legal and policy reference below against the current text before
> you rely on it. Laws, regulations and county plans change, and this document
> is a starting point, not legal advice.

---

## 1. Programme context

| Item | Case-study assumption |
|---|---|
| Implementer | A Kenyan NGO / Public Benefit Organization with a Nairobi head office and county field offices |
| Duration | Jan 2025 – Dec 2027 (3 years) |
| Sectors | WASH, girls' education, women's economic empowerment (VSLAs), plus accountability to communities |
| Counties | Turkana (23), Marsabit (10), Kitui (15), Kilifi (3), Kisumu (42), Nairobi (47, informal settlements) |
| Donors | Mix of institutional donors with different reporting templates |

**Why these counties?** They cover the main operating environments an NGO
meets in Kenya:

- **Arid north (Turkana, Marsabit):** pastoralist and mobile populations, long
  distances, patchy mobile coverage, drought cycles, occasional insecurity.
  Data collection must work offline and reporting gaps should be expected.
- **Semi-arid east and coast (Kitui, Kilifi):** recurrent water stress, mixed
  farming, high poverty in parts of the coast.
- **Lake region (Kisumu):** better connectivity and county data systems; a good
  pilot site.
- **Urban informal settlements (Nairobi):** dense, mobile populations, where
  avoiding double-counting is a major issue.

## 2. Policy alignment: why the indicators look the way they do

An NGO dashboard in Kenya is more useful (and gets more traction with
government) when its indicators report into existing frameworks:

| Framework | How the dashboard uses it |
|---|---|
| **Sustainable Development Goals** | Each indicator lists its SDG target (e.g. SDG 6.1.1 safe drinking water) in `config/indicators.yaml`. |
| **Kenya Vision 2030 & Medium-Term Plan IV (2023–2027)** | Indicators are tagged to the relevant pillar so they can be quoted in national-level reports. |
| **County Integrated Development Plans (CIDPs 2023–2027)** | Under devolution, counties lead on water, early childhood education, health and agriculture. Mapping indicators to CIDP sector targets lets you present results at County Assembly and sector working-group meetings. |
| **National & County Integrated M&E Systems (NIMES / CIMES)** | Use the same county codes and indicator definitions as government so data can be shared upwards. |
| **Public Benefit Organizations Act, 2013** (commenced May 2024; replaces the NGO Coordination Act regime) | Annual reporting to the PBO Regulatory Authority. The dashboard's annual export is a useful input. |

**County codes:** the reference file `data/reference/kenya_counties.csv` holds
the official 001–047 county codes. Every data file uses the numeric code, not
the name, which avoids problems with spellings like *Murang'a / Muranga* or
*Taita-Taveta / Taita Taveta*. Add sub-county and ward codes (from KNBS or the
IEBC) as a second reference table when you need finer detail.

## 3. Data sources

| Source | What it gives you | How it enters the dashboard |
|---|---|---|
| **KoboToolbox / ODK Collect** forms (English + Kiswahili, and local languages where needed, e.g. Ng'aturkana, Borana, Dholuo) | Household surveys, water-point checks, training attendance | `src/me_dashboard/ingest/kobo.py` pulls submissions through the API |
| **Beneficiary register** | Who was reached, disaggregated by sex, age and disability | Pseudonymous IDs only; names stay in the field system |
| **VSLA ledgers** | Savings and loans per group | Monthly ledger form summarised quarterly |
| **School records + NEMIS** (Ministry of Education's education management system) | Enrolment, transition | Cross-check NGO school data against NEMIS records shared by the County Director of Education |
| **KNBS** (2019 Census, Kenya Demographic & Health Survey 2022, Economic Survey) | Denominators and comparison baselines | Load county populations as a reference table |
| **KHIS (Kenya Health Information System, DHIS2)** | Health facility data, if you add a health component | DHIS2 Web API |
| **Feedback & complaints** (SMS short-code, toll-free line, suggestion boxes) | Accountability indicator CC-OC1 | SMS provider export or a simple form |

## 4. Data flow

```
 Field (offline)            Sync                 Processing                    Use
┌──────────────────┐   ┌──────────────┐   ┌──────────────────────────┐   ┌───────────────────┐
│ Enumerators on   │──▶│ KoboToolbox  │──▶│ ingest/kobo.py           │──▶│ Streamlit         │
│ Android phones   │   │ server       │   │  → long results table    │   │ dashboard         │
│ (Kobo / ODK)     │   └──────────────┘   │ validation.py            │   │  · County teams   │
├──────────────────┤                      │  → data-quality report   │   │  · HQ / donors    │
│ Paper registers  │──── data entry ─────▶│ metrics.py               │   │  · County gov't   │
│ (VSLA, schools)  │                      │  → scorecard vs targets  │   │    (aggregates)   │
└──────────────────┘                      └──────────────────────────┘   └───────────────────┘
```

All indicator values are stored in one long table
(`indicator_id, county_code, period, disaggregation, value, source`). Adding an
indicator means adding an entry to `config/indicators.yaml` and rows to that
table; no code changes are needed.

## 5. Data protection (Kenya Data Protection Act, 2019)

NGOs that collect beneficiary data are **data controllers** under the Act and
may need to register with the **Office of the Data Protection Commissioner
(ODPC)**. Design consequences for this project:

1. **Lawful basis and consent.** Registration forms record informed consent, in
   a language the respondent understands. For children (the education
   component), get consent from a parent or guardian.
2. **Data minimisation.** The dashboard never needs names, ID numbers or phone
   numbers. It uses pseudonymous beneficiary IDs (`IJ-000123`). The lookup
   between ID and identity stays in the field system with restricted access.
3. **Sensitive data.** Health status, disability and ethnicity are sensitive
   personal data. Collect only what an indicator needs, and report it in
   aggregate.
4. **Small-cell suppression.** When the dashboard is shared outside the NGO
   (with donors or counties), hide any disaggregated cell under 5 people so
   individuals in small villages cannot be identified. *(This is on the roadmap.)*
5. **Data Protection Impact Assessment (DPIA).** Do one before rollout. Large
   registers of vulnerable people are a typical trigger.
6. **Hosting and cross-border transfer.** If data is hosted outside Kenya (for
   example on the KoboToolbox EU server or a foreign cloud region), document
   the safeguards. Check the current transfer rules with counsel.
7. **Retention.** Set a retention period (for example, end of programme plus
   the donor audit period) and delete raw data afterwards.

`data/raw/` is git-ignored so real field data cannot be committed by accident.

## 6. Roles and responsibilities

| Role | Responsibility in the system |
|---|---|
| Community mobilisers / enumerators | Collect data with Kobo forms; first-line quality (complete forms, GPS on) |
| County M&E officer (one per county) | Reviews the data-quality tab weekly; follows up missing reports; validates before the quarter closes |
| HQ M&E lead | Owns `indicators.yaml` and targets; runs quarterly data-quality audits (DQA) with a sample re-check |
| Programme managers | Use the scorecard in quarterly review meetings; agree corrective actions for "Off track" lines |
| County government focal persons | Receive aggregate county views and align them with CIDP reviews |
| Communities | Get results back through barazas and feedback sessions (closing the loop) |

## 7. Reporting calendar

| When | What |
|---|---|
| Monthly | VSLA ledgers, feedback log |
| Quarterly (by the 15th of the next month) | All quarterly indicators submitted; data-quality tab clean; quarterly review meeting |
| Annually (Q4) | Household outcome survey (WASH-OC1), school transition (EDU-OC1), PBO annual report, donor annual reports |
| Mid-term (mid-2026) & end-line (late 2027) | External evaluation using the dashboard data as the monitoring baseline |

Kenya's government financial year runs July–June, while most donors use
calendar years. The dashboard uses calendar quarters; add a mapping column if
you need to report against county FY budgets.

## 8. Contextual risks and mitigation

| Risk | Effect on data | Mitigation built in / planned |
|---|---|---|
| Poor connectivity in arid counties | Late submissions | Offline forms, completeness check flags gaps instead of hiding them |
| Drought / displacement | Denominators change, outcomes fall | Annotate periods; compare with KNBS/NDMA drought phase data |
| Insecurity limiting access | Missing quarters | "No data" status kept separate from "Off track" |
| Double counting across sectors | Inflated reach | Unique pseudonymous ID across sectors; reach counts people, not services |
| Election periods (e.g. 2027 general election) | Activity slowdowns, sensitivity of data | Plan collection around the calendar; restrict sharing of location-level data |
| Staff turnover | Inconsistent definitions | Indicator definitions live in one YAML file under version control |

## 9. Lessons this case study is designed to test

- Does showing **"No data" separately from "Off track"** lead to better
  follow-up in hard-to-reach counties?
- Does sharing a county view with county officials improve **co-ownership** and
  data sharing (e.g. NEMIS access)?
- Is a lightweight stack (Kobo + Python + Streamlit) maintainable by a small
  M&E team without a dedicated developer?

See [implementation-roadmap.md](implementation-roadmap.md) for the phased plan.
