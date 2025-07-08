 
# Task 5: Real-Time Binance Price Capture via WebSockets

This project demonstrates a high-performance data ingestion pipeline that connects to the Binance public WebSocket stream, captures live trade data for BTC/USDT and ETH/USDT with millisecond precision, and persists it into a PostgreSQL database for real-time analysis.

## Architecture Overview

The system is composed of two primary components: a persistent data ingestor and a query script, backed by a containerized PostgreSQL database.

- **Data Ingestor (`data_ingestor.py`):** A Python script utilizing the `asyncio` and `websockets` libraries to maintain a persistent connection to the Binance multi-stream endpoint. It asynchronously receives JSON messages, parses the relevant trade data (symbol, price, timestamp), and inserts them into the database in real-time. The script is designed to be resilient, logging errors and handling connection logic gracefully.

- **PostgreSQL Database (`db` service):** A containerized PostgreSQL instance, managed by Docker Compose. The database schema is designed for time-series data, featuring a `trades` table with a `TIMESTAMPTZ(3)` column to store timestamps with millisecond precision. A composite B-tree index on `(timestamp DESC, symbol)` is created to ensure high-performance queries, especially for time-based lookups and filtering by symbol.

- **Query Script (`db_queries.py`):** A separate Python script that connects to the database and demonstrates the ability to retrieve the stored data. It includes functions to perform the three required queries:
  1.  Fetch the most recent price for a given symbol.
  2.  Find the price at the time closest to a specific timestamp.
  3.  Calculate the highest and lowest price within a given time interval (e.g., the last minute).

This architecture effectively decouples data ingestion from data analysis, a common pattern in real-time systems.

## Environment Setup

### Prerequisites

- Docker
- Docker Compose
- Python 3.x

### Configuration

Create a `.env` file in the project root directory (`task-5-websockets/`) to configure the database connection.

```ini
# Database Configuration for PostgreSQL
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=binance_prices
DB_HOST=localhost
DB_PORT=5433 # Using a non-default port to avoid conflicts
```

## How to Run

1.  **Start the Database Container:** From the `task-5-websockets/` directory, start the PostgreSQL service in the background.

    ```bash
    docker-compose up -d
    ```

2.  **Install Python Dependencies:** Install the required libraries into your local environment.

    ```bash
    pip install -r requirements.txt
    ```

3.  **Start the Data Ingestor (Terminal 1):** Run this script to begin capturing live trade data. It will connect to the database and the WebSocket stream.

    ```bash
    python3 data_ingestor.py
    ```
    You will see a log of incoming trades. **Let this run for at least 2-3 minutes** to accumulate a meaningful amount of data.

4.  **Run Queries (Terminal 2):** While the ingestor is running, open a new terminal and execute the query script to see the results.

    ```bash
    python3 db_queries.py
    ```
    This will print the results for the latest price, price at a specific time, and the high/low over the last minute.

## How to Stop

1.  Press `CTRL+C` in the data ingestor's terminal to stop the client.
2.  Run the following command to stop and remove the database container and its associated data volume.
    ```bash
    docker-compose down -v
    ```