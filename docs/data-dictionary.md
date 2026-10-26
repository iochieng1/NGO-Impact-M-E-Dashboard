# Data Dictionary

All files are UTF-8 CSV. County is always the official numeric code (1–47).

## `data/reference/kenya_counties.csv`
| Column | Type | Description |
|---|---|---|
| county_code | int | Official county code, 1 (Mombasa) – 47 (Nairobi) |
| county | str | County name |
| former_province | str | Pre-2013 province, useful for regional grouping |

## `data/sample/indicator_results.csv`: one row per reported value
| Column | Type | Description |
|---|---|---|
| indicator_id | str | Matches `id` in `config/indicators.yaml` |
| county_code | int | 1–47 |
| period | str | `YYYY-Qn` for quarterly, `YYYY` for annual |
| disaggregation | str | `all`, `female` or `male` |
| value | float | Percent (0–100), count, or KES depending on the indicator's `unit` |
| source | str | Where the value came from (e.g. `kobo:water_point_check`) |

Counts reported only by sex are summed for the headline figure. Rates must
include an `all` row because rates cannot be summed.

## `data/sample/targets.csv`
| Column | Type | Description |
|---|---|---|
| indicator_id | str | |
| county_code | int | |
| year | int | Calendar year |
| baseline | float | Programme baseline (for output counts: 0) |
| target | float | End-of-year target. Output counts are annual targets; outcomes are the level to reach |

## `data/sample/beneficiaries.csv`
| Column | Type | Description |
|---|---|---|
| beneficiary_id | str | Pseudonymous ID, unique across sectors. No names or phone numbers |
| county_code | int | |
| sector | str | `wash`, `education`, `livelihoods` |
| sex | str | `female` / `male` |
| age_band | str | `10-17`, `18-24`, `25-35`, `36-59`, `60+` |
| disability | bool | Washington Group Short Set: "a lot of difficulty" or worse in any domain |
| enrolled_on | date | ISO date |
