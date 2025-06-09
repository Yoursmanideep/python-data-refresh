import requests
import yfinance as yf
import datetime
import pandas as pd
import mysql.connector

# MySQL Cloud SQL credentials
DB_HOST = "35.244.49.8"
DB_NAME = "stocks"
DB_USER = "Googleclouddata"
DB_PASS = "%\\LA*HA9[\">;C=pv"

def get_nifty_25_symbols():
    headers = {"User-Agent": "Mozilla/5.0"}
    url_csv = "https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv"
    try:
        response = requests.get(url_csv, headers=headers)
        response.raise_for_status()
        lines = response.text.strip().split("\n")[1:]
        symbols = []
        for line in lines[:25]:
            parts = line.split(",")
            name = parts[2].strip().replace("&", "and")
            symbols.append(name + ".NS")
        print("✅ Nifty 25:", symbols)
        return symbols
    except Exception as e:
        print("❌ Failed to fetch Nifty list:", e)
        return []

def fetch_monthly_data(symbols):
    try:
        print("⏳ Downloading monthly data (from earliest to today)...")
        data = yf.download(
            tickers=" ".join(symbols),
            start="1990-01-01",  # This will auto-trim to the earliest available per stock
            end=datetime.datetime.now().strftime("%Y-%m-%d"),
            interval="1mo",
            group_by="ticker",
            threads=True
        )
        print("✅ Data downloaded.")
        return data
    except Exception as e:
        print("❌ Failed to download stock data:", e)
        return None

def get_monthly_winners(data, symbols):
    monthly_winners = []
    months = pd.date_range("1990-01-01", datetime.date.today(), freq="MS")

    for month in months:
        month_records = []

        for symbol in symbols:
            try:
                symbol_df = data[symbol]
                symbol_df = symbol_df.dropna(subset=["Open", "Close"])
                row = symbol_df[(symbol_df.index.month == month.month) & (symbol_df.index.year == month.year)]

                if row.empty:
                    continue

                row = row.iloc[0]
                open_price = row["Open"]
                close_price = row["Close"]
                gain_pct = ((close_price - open_price) / open_price) * 100

                month_records.append({
                    "symbol": symbol.replace(".NS", ""),
                    "date": row.name.date(),
                    "open": float(open_price),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(close_price),
                    "adj_close": float(row["Adj Close"]) if "Adj Close" in row and not pd.isna(row["Adj Close"]) else float(close_price),
                    "volume": int(row["Volume"]),
                    "gain_pct": gain_pct
                })
            except Exception as e:
                print(f"⚠️ Skipped {symbol} in {month.strftime('%Y-%m')} due to: {e}")

        if month_records:
            best = max(month_records, key=lambda x: x["gain_pct"])
            best["inserted_at"] = datetime.datetime.now()
            monthly_winners.append(best)

    print(f"📊 Total monthly winners fetched: {len(monthly_winners)}")
    return monthly_winners

def save_to_mysql(monthly_winners):
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )
        cursor = conn.cursor()

        # Drop and recreate table so ID starts from 1 every time
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
        print("✅ Best monthly performers saved to MySQL.")
    except Exception as e:
        print("❌ MySQL Error:", e)

if __name__ == "__main__":
    symbols = get_nifty_25_symbols()
    data = fetch_monthly_data(symbols)
    if data is not None:
        winners = get_monthly_winners(data, symbols)
        if winners:
            save_to_mysql(winners)
