"""COVID-19 country dashboard (Streamlit). Author: Luke Wamalwa."""
import pandas as pd
import plotly.express as px
import streamlit as st

import covid_data as cd

st.set_page_config(page_title="COVID-19 Country Dashboard", layout="wide")
st.title("COVID-19 Country Dashboard")
st.markdown(
    "Data from the [disease.sh](https://disease.sh) API. The daily time series comes from "
    "Johns Hopkins CSSE, which **stopped updating in March 2023**, so the charts show the "
    "pandemic period, not current conditions."
)


@st.cache_data(ttl=3600, show_spinner=False)
def load_countries():
    return cd.country_list()


@st.cache_data(ttl=3600, show_spinner=False)
def load_snapshot(country):
    return cd.country_snapshot(country)


@st.cache_data(ttl=3600, show_spinner=False)
def load_history(country):
    return cd.country_history(country, lastdays="all")


try:
    countries = load_countries()
except cd.DataUnavailable as exc:
    st.error(f"The disease.sh API is unavailable right now. {exc}")
    st.stop()

default = countries.index("USA") if "USA" in countries else 0
country = st.sidebar.selectbox("Country", countries, index=default)
window = st.sidebar.slider("Days to show (ending at the last reported date)", 30, 1200, 365, step=30)


def fmt(x):
    return "n/a" if x is None or pd.isna(x) else f"{int(x):,}"


# ── Cumulative totals ──────────────────────────────────────────
try:
    snap = load_snapshot(country)
    st.subheader(f"Cumulative totals: {country}")
    cols = st.columns(3)
    cols[0].metric("Total cases", fmt(snap["cases"]))
    cols[1].metric("Total deaths", fmt(snap["deaths"]))
    cols[2].metric("Recovered", fmt(snap["recovered"]))
    if snap["recovered"] is None:
        st.caption("Recoveries are no longer reported for this country, so active cases cannot be estimated.")
    if snap["updated"] is not None:
        st.caption(f"API response timestamp: {snap['updated']:%Y-%m-%d %H:%M} UTC. "
                   "This is when the API refreshed, not when the country last reported.")
except cd.DataUnavailable as exc:
    st.warning(f"Totals unavailable for {country}: {exc}")

# ── Daily series ───────────────────────────────────────────────
try:
    hist = load_history(country)
except cd.DataUnavailable as exc:
    st.warning(f"Historical series unavailable for {country}: {exc}")
    st.stop()

last = hist["Date"].max()
recent = cd.trailing_window(hist, window)
st.subheader(f"Daily new cases and deaths, {window} days to {last:%d %b %Y}")
st.caption("Daily values are differences of the cumulative series, with a 7-day rolling mean. "
           "Downward revisions are set to zero.")

c1, c2 = st.columns(2)
for col, metric in zip((c1, c2), ("New cases", "New deaths")):
    plot_df = recent.assign(**{"7-day mean": recent[metric].rolling(7, min_periods=1).mean()})
    fig = px.bar(plot_df, x="Date", y=metric, opacity=0.4, title=metric)
    fig.add_scatter(x=plot_df["Date"], y=plot_df["7-day mean"], mode="lines", name="7-day mean")
    col.plotly_chart(fig, use_container_width=True)

st.caption("Built with Streamlit + Plotly | Data: disease.sh (Johns Hopkins CSSE, Worldometers)")
