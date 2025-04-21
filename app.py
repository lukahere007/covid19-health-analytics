
# app.py

import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="COVID-19 Global Dashboard", layout="wide")

st.title("🌍 Real-Time COVID-19 Tracker")
st.markdown("Powered by [disease.sh](https://disease.sh) API")

# Sidebar - Country selection
countries_url = "https://disease.sh/v3/covid-19/countries"
response = requests.get(countries_url)
country_data = response.json()
country_names = sorted([country["country"] for country in country_data])
country = st.sidebar.selectbox("Select a Country", country_names, index=country_names.index("USA"))

# Fetch country-specific data
data_url = f"https://disease.sh/v3/covid-19/countries/{country}"
resp = requests.get(data_url).json()

st.subheader(f"📊 Current Statistics for {country}")
cols = st.columns(3)
cols[0].metric("Total Cases", f"{resp['cases']:,}")
cols[1].metric("Total Deaths", f"{resp['deaths']:,}")
cols[2].metric("Recovered", f"{resp['recovered']:,}")

# Pie chart for active, recovered, deaths
pie_df = pd.DataFrame({
    "Status": ["Active", "Recovered", "Deaths"],
    "Count": [resp["active"], resp["recovered"], resp["deaths"]]
})
fig_pie = px.pie(pie_df, names="Status", values="Count", title="Current Case Distribution")
st.plotly_chart(fig_pie, use_container_width=True)

# Historical data for line chart
hist_url = f"https://disease.sh/v3/covid-19/historical/{country}?lastdays=60"
hist_resp = requests.get(hist_url).json()
if "timeline" in hist_resp:
    timeline = hist_resp["timeline"]
else:
    timeline = hist_resp  # some countries don't have "timeline"

cases = pd.DataFrame(timeline["cases"].items(), columns=["Date", "Cases"])
deaths = pd.DataFrame(timeline["deaths"].items(), columns=["Date", "Deaths"])
cases["Date"] = pd.to_datetime(cases["Date"])
deaths["Date"] = pd.to_datetime(deaths["Date"])
df_combined = pd.merge(cases, deaths, on="Date")

st.subheader("📈 Trends Over the Last 60 Days")
fig_line = px.line(df_combined, x="Date", y=["Cases", "Deaths"], labels={"value": "Count", "Date": "Date"}, title="COVID-19 Trends")
st.plotly_chart(fig_line, use_container_width=True)

st.caption("Built with Streamlit + Plotly | Data from disease.sh API")
