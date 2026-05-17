import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import date
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="Market Volatility Dashboard", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    h1 { font-size: 1.6rem; font-weight: 600; }
    .stMetric [data-testid="metric-container"] {
        background: #f8f8f8;
        padding: 0.75rem 1rem;
        border-radius: 6px;
        border: 1px solid #e8e8e8;
    }
</style>
""", unsafe_allow_html=True)

# ─── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Parameters")

    ticker1 = st.text_input("First ticker (Yahoo Finance)", value="GC=F", help="e.g. GC=F for Gold futures")
    ticker2 = st.text_input("Second ticker (Yahoo Finance)", value="EURUSD=X", help="e.g. EURUSD=X for Euro/USD")

    st.markdown("---")
    st.subheader("Date range")
    start_date = st.date_input("From", value=date(2015, 1, 2))
    end_date = st.date_input("To", value=date.today())

    st.markdown("---")
    st.subheader("Global events (optional)")
    st.caption("Overlay vertical markers on the % change chart.")
    events_text = st.text_area(
        "One per line: YYYY-MM-DD, Label",
        height=140,
        placeholder="2022-02-24, Russia-Ukraine war\n2020-03-11, COVID declared\n2023-03-10, SVB collapse",
    )

    run = st.button("Run analysis", type="primary", use_container_width=True)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def parse_events(text):
    events = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(",", 1)
        if len(parts) == 2:
            try:
                events.append({"date": pd.to_datetime(parts[0].strip()), "label": parts[1].strip()})
            except Exception:
                pass
    return events


# ─── Header ──────────────────────────────────────────────────────────────────

st.title("Gold / FX Volatility and Flight-to-Safety Dashboard")
st.caption(
    "Compares daily returns of two assets and identifies days when they move in opposite directions — "
    "a common signal for risk-off behaviour in markets."
)

if not run:
    st.info("Set your parameters in the sidebar and click Run analysis.")
    st.stop()


# ─── Data fetch ───────────────────────────────────────────────────────────────

if not ticker1 or not ticker2:
    st.error("Please enter both tickers.")
    st.stop()

if start_date >= end_date:
    st.error("Start date must be before end date.")
    st.stop()

with st.spinner("Downloading price data from Yahoo Finance..."):
    try:
        raw = yf.download(
            [ticker1, ticker2],
            start=str(start_date),
            end=str(end_date),
            group_by="ticker",
            auto_adjust=True,
            progress=False,
        )
    except Exception as e:
        st.error(f"Download failed: {e}")
        st.stop()

if raw.empty:
    st.error("No data returned. Check your tickers and date range.")
    st.stop()

try:
    s1 = raw[ticker1]["Close"].rename(ticker1)
    s2 = raw[ticker2]["Close"].rename(ticker2)
except KeyError as e:
    st.error(f"Ticker not found in the downloaded data: {e}")
    st.stop()

if s1.isna().all() or s2.isna().all():
    st.error("One or both tickers returned no valid price data.")
    st.stop()

data = pd.DataFrame({ticker1: s1, ticker2: s2}).ffill().dropna()

df = data.copy()
df[ticker1 + "_pct"] = df[ticker1].pct_change() * 100
df[ticker2 + "_pct"] = df[ticker2].pct_change() * 100
df = df.dropna()


# ─── Flight-to-safety ────────────────────────────────────────────────────────

flight_days = df[(df[ticker1 + "_pct"] > 0) & (df[ticker2 + "_pct"] < 0)]
total_days = len(df)
fts_count = len(flight_days)
fts_pct = round(fts_count / total_days * 100, 2) if total_days else 0
avg_t1_on_fts = round(flight_days[ticker1 + "_pct"].mean(), 3) if fts_count else 0.0
avg_t2_on_fts = round(flight_days[ticker2 + "_pct"].mean(), 3) if fts_count else 0.0
events = parse_events(events_text)


# ─── Metrics ─────────────────────────────────────────────────────────────────

st.markdown("### Overview")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Trading days", f"{total_days:,}")
c2.metric("Flight-to-safety days", f"{fts_count:,}")
c3.metric("Flight-to-safety rate", f"{fts_pct}%")
c4.metric(f"Avg {ticker1} on FTS days", f"+{avg_t1_on_fts}%")
c5.metric(f"Avg {ticker2} on FTS days", f"{avg_t2_on_fts}%")

st.markdown("---")


# ─── Chart 1: Daily % change ─────────────────────────────────────────────────

st.markdown("### Daily % change")

fig1, ax1 = plt.subplots(figsize=(13, 4))
ax1.plot(df.index, df[ticker1 + "_pct"], lw=0.75, alpha=0.85, label=ticker1)
ax1.plot(df.index, df[ticker2 + "_pct"], lw=0.75, alpha=0.85, label=ticker2)
ax1.axhline(0, color="#bbb", lw=0.6, linestyle="--")

y_top = df[[ticker1 + "_pct", ticker2 + "_pct"]].max().max()
for ev in events:
    dt = ev["date"]
    if df.index.min() <= dt <= df.index.max():
        ax1.axvline(dt, color="red", linestyle="--", lw=0.9, alpha=0.65)
        ax1.annotate(
            ev["label"],
            xy=(dt, y_top * 0.9),
            xytext=(5, 0),
            textcoords="offset points",
            fontsize=7,
            color="red",
            rotation=70,
            va="top",
        )

ax1.set_ylabel("% change")
ax1.legend(fontsize=9)
ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax1.xaxis.set_major_locator(mdates.YearLocator())
ax1.tick_params(axis="both", labelsize=8)
fig1.tight_layout()
st.pyplot(fig1)


# ─── Chart 2: Flight-to-safety days per year ─────────────────────────────────

st.markdown("### Flight-to-safety days per year")
st.caption(f"{ticker1} positive and {ticker2} negative on the same trading day")

yearly = flight_days.copy()
yearly["year"] = pd.to_datetime(yearly.index).year
yearly_counts = yearly["year"].value_counts().sort_index()

fig2, ax2 = plt.subplots(figsize=(10, 3.5))
bars = ax2.bar(yearly_counts.index.astype(str), yearly_counts.values, color="#e07b39", width=0.6)
ax2.bar_label(bars, fontsize=8, padding=3)
ax2.set_xlabel("Year")
ax2.set_ylabel("Days")
ax2.tick_params(axis="both", labelsize=8)
fig2.tight_layout()
st.pyplot(fig2)


# ─── Chart 3: Scatter ────────────────────────────────────────────────────────

left, right = st.columns([1, 2])

with left:
    st.markdown("### Return scatter")
    st.caption("Red = flight-to-safety day. Each dot is one trading day.")

    fig3, ax3 = plt.subplots(figsize=(5, 4))
    non_fts = df[~df.index.isin(flight_days.index)]
    ax3.scatter(
        non_fts[ticker2 + "_pct"], non_fts[ticker1 + "_pct"],
        alpha=0.2, s=5, color="#999", label="Other days", rasterized=True
    )
    ax3.scatter(
        flight_days[ticker2 + "_pct"], flight_days[ticker1 + "_pct"],
        alpha=0.5, s=7, color="#d93030", label="Flight-to-safety"
    )
    ax3.axhline(0, color="#ccc", lw=0.6)
    ax3.axvline(0, color="#ccc", lw=0.6)
    ax3.set_xlabel(f"{ticker2} daily % chg", fontsize=9)
    ax3.set_ylabel(f"{ticker1} daily % chg", fontsize=9)
    ax3.legend(fontsize=8)
    ax3.tick_params(labelsize=8)
    fig3.tight_layout()
    st.pyplot(fig3)

with right:
    st.markdown("### Recent flight-to-safety days")

    display = (
        flight_days[[ticker1, ticker2, ticker1 + "_pct", ticker2 + "_pct"]]
        .sort_index(ascending=False)
        .rename(columns={
            ticker1 + "_pct": f"{ticker1} % chg",
            ticker2 + "_pct": f"{ticker2} % chg",
        })
    )
    display.index = display.index.strftime("%Y-%m-%d")

    st.dataframe(
        display.head(25).style.format({
            ticker1: "{:.2f}",
            ticker2: "{:.4f}",
            f"{ticker1} % chg": "{:+.3f}%",
            f"{ticker2} % chg": "{:+.3f}%",
        }),
        use_container_width=True,
        height=400,
    )
    st.caption(f"Showing the 25 most recent of {fts_count} total flight-to-safety days.")