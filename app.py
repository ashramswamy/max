import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
from fpdf import FPDF
import tempfile
import os

st.set_page_config(page_title="📊 Enhanced Stock Market Dashboard", layout="wide")

# --- SIDEBAR ---
st.sidebar.title("📊 Dashboard Controls")
st.sidebar.markdown("""
Welcome to your **Stock Dashboard**!  
Track **Opening, Closing, Volume**, and **% Change** of top companies in real time.
""")

symbols = st.sidebar.multiselect(
    "📌 Select Stocks to View",
    ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX", "IBM", "INTC"],
    default=["AAPL", "MSFT"]
)

start_date = st.sidebar.date_input("🗓 Start Date", datetime.date(2023, 1, 1))
end_date = st.sidebar.date_input("📅 End Date", datetime.date.today())

with st.sidebar.expander("ℹ️ What do these mean?"):
    st.markdown("""
    - **Open**: Price at market open  
    - **Close**: Price at market close  
    - **Volume**: Number of shares traded  
    - **% Change**: Daily percent movement  
    """)

# MAIN
st.title("📈 Enhanced Real-Time Stock Market Dashboard")
st.markdown("View real-time stock prices with interactive **Opening/Closing price trends**, **volume**, and more!")

if symbols:
    data = yf.download(symbols, start=start_date, end=end_date, group_by='ticker', auto_adjust=True)
    st.success("✅ Data successfully loaded!")

    # Show raw data
    preview_data = pd.concat([data[sym].assign(Symbol=sym) for sym in symbols])
    with st.expander("📋 Show Raw Data"):
        st.dataframe(preview_data.head(20), use_container_width=True)

    # Graphs
    def plot_line(title, y_label, column):
        fig = go.Figure()
        for sym in symbols:
            fig.add_trace(go.Scatter(x=data[sym].index, y=data[sym][column], mode='lines', name=sym))
        fig.update_layout(title=title, xaxis_title="Date", yaxis_title=y_label)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("🚀 Opening Price Trend")
    plot_line("Opening Price", "Opening Price (USD)", "Open")

    st.subheader("📉 Closing Price Trend")
    plot_line("Closing Price", "Closing Price (USD)", "Close")

    st.subheader("📊 Volume Traded")
    fig = go.Figure()
    for sym in symbols:
        fig.add_trace(go.Scatter(x=data[sym].index, y=data[sym]["Volume"], mode='lines', stackgroup='one', name=sym))
    fig.update_layout(title="Volume Traded", xaxis_title="Date", yaxis_title="Volume")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📈 Daily % Change")
    fig = go.Figure()
    for sym in symbols:
        pct = data[sym]["Close"].pct_change() * 100
        fig.add_trace(go.Scatter(x=data[sym].index, y=pct, mode='lines', name=sym))
    fig.update_layout(title="Daily % Change", xaxis_title="Date", yaxis_title="Change (%)")
    st.plotly_chart(fig, use_container_width=True)

    # Candlestick chart
    st.subheader("🕯️ Candlestick Chart")
    fig_candle = make_subplots(rows=1, cols=1)
    for sym in symbols:
        fig_candle.add_trace(go.Candlestick(
            x=data[sym].index,
            open=data[sym]["Open"],
            high=data[sym]["High"],
            low=data[sym]["Low"],
            close=data[sym]["Close"],
            name=sym
        ))
    fig_candle.update_layout(title="Candlestick View", xaxis_title="Date", yaxis_title="Price")
    st.plotly_chart(fig_candle, use_container_width=True)

    # Latest Snapshot
    st.subheader("🔍 Latest Market Snapshot")
    snapshot = {
        "Symbol": [],
        "Latest Price": [],
        "Opening Price": [],
        "High": [],
        "Low": [],
        "Volume": []
    }

    for sym in symbols:
        row = data[sym].iloc[-1]
        snapshot["Symbol"].append(sym)
        snapshot["Latest Price"].append(round(row["Close"], 2))
        snapshot["Opening Price"].append(round(row["Open"], 2))
        snapshot["High"].append(round(row["High"], 2))
        snapshot["Low"].append(round(row["Low"], 2))
        snapshot["Volume"].append(int(row["Volume"]))

    df_snapshot = pd.DataFrame(snapshot)
    st.dataframe(df_snapshot)

    # Export CSV
    csv_data = df_snapshot.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button("📥 Download CSV", data=csv_data, file_name="snapshot.csv", mime="text/csv")

    # Create and export PDF
    class PDF(FPDF):
        def header(self):
            self.set_font("Arial", "B", 12)
            self.cell(200, 10, "Stock Market Snapshot", ln=True, align="C")

        def footer(self):
            self.set_y(-15)
            self.set_font("Arial", "I", 8)
            self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

        def add_table(self, df):
            self.set_font("Arial", "", 10)
            col_width = (self.w - 2 * self.l_margin) / len(df.columns)
            th = self.font_size + 2
            for col in df.columns:
                self.cell(col_width, th, col, border=1)
            self.ln(th)
            for i in range(len(df)):
                for col in df.columns:
                    self.cell(col_width, th, str(df.iloc[i][col]), border=1)
                self.ln(th)

    pdf = PDF()
    pdf.add_page()
    pdf.add_table(df_snapshot)

    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp_file.name)
    with open(tmp_file.name, "rb") as f:
        st.sidebar.download_button("📄 Download PDF", data=f, file_name="stock_report.pdf", mime="application/pdf")

else:
    st.warning("👈 Please select at least one stock symbol to view data.")
