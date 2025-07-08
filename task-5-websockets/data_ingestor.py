import asyncio
import websockets
import json
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import logging
from datetime import datetime

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

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Binance WebSocket URL
# We subscribe to multiple streams: btcusdt and ethusdt trade streams
BINANCE_WS_URL = "wss://stream.binance.com:9443/stream?streams=btcusdt@trade/ethusdt@trade"

# --- Database Schema Setup ---
def setup_database():
    """
    Sets up the database table. For high-volume time-series data,
    PostgreSQL's TimescaleDB extension would be ideal, but for this task,
    a hypertable-like plain table with a good index is sufficient.
    """
    with engine.connect() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS trades (
                id BIGSERIAL PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL,
                price NUMERIC NOT NULL,
                timestamp TIMESTAMPTZ(3) NOT NULL
            );
        """))
        # Create an index on timestamp and symbol for fast querying
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_trades_timestamp_symbol ON trades (timestamp DESC, symbol);
        """))
        logging.info("Database table 'trades' and index are set up.")
        # The text() construct is needed to execute raw SQL with SQLAlchemy 2.0+
        connection.commit()


# --- WebSocket Client Logic ---
async def ingest_data():
    """
    Connects to the Binance WebSocket, receives trade data, and inserts it into the database.
    """
    db_session = SessionLocal()
    logging.info(f"Connecting to WebSocket at {BINANCE_WS_URL}")
    
    async with websockets.connect(BINANCE_WS_URL) as websocket:
        logging.info("WebSocket connection successful. Waiting for data...")
        
        while True:
            try:
                message_str = await websocket.recv()
                message = json.loads(message_str)
                
                # The stream format nests the data
                data = message.get('data')
                
                if data and data.get('e') == 'trade':
                    symbol = data['s']
                    price = float(data['p'])
                    # Binance provides event time in milliseconds since epoch
                    ts_ms = data['E']
                    timestamp = datetime.fromtimestamp(ts_ms / 1000.0)
                    
                    # Log the received trade
                    logging.info(f"Received trade: {symbol} @ {price:.2f}")
                    
                    # Insert into database
                    insert_query = text("""
                        INSERT INTO trades (symbol, price, timestamp) VALUES (:symbol, :price, :timestamp)
                    """)
                    db_session.execute(insert_query, {
                        "symbol": symbol,
                        "price": price,
                        "timestamp": timestamp
                    })
                    db_session.commit()

            except websockets.ConnectionClosed:
                logging.warning("WebSocket connection closed. Reconnecting...")
                # The 'async with' block will handle reconnection attempts automatically
                # on the next iteration of a surrounding loop if we had one.
                # For simplicity, we'll let it exit and be restarted by a process manager.
                await asyncio.sleep(5)
                # In a real app, you would have a more robust reconnection loop here.
                # For this task, we will re-run the script.
                break
            except Exception as e:
                logging.error(f"An error occurred: {e}")
                db_session.rollback()
                await asyncio.sleep(5)


if __name__ == "__main__":
    setup_database()
    asyncio.run(ingest_data())