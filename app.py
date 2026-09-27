import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from io import StringIO
import urllib3

st.set_page_config(page_title="Lebanon External Debt Explorer", layout="wide")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATA_URL = "https://linked.aub.edu.lb/pkgcube/data/7e9c8c1012f2ba58a1c9de888cd8449d.csv"

# Load data
@st.cache_data
def load_data():
    response = requests.get(DATA_URL, verify=False, timeout=30)
    response.raise_for_status()
    return pd.read_csv(StringIO(response.text))

try:
    df = load_data()
except Exception as e:
    st.error("The dataset could not be loaded.")
    st.write(e)
    st.stop()

# Prepare data
codes = ["DT.DOD.DECT.GN.ZS", "DT.TDS.DECT.EX.ZS", "DT.DOD.DSTC.IR.ZS"]
debt_data = df[df["Indicator Code"].isin(codes)].copy()
debt_data["Value"] = pd.to_numeric(debt_data["Value"], errors="coerce")
debt_data["refPeriod"] = pd.to_numeric(debt_data["refPeriod"], errors="coerce")

vulnerability = debt_data.pivot_table(
    index="refPeriod", columns="Indicator Code", values="Value", aggfunc="first"
).reset_index()

vulnerability = vulnerability.rename(columns={
    "refPeriod": "Year",
    "DT.DOD.DECT.GN.ZS": "Debt_GNI",
    "DT.TDS.DECT.EX.ZS": "Debt_Service_Exports",
    "DT.DOD.DSTC.IR.ZS": "Short_Term_Reserves"
})

vulnerability = vulnerability.dropna(subset=[
    "Year", "Debt_GNI", "Debt_Service_Exports", "Short_Term_Reserves"
]).copy()

vulnerability["Year"] = vulnerability["Year"].astype(int)
vulnerability = vulnerability.sort_values("Year").reset_index(drop=True)

changes = vulnerability.copy()
changes["Debt_Burden_Change"] = changes["Debt_GNI"].diff()
changes["Servicing_Change"] = changes["Debt_Service_Exports"].diff()
changes["Liquidity_Change"] = changes["Short_Term_Reserves"].diff()
changes = changes.dropna(subset=[
    "Debt_Burden_Change", "Servicing_Change", "Liquidity_Change"
]).reset_index(drop=True)

st.title("Lebanon External Debt Shock & Turning-Point Explorer")
st.write("""
This dashboard explores how key dimensions of Lebanon's external debt changed over time.

The analysis focuses on three dimensions: **debt burden, servicing pressure, and liquidity exposure**.

Use the controls to explore the historical trend and then drill down into a specific year.
""")

with st.expander("Understanding the indicators"):
    st.markdown("""
**Debt Burden — External Debt / GNI**

Shows external debt relative to Lebanon's national income.

**Servicing Pressure — Debt Service / Exports**

Shows external debt-service payments relative to export earnings.

**Liquidity Exposure — Short-Term Debt / Reserves**

Shows short-term external debt relative to international reserves.

The three ratios come from the original dataset.

**Annual Change = Current Year Value − Previous Year Value**

The change is expressed in percentage points (pp).
""")

indicator_map = {
    "Debt Burden": "Debt_Burden_Change",
    "Servicing Pressure": "Servicing_Change",
    "Liquidity Exposure": "Liquidity_Change"
}

indicator_descriptions = {
    "Debt Burden": "External debt relative to national income.",
    "Servicing Pressure": "Debt-service payments relative to export earnings.",
    "Liquidity Exposure": "Short-term external debt relative to international reserves."
}

# Plot 1
st.divider()
st.header("1. External Debt Shock Timeline")
st.write("Choose an indicator and period to examine its year-to-year movements.")

selected_indicator = st.selectbox("Indicator", list(indicator_map.keys()))
column = indicator_map[selected_indicator]
st.caption(indicator_descriptions[selected_indicator])

min_year = int(changes["Year"].min())
max_year = int(changes["Year"].max())

start_year, end_year = st.slider(
    "Period", min_value=min_year, max_value=max_year,
    value=(min_year, max_year), step=1
)

filtered = changes[
    (changes["Year"] >= start_year) & (changes["Year"] <= end_year)
].copy()

fig1 = go.Figure()
fig1.add_trace(go.Scatter(
    x=filtered["Year"], y=filtered[column], mode="lines+markers",
    line=dict(width=3), marker=dict(size=9),
    hovertemplate="<b>Year: %{x}</b><br>Annual Change: %{y:+.2f} pp<extra></extra>"
))
fig1.add_hline(y=0, line_dash="dash", annotation_text="No change",
               annotation_position="bottom right")
fig1.update_layout(
    title=f"{selected_indicator} Shock Timeline: {start_year}–{end_year}",
    xaxis_title="Year", yaxis_title="Annual Change (percentage points)",
    template="plotly_white", height=520, showlegend=False,
    hovermode="x unified", margin=dict(l=50, r=40, t=80, b=50)
)
st.plotly_chart(fig1, use_container_width=True)

st.subheader(f"Interpretation: {start_year}–{end_year}")
valid = filtered.dropna(subset=[column])

if valid.empty:
    st.warning("No observations are available for this selection.")
else:
    largest_increase = valid.loc[valid[column].idxmax()]
    largest_decrease = valid.loc[valid[column].idxmin()]
    increases = int((valid[column] > 0).sum())
    decreases = int((valid[column] < 0).sum())
    average_change = valid[column].mean()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Largest Increase", f"{largest_increase[column]:+.2f} pp",
                  f"Year {int(largest_increase['Year'])}")
    with col2:
        st.metric("Largest Decrease", f"{largest_decrease[column]:+.2f} pp",
                  f"Year {int(largest_decrease['Year'])}")
    with col3:
        st.metric("Average Annual Change", f"{average_change:+.2f} pp")

    st.markdown(f"""
During **{start_year}–{end_year}**, the largest increase in **{selected_indicator.lower()}**
occurred in **{int(largest_increase["Year"])}**, with a change of
**{largest_increase[column]:+.2f} percentage points**.

The largest decrease occurred in **{int(largest_decrease["Year"])}**,
with a change of **{largest_decrease[column]:+.2f} percentage points**.

Across the selected period, **{increases} years showed increases**
and **{decreases} years showed decreases**.
""")

    if increases > decreases:
        st.info("Increases occurred more often than decreases during the selected period.")
    elif decreases > increases:
        st.info("Decreases occurred more often than increases during the selected period.")
    else:
        st.info("The selected period contains the same number of increases and decreases.")

# Plot 2
st.divider()
st.header("2. Turning-Point Profile")
st.write("Select a year from the period above to compare the movement of all three debt dimensions.")

year_options = sorted(filtered["Year"].astype(int).unique().tolist())
if not year_options:
    st.warning("No years are available in the selected period.")
    st.stop()

selected_year = st.select_slider("Year", options=year_options, value=year_options[-1])
selected_row = changes[changes["Year"] == selected_year].iloc[0]

debt_change = float(selected_row["Debt_Burden_Change"])
service_change = float(selected_row["Servicing_Change"])
liquidity_change = float(selected_row["Liquidity_Change"])

dimensions = ["Debt Burden", "Servicing Pressure", "Liquidity Exposure"]
profile_values = [debt_change, service_change, liquidity_change]

fig2 = go.Figure()
for dimension, value in zip(dimensions, profile_values):
    fig2.add_trace(go.Scatter(
        x=[0, value], y=[dimension, dimension], mode="lines",
        line=dict(width=7), showlegend=False, hoverinfo="skip"
    ))
    fig2.add_trace(go.Scatter(
        x=[value], y=[dimension], mode="markers+text",
        marker=dict(size=20), text=[f"{value:+.2f} pp"],
        textposition="middle right" if value >= 0 else "middle left",
        showlegend=False,
        hovertemplate=(
            f"<b>{dimension}</b><br>Year: {selected_year}<br>"
            f"Annual Change: {value:+.2f} pp<extra></extra>"
        )
    ))

fig2.add_vline(x=0, line_dash="dash", annotation_text="No change")

maximum_change = changes[
    ["Debt_Burden_Change", "Servicing_Change", "Liquidity_Change"]
].abs().max().max()

fig2.update_layout(
    title=f"External Debt Turning-Point Profile — {selected_year}",
    xaxis=dict(
        title="Annual Change (percentage points)",
        range=[-maximum_change * 1.25, maximum_change * 1.25]
    ),
    yaxis_title="", template="plotly_white", height=430,
    showlegend=False, margin=dict(l=50, r=100, t=80, b=50)
)
st.plotly_chart(fig2, use_container_width=True)

st.subheader(f"What happened in {selected_year}?")

def movement(value):
    if value > 0:
        return "increased"
    if value < 0:
        return "decreased"
    return "remained unchanged"

st.markdown(f"""
Compared with the previous year:

- **Debt Burden** {movement(debt_change)} by **{abs(debt_change):.2f} percentage points**
- **Servicing Pressure** {movement(service_change)} by **{abs(service_change):.2f} percentage points**
- **Liquidity Exposure** {movement(liquidity_change)} by **{abs(liquidity_change):.2f} percentage points**
""")

all_values = [debt_change, service_change, liquidity_change]

if all(value > 0 for value in all_values):
    st.success("All three indicators increased during this year, so their movements were aligned in the same direction.")
elif all(value < 0 for value in all_values):
    st.success("All three indicators decreased during this year, so their movements were aligned in the same direction.")
else:
    st.info("The three indicators moved in different directions, showing a mixed external-debt profile.")

movements = {
    "Debt Burden": debt_change,
    "Servicing Pressure": service_change,
    "Liquidity Exposure": liquidity_change
}

largest_dimension = max(movements, key=lambda x: abs(movements[x]))
largest_value = movements[largest_dimension]

st.markdown(f"""
The **largest movement** in {selected_year} came from **{largest_dimension}**,
which changed by **{largest_value:+.2f} percentage points**.
""")

# Key insights
st.divider()
st.header("Key Insights")

if 2020 in changes["Year"].values:
    row_2020 = changes[changes["Year"] == 2020].iloc[0]
    st.subheader("2020 — Broad upward movement")
    st.markdown(f"""
All three indicators increased compared with 2019:

- Debt Burden: **{row_2020["Debt_Burden_Change"]:+.2f} pp**
- Servicing Pressure: **{row_2020["Servicing_Change"]:+.2f} pp**
- Liquidity Exposure: **{row_2020["Liquidity_Change"]:+.2f} pp**

The important feature is that all three dimensions moved upward together.
""")

if 2021 in changes["Year"].values:
    row_2021 = changes[changes["Year"] == 2021].iloc[0]
    st.subheader("2021 — Diverging movements")
    st.markdown(f"""
In 2021:

- Debt Burden: **{row_2021["Debt_Burden_Change"]:+.2f} pp**
- Servicing Pressure: **{row_2021["Servicing_Change"]:+.2f} pp**
- Liquidity Exposure: **{row_2021["Liquidity_Change"]:+.2f} pp**

Unlike 2020, the indicators did not move in the same direction.
This shows why external debt should be examined through more than one measure.
""")

st.divider()
st.caption(
    "Data source: dataset provided through the AUB PKGCube publisher. "
    "Original indicator values come from the dataset; annual changes are calculated in the dashboard."
)
