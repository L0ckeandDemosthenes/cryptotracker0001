import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# ---------------------------
# CONFIG
# ---------------------------
st.set_page_config(page_title="Crypto Portfolio Tracker", layout="wide")

# ---------------------------
# DARK / LIGHT MODE TOGGLE
# ---------------------------
theme = st.sidebar.radio("Select Theme", ["Light Mode", "Dark Mode"])

if theme == "Dark Mode":
    st.markdown("""
        <style>
        body { background-color: #0e1117; color: white; }
        </style>
    """, unsafe_allow_html=True)

# ---------------------------
# FETCH LIVE CRYPTO DATA
# ---------------------------
@st.cache_data(ttl=60)
def get_crypto_prices():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 50,
        "page": 1,
        "sparkline": False
    }
    response = requests.get(url, params=params)
    return pd.DataFrame(response.json())

# ---------------------------
# HISTORICAL DATA
# ---------------------------
@st.cache_data(ttl=300)
def get_historical_data(coin_id, days=7):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": days}
    response = requests.get(url, params=params)
    data = response.json()
    prices = data["prices"]
    df = pd.DataFrame(prices, columns=["timestamp", "price"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df

# ---------------------------
# LOAD DATA
# ---------------------------
crypto_df = get_crypto_prices()

st.title("📊 Crypto Portfolio Tracker")

# ---------------------------
# PORTFOLIO INPUT
# ---------------------------
st.sidebar.header("Your Portfolio")

selected_coins = st.sidebar.multiselect(
    "Select Cryptos",
    crypto_df["name"].tolist()
)

portfolio = []

for coin in selected_coins:
    amount = st.sidebar.number_input(f"Amount of {coin}", min_value=0.0, step=0.01)
    portfolio.append((coin, amount))

# ---------------------------
# PORTFOLIO VALUE CALCULATION
# ---------------------------
total_value = 0
portfolio_table = []

for coin, amount in portfolio:
    price = crypto_df.loc[crypto_df["name"] == coin, "current_price"].values[0]
    value = amount * price
    total_value += value

    portfolio_table.append({
        "Coin": coin,
        "Amount": amount,
        "Current Price ($)": price,
        "Value ($)": round(value, 2)
    })

if portfolio_table:
    st.subheader("💼 Portfolio Overview")
    st.dataframe(pd.DataFrame(portfolio_table))
    st.metric("Total Portfolio Value ($)", round(total_value, 2))

# ---------------------------
# PRICE PATTERN ANALYSIS
# ---------------------------
st.subheader("📈 Price Pattern Analysis")

coin_choice = st.selectbox("Choose a coin for analysis", crypto_df["id"])

timeframe = st.radio("Timeframe", ["1 Day", "7 Days"])

days = 1 if timeframe == "1 Day" else 7

hist_data = get_historical_data(coin_choice, days=days)

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=hist_data["timestamp"],
    y=hist_data["price"],
    mode="lines",
    name="Price"
))

fig.update_layout(
    title=f"{coin_choice.capitalize()} Price Trend ({timeframe})",
    xaxis_title="Time",
    yaxis_title="Price (USD)",
    template="plotly_dark" if theme == "Dark Mode" else "plotly_white"
)

st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# AUTO REFRESH
# ---------------------------
st.caption("🔄 Prices auto-refresh every 60 seconds")
