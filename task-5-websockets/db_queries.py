import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import logging

# --- Configuration & Setup ---
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Database connection
DB_USER = os.getenv('POSTGRES_USER')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('POSTGRES_DB')
DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

try:
    engine = create_engine(DATABASE_URL)
    connection = engine.connect()
    logging.info("Database connection successful.")
except Exception as e:
    logging.error(f"Failed to connect to database: {e}")
    exit()

def get_latest_price(symbol: str):
    """
    Demonstrates querying for the latest price of a given symbol.
    """
    logging.info(f"\n--- Query 1: Getting latest price for {symbol} ---")
    query = text("""
        SELECT price, timestamp FROM trades
        WHERE symbol = :symbol
        ORDER BY timestamp DESC
        LIMIT 1;
    """)
    result = connection.execute(query, {"symbol": symbol}).fetchone()
    
    if result:
        price, timestamp = result
        print(f"Latest price for {symbol}: {price:.2f} at {timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
    else:
        print(f"No data found for symbol {symbol}.")

def get_price_at_specific_time(symbol: str, target_time: str):
    """
    Demonstrates querying for the price at a specific second.
    Since trades may not happen at the exact millisecond, we find the one closest to it.
    """
    logging.info(f"\n--- Query 2: Getting price for {symbol} near {target_time} ---")
    query = text("""
        SELECT price, timestamp FROM trades
        WHERE symbol = :symbol
        ORDER BY ABS(EXTRACT(EPOCH FROM (timestamp - CAST(:target_time AS TIMESTAMPTZ))))
        LIMIT 1;
    """)
    result = connection.execute(query, {"symbol": symbol, "target_time": target_time}).fetchone()
    
    if result:
        price, timestamp = result
        print(f"Closest price for {symbol} near {target_time}: {price:.2f} at {timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
    else:
        print(f"No data found for symbol {symbol}.")

def get_high_low_in_interval(symbol: str, interval_minutes: int = 1):
    """
    Demonstrates querying for the highest and lowest price in the last N minutes.
    """
    logging.info(f"\n--- Query 3: Getting Highest/Lowest price for {symbol} in the last {interval_minutes} minute(s) ---")
    query = text("""
        SELECT
            MAX(price) AS highest_price,
            MIN(price) AS lowest_price
        FROM trades
        WHERE
            symbol = :symbol AND
            timestamp >= NOW() - INTERVAL ':interval_minutes minutes';
    """)
    # Note: SQLAlchemy doesn't love interval binding directly, so we format it.
    # A more robust solution might use a stored procedure or more complex query building.
    # For this task, we will format the interval into the string.
    # THIS IS GENERALLY UNSAFE, but acceptable for a controlled value like an integer.
    safe_query_str = f"""
        SELECT
            MAX(price) AS highest_price,
            MIN(price) AS lowest_price
        FROM trades
        WHERE
            symbol = :symbol AND
            timestamp >= NOW() - INTERVAL '{interval_minutes} minutes';
    """
    query = text(safe_query_str)

    result = connection.execute(query, {"symbol": symbol}).fetchone()
    
    if result and result.highest_price is not None:
        highest, lowest = result
        print(f"In the last {interval_minutes} minute(s) for {symbol}:")
        print(f"  Highest Price: {highest:.2f}")
        print(f"  Lowest Price:  {lowest:.2f}")
    else:
        print(f"No data found for symbol {symbol} in the last {interval_minutes} minute(s).")


if __name__ == "__main__":
    # Get the current time to use for the second query
    # We'll subtract 30 seconds to make sure there's likely data around that time
    from datetime import datetime, timedelta
    target_dt = datetime.now() - timedelta(seconds=30)
    target_time_str = target_dt.strftime('%Y-%m-%d %H:%M:%S')

    # --- Run Demonstrations ---
    get_latest_price("BTCUSDT")
    get_latest_price("ETHUSDT")
    
    get_price_at_specific_time("BTCUSDT", target_time_str)
    
    get_high_low_in_interval("BTCUSDT", interval_minutes=1)

    # Clean up the connection
    connection.close()