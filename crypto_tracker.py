import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import time

st.set_page_config(page_title="Crypto Portfolio Tracker", layout="wide")

# =========================
# THEME TOGGLE
# =========================
theme = st.sidebar.radio("Theme", ["Light Mode", "Dark Mode"])

plotly_template = "plotly_dark" if theme == "Dark Mode" else "plotly_white"

# =========================
# SAFE API FETCH WITH RETRY
# =========================
def fetch_with_retry(url, params=None, retries=3, timeout=10):
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            time.sleep(1)
    return None

# =========================
# GET MARKET DATA
# =========================
@st.cache_data(ttl=120)
def get_crypto_prices():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 50,
        "page": 1,
        "sparkline": False
    }

    data = fetch_with_retry(url, params)

    if data and isinstance(data, list):
        df = pd.DataFrame(data)
        return df

    return pd.DataFrame()

# =========================
# GET HISTORICAL DATA
# =========================
@st.cache_data(ttl=300)
def get_historical_data(coin_id, days):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": days}

    data = fetch_with_retry(url, params)

    if data and "prices" in data:
        df = pd.DataFrame(data["prices"], columns=["timestamp", "price"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        return df

    return pd.DataFrame()

# =========================
# LOAD DATA SAFELY
# =========================
crypto_df = get_crypto_prices()

if crypto_df.empty or "name" not in crypto_df.columns:
    st.error("⚠ Unable to load crypto data. API may be temporarily unavailable.")
    st.stop()

# =========================
# APP TITLE
# =========================
st.title("📊 Crypto Portfolio Tracker (Production Safe)")

# =========================
# PORTFOLIO SECTION
# =========================
st.sidebar.header("💼 Your Portfolio")

coin_names = crypto_df["name"].tolist()

selected_coins = st.sidebar.multiselect("Select Coins", coin_names)

portfolio_data = []
total_value = 0

for coin in selected_coins:
    amount = st.sidebar.number_input(
        f"Amount of {coin}",
        min_value=0.0,
        step=0.01,
        key=coin
    )

    coin_row = crypto_df.loc[crypto_df["name"] == coin]

    if not coin_row.empty:
        price = coin_row["current_price"].values[0]
        value = amount * price
        total_value += value

        portfolio_data.append({
            "Coin": coin,
            "Amount": amount,
            "Price ($)": price,
            "Value ($)": round(value, 2)
        })

if portfolio_data:
    st.subheader("📌 Portfolio Overview")
    st.dataframe(pd.DataFrame(portfolio_data), use_container_width=True)
    st.metric("Total Portfolio Value ($)", f"{round(total_value, 2):,}")

# =========================
# PRICE ANALYSIS SECTION
# =========================
st.subheader("📈 Price Pattern Analysis")

coin_choice = st.selectbox("Select Coin for Analysis", crypto_df["id"])

timeframe = st.radio("Timeframe", ["1 Day", "7 Days"])

days = 1 if timeframe == "1 Day" else 7

hist_df = get_historical_data(coin_choice, days)

if not hist_df.empty:

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=hist_df["timestamp"],
        y=hist_df["price"],
        mode="lines",
        name="Price"
    ))

    # Add simple moving average for pattern visibility
    hist_df["SMA"] = hist_df["price"].rolling(window=10).mean()

    fig.add_trace(go.Scatter(
        x=hist_df["timestamp"],
        y=hist_df["SMA"],
        mode="lines",
        name="Moving Avg",
        line=dict(dash="dash")
    ))

    fig.update_layout(
        template=plotly_template,
        title=f"{coin_choice.capitalize()} Price Trend ({timeframe})",
        xaxis_title="Time",
        yaxis_title="Price (USD)"
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("Historical data unavailable for this coin.")

# =========================
# AUTO REFRESH INFO
# =========================
st.caption("🔄 Data refreshes every 2 minutes. If data fails, refresh the page.")
