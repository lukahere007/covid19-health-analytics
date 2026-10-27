# COVID-19 Country Dashboard

[![CI](https://github.com/lukahere007/covid19-health-analytics/actions/workflows/ci.yml/badge.svg)](https://github.com/lukahere007/covid19-health-analytics/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A Streamlit dashboard that pulls COVID-19 data for any country from the public [disease.sh](https://disease.sh) API
and shows cumulative totals plus daily new cases and deaths.

**This is a look back at the pandemic period, not a live tracker.** The daily time series comes from
Johns Hopkins CSSE, which stopped updating in March 2023, and most countries have since stopped or reduced
reporting. The app labels every chart with the last date the series actually covers. An earlier version
called itself "real-time", which was not accurate.

Hosted version: <https://lukahere007-covid-dashboard.streamlit.app> (Streamlit Community Cloud. It may need
a minute to wake up and may lag behind this repo.)

## What it shows

- **Cumulative totals** (cases, deaths, recoveries) for the selected country, with the API's refresh time.
  Recoveries show "n/a" where the country no longer reports them, rather than a misleading 0.
- **Daily new cases and deaths** for a chosen window ending at the last reported date, as bars plus a
  7-day rolling mean.

## How it works

| File | Role |
|---|---|
| `covid_data.py` | API calls (10 s timeout, HTTP errors and "country not found" become one `DataUnavailable` error), URL-encodes country names, converts the cumulative series to daily counts |
| `app.py` | Streamlit UI. Responses are cached for an hour with `st.cache_data`. If the API is down, the app shows a message instead of crashing. |
| `tests/test_app.py` | 7 pytest tests with a mocked API, including a full render of the app with Streamlit's `AppTest` and the API-down path |

Fixes compared with the first version:

- The "last 60 days" line chart plotted **cumulative** totals, labelled as trends. It now shows daily new counts,
  computed as differences of the cumulative series. Downward revisions are set to zero.
- "Last 60 days" meant the 60 days before *today*. For a series that ends in 2023, that window has no new data.
  The window now ends at the last reported date.
- No timeouts, no error handling and no caching: one slow or failed request crashed the page, and every
  interaction re-downloaded everything.
- Country names with spaces (e.g. "South Korea") were not URL-encoded.

## Run it

```bash
git clone https://github.com/lukahere007/covid19-health-analytics.git
cd covid19-health-analytics
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

pytest                 # offline tests, API mocked
streamlit run app.py   # needs internet access to disease.sh
```

## Limitations

- The app could not be checked against the live API while this version was prepared (outbound access to
  disease.sh was blocked). The tests and a headless `streamlit run` passed with the API mocked or unreachable.
- Reported case counts depend heavily on testing volume and reporting practice, so they are not comparable
  across countries or over time without adjustment (per-capita rates, excess mortality).
- disease.sh is a free community API with no uptime guarantee.

## License

MIT, see [LICENSE](LICENSE).
