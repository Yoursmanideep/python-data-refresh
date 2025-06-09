import requests
import yfinance as yf
import datetime
import mysql.connector
import pandas as pd

# MySQL Cloud SQL credentials
DB_HOST = "35.244.49.8"
DB_NAME = "stocks"
DB_USER = "Googleclouddata"
DB_PASS = "%\\LA*HA9[\">;C=pv"  # Properly escaped

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
        return symbols
    except Exception as e:
        print("❌ Failed to fetch Nifty list:", e)
        return []

def fetch_yearly_returns(symbols):
    all_yearly_returns = {}

    try:
        data = yf.download(
            tickers=symbols,
            start="1992-01-01",  # From as early as possible
            end=datetime.date.today().strftime("%Y-%m-%d"),
            interval="1mo",
            group_by="ticker",
            auto_adjust=False,
            threads=True
        )
    except Exception as e:
        print("❌ Failed to download stock data:", e)
        return {}

    for symbol in symbols:
        try:
            df = data[symbol].dropna()
            df.index = pd.to_datetime(df.index)
            df = df.resample('Y').agg({
                'Open': 'first',
                'Close': 'last'
            }).dropna()
            df['return_pct'] = ((df['Close'] - df['Open']) / df['Open']) * 100
            for year, row in df.iterrows():
                year_int = year.year
                if year_int not in all_yearly_returns:
                    all_yearly_returns[year_int] = []
                all_yearly_returns[year_int].append({
                    "symbol": symbol.replace(".NS", ""),
                    "return_pct": round(row["return_pct"], 2)
                })
        except Exception as e:
            print(f"⚠️ Skipped {symbol} due to error: {e}")
    return all_yearly_returns

def identify_top_performers(yearly_returns):
    top_performers = []
    for year in sorted(yearly_returns.keys()):
        companies = yearly_returns[year]
        if not companies:
            continue
        best = max(companies, key=lambda x: x["return_pct"])
        top_performers.append((year, best["symbol"], best["return_pct"]))
    return top_performers

def store_in_mysql(records):
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )
        cursor = conn.cursor()

        # Drop the old table to reset auto-increment ID from 1
        cursor.execute("DROP TABLE IF EXISTS yearly_top_performers;")

        cursor.execute("""
        CREATE TABLE yearly_top_performers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            year INT,
            company VARCHAR(50),
            return_pct DECIMAL(6,2),
            UNIQUE KEY unique_year (year)
        );
        """)

        for record in records:
            year, company, return_pct = record
            cursor.execute("""
                INSERT INTO yearly_top_performers (year, company, return_pct)
                VALUES (%s, %s, %s)
            """, (year, company, return_pct))

        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Yearly top performers stored in MySQL.")
    except Exception as e:
        print("❌ MySQL Error:", e)

if __name__ == "__main__":
    symbols = get_nifty_25_symbols()
    print("⏳ Fetching historical stock data...")
    yearly_returns = fetch_yearly_returns(symbols)
    print("⏳ Identifying best performers...")
    top_performers = identify_top_performers(yearly_returns)
    print("📊 Top performers by year:")
    for t in top_performers:
        print(t)
    store_in_mysql(top_performers)
