"""Tests with mocked HTTP: no network needed."""
from unittest import mock

import pandas as pd
import pytest
import requests
import streamlit as st
from streamlit.testing.v1 import AppTest

import covid_data as cd

COUNTRIES = [{"country": "USA"}, {"country": "South Korea"}]
SNAPSHOT = {"cases": 1000, "deaths": 10, "recovered": 0, "active": 990, "updated": 1700000000000}
HISTORY = {"country": "USA", "timeline": {
    "cases": {"3/7/23": 100, "3/8/23": 130, "3/9/23": 125, "3/10/23": 160},
    "deaths": {"3/7/23": 1, "3/8/23": 2, "3/9/23": 2, "3/10/23": 4},
}}


def _resp(payload, status=200):
    r = mock.Mock()
    r.json.return_value = payload
    r.raise_for_status.side_effect = (
        requests.HTTPError(f"{status}") if status >= 400 else None)
    return r


def fake_get(url, params=None, timeout=None):
    assert timeout is not None, "every request must set a timeout"
    if url.endswith("/countries"):
        return _resp(COUNTRIES)
    if "/historical/" in url:
        return _resp(HISTORY)
    return _resp(SNAPSHOT)


def test_history_is_daily_not_cumulative():
    with mock.patch("requests.get", fake_get):
        h = cd.country_history("USA")
    assert list(h["New cases"].fillna(-1)) == [-1, 30, 0, 35]  # revision clipped to 0
    assert h["Date"].max() == pd.Timestamp("2023-03-10")


def test_missing_recoveries_become_none():
    with mock.patch("requests.get", fake_get):
        assert cd.country_snapshot("USA")["recovered"] is None


def test_country_name_is_url_encoded():
    seen = []
    with mock.patch("requests.get", lambda url, **kw: seen.append(url) or _resp(SNAPSHOT)):
        cd.country_snapshot("South Korea")
    assert seen[0].endswith("/countries/South%20Korea")


def test_api_message_raises():
    with mock.patch("requests.get", lambda *a, **k: _resp({"message": "Country not found"})):
        with pytest.raises(cd.DataUnavailable):
            cd.country_history("Atlantis")


def test_trailing_window_is_relative_to_last_date():
    with mock.patch("requests.get", fake_get):
        h = cd.country_history("USA")
    assert len(cd.trailing_window(h, 2)) == 2


def test_app_renders_with_mocked_api():
    st.cache_data.clear()
    with mock.patch("requests.get", fake_get):
        at = AppTest.from_file("../app.py", default_timeout=30).run()
    assert not at.exception
    assert [m.value for m in at.metric] == ["1,000", "10", "n/a"]


def test_app_shows_error_when_api_down():
    st.cache_data.clear()
    def down(*a, **k):
        raise requests.ConnectionError("blocked")
    with mock.patch("requests.get", down):
        at = AppTest.from_file("../app.py", default_timeout=30).run()
    assert not at.exception
    assert "unavailable" in at.error[0].value
