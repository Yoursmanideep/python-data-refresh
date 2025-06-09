import requests
import yfinance as yf
import datetime
import mysql.connector

# MySQL Cloud SQL credentials
DB_HOST = "35.244.49.8"
DB_NAME = "stocks"
DB_USER = "Googleclouddata"
DB_PASS = "%\\LA*HA9[\">;C=pv"

def get_nifty_50_symbols():
    headers = {"User-Agent": "Mozilla/5.0"}
    url_csv = "https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv"
    try:
        response = requests.get(url_csv, headers=headers)
        response.raise_for_status()
        lines = response.text.strip().split("\n")[1:]
        symbols = []
        for line in lines:  # Top 50 (full list)
            parts = line.split(",")
            name = parts[2].strip().replace("&", "and")
            symbols.append(name + ".NS")
        return symbols
    except Exception as e:
        print("❌ Failed to fetch Nifty list:", e)
        return []

def fetch_stock_data(symbols):
    all_data = []
    try:
        data = yf.download(" ".join(symbols), period="1d", interval="1d", group_by="ticker", auto_adjust=False)
    except Exception as e:
        print("❌ Failed to download stock data:", e)
        return []

    today = datetime.date.today()

    for symbol in symbols:
        try:
            stock = data[symbol]
            latest = stock.iloc[-1]
            record = (
                symbol.replace(".NS", ""),
                str(today),
                float(latest["Open"]),
                float(latest["High"]),
                float(latest["Low"]),
                float(latest["Close"]),
                float(latest["Adj Close"]) if "Adj Close" in latest else float(latest["Close"]),
                int(latest["Volume"]),
                datetime.datetime.now()
            )
            all_data.append(record)
        except Exception as e:
            print(f"⚠️ Skipped {symbol} due to error: {e}")
    return all_data

def refresh_mysql_data(records):
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )
        cursor = conn.cursor()

        # Drop table to reset ID sequence
        cursor.execute("DROP TABLE IF EXISTS stock_data;")

        # Create fresh table
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

        for record in records:
            cursor.execute("""
                INSERT INTO stock_data
                (ticker, date, open, high, low, close, adj_close, volume, inserted_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, record)

        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Top 50 Nifty stock data refreshed in MySQL.")
    except Exception as e:
        print("❌ MySQL Error:", e)

if __name__ == "__main__":
    symbols = get_nifty_50_symbols()
    if not symbols:
        print("❌ Couldn’t fetch Nifty symbols.")
        exit(1)

    print("⏳ Fetching stock data...")
    stock_data = fetch_stock_data(symbols)
    if not stock_data:
        print("❌ No stock data fetched.")
        exit(1)

    print("⏳ Refreshing data in MySQL...")
    refresh_mysql_data(stock_data)
