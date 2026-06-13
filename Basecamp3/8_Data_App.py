import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ---------- Data Loading ----------
@st.cache_data
def load_data(csv_path: str = "index.csv") -> pd.DataFrame:
    df = pd.read_csv(csv_path, parse_dates=["Date"], date_format="%d-%b-%y")
    df = df.sort_values("Date").reset_index(drop=True)
    return df

df = load_data()

st.title("Index Data anlysis")

# ---------- Sidebar Controls ----------
st.sidebar.header("Controls")

min_date = df["Date"].min().date()
max_date = df["Date"].max().date()

# Date range selection
date_range = st.sidebar.date_input(
    "Select date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

# Make sure we always end up with start_date and end_date (even if only one date picked)
if isinstance(date_range, (list, tuple)):
    if len(date_range) == 2:
        start_date, end_date = date_range
    elif len(date_range) == 1:
        start_date = end_date = date_range[0]
    else:
        # Fallback in weird case – use full range
        start_date, end_date = min_date, max_date
else:
    start_date = end_date = date_range

# Ensure start_date <= end_date
if start_date > end_date:
    start_date, end_date = end_date, start_date

# Range mask (for Tab 1 & 2 views)
mask = (df["Date"].dt.date >= start_date) & (df["Date"].dt.date <= end_date)
df_range = df.loc[mask].copy()

# ---------- Tabs ----------
tab1, tab2 = st.tabs(
    ["📋 Data Table (Day Trend)", "🌋 Volatility Surface"]
)


# TAB 1: Range-sliced data table with Day Trend (circle)

with tab1:
    st.subheader("Day Trend for the date range")

    if df_range.empty:
        st.warning("No data available for the selected date range.")
    else:
        # 0.25% threshold:
        # Green: Close >= Open * (1 + 0.0025)
        # Red  : Close <= Open * (1 - 0.0025)
        # Amber: otherwise
        threshold = 0.0025  # 0.25%

        up_level = df_range["Open"] * (1 + threshold)
        down_level = df_range["Open"] * (1 - threshold)

        is_green = df_range["Close"] >= up_level
        is_red = df_range["Close"] <= down_level

        conditions = [
            is_green,
            is_red,
        ]
        choices_text = ["Green", "Red"]
        candle_text = np.select(conditions, choices_text, default="Amber")

        # Circle indicators: 🟢, 🔴, 🟡
        choices_circle = ["🟢", "🔴"]
        candle_circle = np.select(conditions, choices_circle, default="🟡")

        df_range["Day_Trend"] = candle_circle
        df_range["Day_Trend_Text"] = candle_text

        st.markdown(
            "- **🟢 Green**: Close ≥ Open × (1 + 0.25%)  \n"
            "- **🔴 Red**: Close ≤ Open × (1 − 0.25%)  \n"
            "- **🟡 Amber**: Within ±0.25% of Open"
        )
        
        # Reorder columns 
        df_range['Date_Str'] = df_range['Date'].dt.strftime ("%d-%b-%y")
        cols_order = ["Date_Str", "Open", "High", "Low", "Close", "Day_Trend"]
        # other_cols = [c for c in df_range.columns if c not in cols_order]
        display_df = df_range[cols_order]

        st.dataframe(display_df, width="stretch")



# TAB 2: Rolling Volatility Surface (entire data range)

with tab2:
    st.subheader("Rolling Volatility Surface (for Close Price)")

    # Compute returns from Close
    returns = df["Close"].pct_change()

    # Choose a set of windows for the surface
    vol_windows = [5, 10, 20, 30, 60]

    vol_matrix = []
    for w in vol_windows:
        # Rolling std; scaled to annualized volatility (approx 250 trading days)
        vol = returns.rolling(w).std() * np.sqrt(250)
        vol_matrix.append(vol.values)

    z = np.array(vol_matrix)  # shape: (len(vol_windows), len(df))

    # X-axis: dates, Y-axis: window sizes
    x = df["Date"]
    y = vol_windows

    surface = go.Surface(
        z=z,
        x=x,
        y=y,
        colorscale="Viridis",
        colorbar=dict(title="Volatility"),
    )

    fig_vol = go.Figure(data=[surface])
    fig_vol.update_layout(
        scene=dict(
            xaxis_title="Date",
            yaxis_title="Window (days)",
            zaxis_title="Rolling Volatility (annualized)",
        ),
        margin=dict(l=0, r=0, b=0, t=30),
    )

    st.plotly_chart(fig_vol, width='stretch')