 
# Task 5 Summary: Real-Time Price Capture

This document outlines the challenges, key architectural decisions, and potential improvements for the Binance WebSocket data ingestion project.

## Challenges Faced

1.  **Handling High-Frequency Data:** The Binance trade stream pushes multiple messages per second. The primary challenge was designing an ingestor that could parse and insert this data into a database without becoming a bottleneck or falling behind.

2.  **Timestamp Precision:** Capturing the price is meaningless without an accurate timestamp. The Binance API provides a millisecond-precision Unix epoch timestamp. It was crucial to ensure that the database schema (`TIMESTAMPTZ(3)`) and the Python `datetime` objects could store this level of precision without loss.

3.  **Efficient Time-Series Querying:** Storing the data is only half the battle. The queries for "price at a specific time" and "high/low in an interval" require efficient database lookups. A naive table scan on a large dataset would be unacceptably slow.

## Architectural Decisions

1.  **Asynchronous I/O with `asyncio` and `websockets`:** The choice of `asyncio` for the ingestor was deliberate. It allows the script to efficiently wait for new data from the WebSocket (`await websocket.recv()`) without blocking the entire program. This is the standard, high-performance approach for handling I/O-bound tasks like network communication in Python.

2.  **PostgreSQL as a Time-Series Database:** While a purpose-built TSDB like InfluxDB is a strong choice, using PostgreSQL demonstrates the ability to optimize a general-purpose relational database for a specific task. Key decisions here were:
    - **`TIMESTAMPTZ(3)` Data Type:** This was chosen specifically to handle timezones correctly (`TZ`) and to store the required millisecond precision (`3`).
    - **Composite Index:** A B-tree index was created on `(timestamp DESC, symbol)`. This is a highly effective index for the required queries. It allows the database to very quickly find the latest records (`ORDER BY timestamp DESC`) and to efficiently filter by a specific `symbol`.

3.  **Decoupled Ingestor and Querier:** The system was designed as two separate scripts. This is a realistic architecture where data ingestion is a long-running background service, and analysis or querying is done on-demand by other applications or users.

4.  **Robust Connection Handling:** The `data_ingestor.py` script includes basic error handling and logging for connection issues. The use of the `async with websockets.connect(...)` context manager provides a clean way to handle the connection lifecycle.

## Scope for Improvement

1.  **Use a Purpose-Built Time-Series Database (TSDB):** For a production system at massive scale, migrating to a specialized TSDB like **TimescaleDB** (an extension for PostgreSQL) or **InfluxDB** would be the next logical step. These systems offer superior ingestion performance, dramatically better compression (reducing storage costs), and a richer set of time-oriented query functions (e.g., time bucketing, gap-filling, moving averages).

2.  **Batch Inserts:** The current implementation commits to the database after every single message. This results in a high number of small transactions, which can limit throughput. A more optimized approach would be to batch messages in memory (e.g., for 1 second or 100 messages) and perform a single, bulk `INSERT` operation. This significantly reduces database overhead. The `psycopg2.extras.execute_values` function is excellent for this.

3.  **Robust Reconnection and Backoff Logic:** The current ingestor exits on a closed connection. A production service should implement an exponential backoff retry strategy. If the connection drops, it would wait 1 second, then 2, then 4, etc., before retrying, to avoid hammering the server during an outage.

4.  **Data Validation and Schema:** The script currently assumes the incoming JSON data is always in the correct format. A production system would use Pydantic to validate the incoming message structure, ensuring that a malformed message from the source doesn't crash the ingestor or corrupt the data.

5.  **Service Management and Monitoring:** The script is run manually. In a real environment, it would be managed by a process supervisor like `systemd` or run as a long-lived container in Kubernetes. It would also expose metrics (e.g., messages processed per second, current connection status) for monitoring with Prometheus/Grafana.