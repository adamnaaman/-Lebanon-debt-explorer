# Lebanon External Debt Shock & Turning-Point Explorer

An interactive Streamlit dashboard exploring changes in Lebanon's external debt indicators.
## Live Dashboard

https://9sb5zujzv2i6faectyljnz.streamlit.app/
## Dashboard

The application focuses on three dimensions:

- Debt Burden — External Debt / GNI
- Servicing Pressure — Debt Service / Exports
- Liquidity Exposure — Short-Term Debt / Reserves

Users can select an indicator, choose a historical period, and drill down into individual years.

## Visualizations

### 1. External Debt Shock Timeline
Shows the annual change in the selected debt indicator across the chosen period.

### 2. Turning-Point Profile
Compares the annual changes in all three debt dimensions for a selected year.

## Interactivity

The dashboard includes linked controls. The selected historical period determines which years are available in the Turning-Point Profile.

## Data

The application uses the dataset provided through the AUB PKGCube publisher.

## Run Locally

```bash
streamlit run app.py
