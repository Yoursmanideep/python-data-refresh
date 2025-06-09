import os
import requests
import yfinance as yf
import datetime
import pandas as pd
import mysql.connector
import logging

# ──────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ──────────────────────────────────────────────────────────────
# STEP 1: Get Top 25 Nifty Symbols
# ──────────────────────────────────────────────────────────────
def get_nifty_25_symbols():
    url_csv = "https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url_csv, headers=headers)
        response.raise_for_status()
        lines = response.text.strip().split("\n")[1:]
        symbols = []

        for line in lines[:25]:
            parts = line.split(",")
            name = parts[2].strip().replace("&", "and")
            symbols.append(name + ".NS")

        logging.info(f"✅ Nifty 25: {symbols}")
        return symbols
    except Exception as e:
        logging.error(f"❌ Failed to fetch Nifty list: {e}")
        return []

# ──────────────────────────────────────────────────────────────
# STEP 2: Fetch Monthly OHLCV Data
# ──────────────────────────────────────────────────────────────
def fetch_monthly_data(symbols):
    try:
        logging.info("⏳ Downloading monthly stock data...")
        data = yf.download(
            tickers=" ".join(symbols),
            start="1990-01-01",
            end=datetime.datetime.now().strftime("%Y-%m-%d"),
            interval="1mo",
            group_by="ticker",
            threads=True
        )
        logging.info("✅ Data downloaded successfully.")
        return data
    except Exception as e:
        logging.error(f"❌ Failed to download stock data: {e}")
        return None

# ──────────────────────────────────────────────────────────────
# STEP 3: Identify Monthly Winners
# ──────────────────────────────────────────────────────────────
def get_monthly_winners(data, symbols):
    monthly_winners = []
    months = pd.date_range("1990-01-01", datetime.date.today(), freq="MS")

    for month in months:
        month_records = []

        for symbol in symbols:
            try:
                symbol_df = data[symbol].dropna(subset=["Open", "Close"])
                row = symbol_df[(symbol_df.index.month == month.month) & (symbol_df.index.year == month.year)]
                if row.empty:
                    continue

                row = row.iloc[0]
                gain_pct = ((row["Close"] - row["Open"]) / row["Open"]) * 100

                month_records.append({
                    "symbol": symbol.replace(".NS", ""),
                    "date": row.name.date(),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "adj_close": float(row.get("Adj Close", row["Close"])),
                    "volume": int(row["Volume"]),
                    "gain_pct": round(gain_pct, 2),
                    "inserted_at": datetime.datetime.now()
                })

            except Exception as e:
                logging.warning(f"⚠️ Skipped {symbol} in {month.strftime('%Y-%m')} due to: {e}")

        if month_records:
            best = max(month_records, key=lambda x: x["gain_pct"])
            monthly_winners.append(best)

    logging.info(f"📊 Total monthly winners: {len(monthly_winners)}")
    return monthly_winners

# ──────────────────────────────────────────────────────────────
# STEP 4: Store Winners to MySQL
# ──────────────────────────────────────────────────────────────
def save_to_mysql(monthly_winners):
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )
        cursor = conn.cursor()

        cursor.execute("DROP TABLE IF EXISTS monthly_winners;")
        cursor.execute("""
            CREATE TABLE monthly_winners (
                id INT AUTO_INCREMENT PRIMARY KEY,
                ticker VARCHAR(20),
                date DATE,
                open DECIMAL(10,2),
                high DECIMAL(10,2),
                low DECIMAL(10,2),
                close DECIMAL(10,2),
                adj_close DECIMAL(10,2),
                volume BIGINT,
                inserted_at DATETIME
            );
        """)

        for record in monthly_winners:
            cursor.execute("""
                INSERT INTO monthly_winners 
                (ticker, date, open, high, low, close, adj_close, volume, inserted_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                record["symbol"],
                record["date"],
                record["open"],
                record["high"],
                record["low"],
                record["close"],
                record["adj_close"],
                record["volume"],
                record["inserted_at"]
            ))

        conn.commit()
        cursor.close()
        conn.close()
        logging.info("✅ Monthly winners saved to MySQL.")
    except Exception as e:
        logging.error(f"❌ MySQL Error: {e}")

# ──────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    symbols = get_nifty_25_symbols()
    data = fetch_monthly_data(symbols)
    if data is not None:
        winners = get_monthly_winners(data, symbols)
        if winners:
            save_to_mysql(winners)
