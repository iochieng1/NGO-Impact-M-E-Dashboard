"""NGO Impact M&E Dashboard - Kenya case study.

Run with:  streamlit run app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent / "src"))

from me_dashboard.data import load_dataset  # noqa: E402
from me_dashboard.metrics import period_key, scorecard  # noqa: E402
from me_dashboard.validation import check_completeness, check_results  # noqa: E402

# Colour-blind-validated categorical order and reserved status colours.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
STATUS = {"On track": "#0ca30c", "At risk": "#fab219", "Off track": "#d03b3b", "No data": "#8a8984"}
STATUS_ICON = {"On track": "✅", "At risk": "⚠️", "Off track": "❌", "No data": "➖"}
SECTOR_ORDER = ["wash", "education", "livelihoods", "cross-cutting"]
SECTOR_LABEL = {"wash": "WASH", "education": "Education", "livelihoods": "Livelihoods", "cross-cutting": "Cross-cutting"}
UNIT_FMT = {"percent": "{:.1f}%", "count": "{:,.0f}", "kes": "KES {:,.0f}"}

st.set_page_config(page_title="NGO Impact M&E - Kenya", page_icon="📊", layout="wide")


@st.cache_data
def get_data():
    return load_dataset()


def fmt(value: float, unit: str) -> str:
    return "–" if pd.isna(value) else UNIT_FMT[unit].format(value)


def style(fig, height=380):
    fig.update_layout(
        height=height, margin=dict(l=8, r=8, t=40, b=8), legend_title_text="",
        hovermode="closest", font=dict(size=13),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(128,128,128,0.15)", zeroline=False)
    return fig


ds = get_data()
county_name = ds.counties.set_index("county_code")["county"]
focus = ds.programme["focus_counties"]
# Fixed county -> colour so filtering never repaints a county.
county_color = {county_name[c]: SERIES[i] for i, c in enumerate(focus)}

# ------------------------------------------------------------------ sidebar
st.sidebar.title("Imarisha Jamii")
st.sidebar.caption("Hypothetical integrated programme · 6 Kenyan counties · synthetic data")
years = sorted(ds.targets["year"].unique())
latest_period = max(ds.results["period"], key=period_key)
default_year = period_key(latest_period)[0]
year = st.sidebar.selectbox("Reporting year", years, index=years.index(default_year))
chosen = st.sidebar.multiselect(
    "Counties", focus, default=focus, format_func=lambda c: f"{county_name[c]} ({c:03d})"
)
sectors = st.sidebar.multiselect("Sectors", SECTOR_ORDER, default=SECTOR_ORDER, format_func=SECTOR_LABEL.get)
st.sidebar.markdown(f"**Latest data:** {latest_period}")

ind = ds.indicators[ds.indicators["sector"].isin(sectors)]
res = ds.results[ds.results["county_code"].isin(chosen) & ds.results["indicator_id"].isin(ind["id"])]
tgt = ds.targets[ds.targets["county_code"].isin(chosen) & ds.targets["indicator_id"].isin(ind["id"])]
ben = ds.beneficiaries[ds.beneficiaries["county_code"].isin(chosen) & ds.beneficiaries["sector"].isin(sectors)]
sc = scorecard(res, tgt, ind, year)

dq = pd.concat(
    [check_results(ds.results, ds.indicators, ds.counties),
     check_completeness(ds.results, ds.indicators, focus, latest_period)],
    ignore_index=True,
)

# ------------------------------------------------------------------ header
st.title("NGO Impact Monitoring & Evaluation Dashboard")
st.caption("Case study: Kenya · results framework aligned to SDGs, Vision 2030 / MTP IV and County Integrated Development Plans")

reached = ben[ben["enrolled_on"].dt.year <= year]
k1, k2, k3, k4 = st.columns(4)
k1.metric("People reached (cumulative)", f"{len(reached):,}")
k2.metric("Women & girls", f"{(reached['sex'] == 'female').mean():.0%}" if len(reached) else "–")
on_track = (sc["status"] == "On track").sum()
reported = (sc["status"] != "No data").sum()
k3.metric(f"Indicator-county pairs on track ({year})", f"{on_track} / {reported}")
k4.metric("Open data-quality issues", len(dq))

tab_score, tab_trend, tab_reach, tab_dq, tab_fw = st.tabs(
    ["Scorecard", "Trends", "Reach", "Data quality", "Results framework"]
)

# ------------------------------------------------------------------ scorecard
with tab_score:
    st.subheader(f"Progress against {year} targets")
    st.caption(
        "Progress = share of the baseline→target distance achieved. Output counts are cumulative "
        "in the year and judged against time elapsed; outcomes use the latest measurement."
    )
    counts = sc["status"].value_counts().reindex(STATUS, fill_value=0)
    cols = st.columns(len(STATUS))
    for col, (status, n) in zip(cols, counts.items()):
        col.markdown(f"{STATUS_ICON[status]} **{status}**  \n{n}")

    if len(sc):
        heat = sc.assign(county=sc["county"], pct=(sc["progress"] * 100).round(0))
        pivot = heat.pivot_table(index="indicator_id", columns="county", values="pct")
        fig = px.imshow(
            pivot, text_auto=".0f", aspect="auto", zmin=0, zmax=120,
            color_continuous_scale=["#cde2fb", "#6da7ec", "#2a78d6", "#184f95"],
            labels=dict(color="% of target"),
        )
        fig.update_traces(hovertemplate="%{y} · %{x}<br>%{z:.0f}% of target<extra></extra>")
        st.plotly_chart(style(fig, 420), width="stretch")

        table = sc.assign(
            Status=sc["status"].map(lambda s: f"{STATUS_ICON[s]} {s}"),
            Achieved=[fmt(v, u) for v, u in zip(sc["value"], sc["unit"])],
            Baseline=[fmt(v, u) for v, u in zip(sc["baseline"], sc["unit"])],
            Target=[fmt(v, u) for v, u in zip(sc["target"], sc["unit"])],
            Progress=(sc["progress"] * 100).round(0),
        )[["indicator_id", "name", "county", "Baseline", "Target", "Achieved", "Progress", "last_period", "Status"]]
        st.dataframe(
            table.rename(columns={"indicator_id": "ID", "name": "Indicator", "county": "County", "last_period": "As of"}),
            hide_index=True, width="stretch",
            column_config={"Progress": st.column_config.NumberColumn(format="%d%%")},
        )

# ------------------------------------------------------------------ trends
with tab_trend:
    options = ind["id"].tolist()
    if options:
        pick = st.selectbox(
            "Indicator", options, format_func=lambda i: f"{i} - {ind.set_index('id').loc[i, 'name']}"
        )
        meta = ind.set_index("id").loc[pick]
        series = res[res["indicator_id"] == pick]
        if meta["disaggregate"]:
            series = series.groupby(["county", "period"], as_index=False)["value"].sum()
        else:
            series = series[series["disaggregation"] == "all"]
        series = series.assign(_k=series["period"].map(period_key)).sort_values("_k")
        if series.empty:
            st.info("No data reported for this indicator yet.")
        else:
            fig = px.line(
                series, x="period", y="value", color="county", markers=True,
                color_discrete_map=county_color, title=meta["name"],
            )
            fig.update_traces(line_width=2, marker_size=8)
            fig.update_layout(hovermode="x unified")
            st.plotly_chart(style(fig), width="stretch")
            st.caption(f"Source: {meta['source']} · Frequency: {meta['frequency']} · Aligns to: {', '.join(meta['alignment'])}")

# ------------------------------------------------------------------ reach
with tab_reach:
    c1, c2 = st.columns(2)
    by_sector = reached.groupby(["county", "sector"], as_index=False).size()
    by_sector["sector"] = by_sector["sector"].map(SECTOR_LABEL)
    fig = px.bar(
        by_sector, x="county", y="size", color="sector", title="People reached by county and sector",
        color_discrete_map={SECTOR_LABEL[s]: SERIES[i] for i, s in enumerate(SECTOR_ORDER)},
        category_orders={"sector": [SECTOR_LABEL[s] for s in SECTOR_ORDER]},
        labels={"size": "People", "county": ""},
    )
    fig.update_traces(marker_line_width=2, marker_line_color="rgba(255,255,255,0.9)")
    c1.plotly_chart(style(fig), width="stretch")

    by_sex = reached.groupby(["sector", "sex"], as_index=False).size()
    by_sex["sector"] = by_sex["sector"].map(SECTOR_LABEL)
    fig = px.bar(
        by_sex, x="size", y="sector", color="sex", orientation="h", barmode="group",
        title="Sex disaggregation by sector", labels={"size": "People", "sector": ""},
        color_discrete_map={"female": SERIES[0], "male": SERIES[1]},
    )
    c2.plotly_chart(style(fig), width="stretch")

    st.markdown(
        f"People with a disability: **{reached['disability'].sum():,}** "
        f"({reached['disability'].mean():.1%}). Capture disability with the "
        "Washington Group Short Set questions in the registration form."
        if len(reached) else "No beneficiaries in the current filter."
    )

# ------------------------------------------------------------------ data quality
with tab_dq:
    st.subheader("Data-quality checks")
    st.caption("Run on every load. Fix issues in the source system (KoboToolbox / field registers), not here.")
    if dq.empty:
        st.success("No issues found.")
    else:
        dq_view = dq.assign(county=dq["county_code"].map(county_name))
        st.dataframe(
            dq_view[["issue", "indicator_id", "county", "period"]], hide_index=True, width="stretch"
        )

# ------------------------------------------------------------------ framework
with tab_fw:
    st.subheader("Results framework (from config/indicators.yaml)")
    fw = ds.indicators.assign(
        sector=ds.indicators["sector"].map(SECTOR_LABEL),
        alignment=ds.indicators["alignment"].map(", ".join),
        disaggregate=ds.indicators["disaggregate"].map(lambda d: ", ".join(d) or "-"),
    )
    st.dataframe(fw, hide_index=True, width="stretch")
