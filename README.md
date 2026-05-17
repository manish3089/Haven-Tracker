# Haven Tracker

A market analysis tool for studying flight-to-safety behaviour — days when one asset rises while another falls, often a signal that investors are moving out of risk.

Live: [haventracker.streamlit.app](https://haventracker.streamlit.app/)

---

## What it does

You pick any two tickers from Yahoo Finance and a date range. The dashboard pulls historical prices, computes daily returns, and flags days where the two assets moved in opposite directions. You can also drop in dates for global events to see how they line up with the data.

The default pair is Gold (GC=F) and EUR/USD, but it works with any combination — equities, commodities, currencies, indices.

---

## Analysis

- Daily % change for both assets, plotted over time
- Flight-to-safety day count and rate across the full period
- Yearly breakdown of how often the divergence occurred
- Scatter of all trading days with flight-to-safety days highlighted
- Table of individual days with prices and returns

---

## Stack

- Python — pandas, yfinance, matplotlib
- Streamlit
- Jupyter Notebook (original exploration)