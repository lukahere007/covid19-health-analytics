"""Fetch and reshape COVID-19 data from the disease.sh API.

Kept separate from the Streamlit UI so it can be unit-tested with mocked
HTTP responses.
"""
from __future__ import annotations

from urllib.parse import quote

import pandas as pd
import requests

BASE_URL = "https://disease.sh/v3/covid-19"
TIMEOUT = 10  # seconds


class DataUnavailable(RuntimeError):
    """The API could not be reached or returned no usable data."""


def _get_json(path: str, session=requests, **params):
    try:
        resp = session.get(f"{BASE_URL}/{path}", params=params or None, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        raise DataUnavailable(f"Could not load {path}: {exc}") from exc
    if isinstance(data, dict) and "message" in data and len(data) == 1:
        raise DataUnavailable(data["message"])
    return data


def country_list(session=requests) -> list[str]:
    data = _get_json("countries", session=session)
    return sorted(c["country"] for c in data if c.get("country"))


def country_snapshot(country: str, session=requests) -> dict:
    """Cumulative totals for one country, plus when the source last updated."""
    d = _get_json(f"countries/{quote(country)}", session=session)
    updated = d.get("updated")
    return {
        "cases": d.get("cases"),
        "deaths": d.get("deaths"),
        # Many countries stopped reporting recoveries; the API then returns 0 or null.
        "recovered": d.get("recovered") or None,
        "active": d.get("active"),
        "updated": pd.to_datetime(updated, unit="ms", utc=True) if updated else None,
    }


def country_history(country: str, lastdays: int | str = "all", session=requests) -> pd.DataFrame:
    """Daily new cases and deaths derived from the cumulative JHU time series.

    Returns columns: Date, Cumulative cases, Cumulative deaths, New cases, New deaths.
    """
    d = _get_json(f"historical/{quote(country)}", session=session, lastdays=lastdays)
    timeline = d.get("timeline", d) if isinstance(d, dict) else {}
    if not timeline.get("cases"):
        raise DataUnavailable(f"No historical series for {country}")
    df = pd.DataFrame({
        "Cumulative cases": pd.Series(timeline["cases"]),
        "Cumulative deaths": pd.Series(timeline.get("deaths", {})),
    })
    df.index = pd.to_datetime(df.index, format="%m/%d/%y")
    df = df.sort_index()
    # Daily counts; negative values are data revisions, not "negative cases".
    df["New cases"] = df["Cumulative cases"].diff().clip(lower=0)
    df["New deaths"] = df["Cumulative deaths"].diff().clip(lower=0)
    return df.rename_axis("Date").reset_index()


def trailing_window(hist: pd.DataFrame, days: int) -> pd.DataFrame:
    """The last `days` days that the series actually covers (not the last days before today)."""
    end = hist["Date"].max()
    return hist[hist["Date"] > end - pd.Timedelta(days=days)]
