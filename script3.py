import os
import requests
import yfinance as yf
import datetime
import mysql.connector
import logging

# ──────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────
DB_HOST = os.getenv("DB_HOST", "35.244.49.8")
DB_NAME = os.getenv("DB_NAME", "stocks")
DB_USER = os.getenv("DB_USER", "Googleclouddata")
DB_PASS = os.getenv("DB_PASS", "%\\LA*HA9[\">;C=pv")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ──────────────────────────────────────────────────────────────
# STEP 1: Get Nifty 50 Symbols
# ──────────────────────────────────────────────────────────────
def get_nifty_50_symbols():
    url_csv = "https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url_csv, headers=headers)
        response.raise_for_status()
        lines = response.text.strip().split("\n")[1:]
        symbols = []

        for line in lines:
            parts = line.split(",")
            name = parts[2].strip().replace("&", "and")
            symbols.append(name + ".NS")

        logging.info(f"✅ Fetched {len(symbols)} Nifty 50 symbols.")
        return symbols
    except Exception as e:
        logging.error(f"❌ Failed to fetch Nifty list: {e}")
        return []

# ──────────────────────────────────────────────────────────────
# STEP 2: Fetch Daily Stock Data
# ──────────────────────────────────────────────────────────────
def fetch_stock_data(symbols):
    try:
        logging.info("⏳ Downloading today's data for all Nifty 50 stocks...")
        data = yf.download(
            tickers=" ".join(symbols),
            period="1d",
            interval="1d",
            group_by="ticker",
            auto_adjust=False,
            threads=True
        )
    except Exception as e:
        logging.error(f"❌ Failed to download stock data: {e}")
        return []

    today = datetime.date.today()
    all_data = []

    for symbol in symbols:
        try:
            stock = data[symbol]
            if stock.empty:
                continue

            latest = stock.iloc[-1]

            record = (
                symbol.replace(".NS", ""),
                str(today),
                float(latest["Open"]),
                float(latest["High"]),
                float(latest["Low"]),
                float(latest["Close"]),
                float(latest.get("Adj Close", latest["Close"])),
                int(latest["Volume"]),
                datetime.datetime.now()
            )
            all_data.append(record)
        except Exception as e:
            logging.warning(f"⚠️ Skipped {symbol} due to error: {e}")

    logging.info(f"✅ Fetched data for {len(all_data)} symbols.")
    return all_data

# ──────────────────────────────────────────────────────────────
# STEP 3: Save to MySQL (fresh table)
# ──────────────────────────────────────────────────────────────
def refresh_mysql_data(records):
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )
        cursor = conn.cursor()

        cursor.execute("DROP TABLE IF EXISTS stock_data;")
        cursor.execute("""
            CREATE TABLE stock_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                ticker VARCHAR(20),
                date DATE,
                open DECIMAL(10,2),
                high DECIMAL(10,2),
                low DECIMAL(10,2),
                close DECIMAL(10,2),
                adj_close DECIMAL(10,2),
                volume BIGINT,
                inserted_at DATETIME,
                UNIQUE KEY unique_ticker_date (ticker, date)
            );
        """)

        cursor.executemany("""
            INSERT INTO stock_data
            (ticker, date, open, high, low, close, adj_close, volume, inserted_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, records)

        conn.commit()
        cursor.close()
        conn.close()
        logging.info("✅ Daily Nifty 50 stock data refreshed in MySQL.")
    except Exception as e:
        logging.error(f"❌ MySQL Error: {e}")

# ──────────────────────────────────────────────────────────────
# MAIN EXECUTION
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    symbols = get_nifty_50_symbols()
    if not symbols:
        logging.error("❌ No symbols fetched. Exiting.")
        exit(1)

    stock_data = fetch_stock_data(symbols)
    if not stock_data:
        logging.error("❌ No stock data downloaded. Exiting.")
        exit(1)

    refresh_mysql_data(stock_data)
