 
# Task 3: High-Throughput API Ingestion with Kafka

This project demonstrates a high-throughput, asynchronous API ingestion system using FastAPI, Kafka, Zookeeper, and Docker. It is designed to handle a massive volume of incoming requests by decoupling the API endpoint from the actual event processing.

## Architecture Overview

The architecture consists of four main components orchestrated by Docker Compose:

- **Producer (`producer` service):** A lightweight FastAPI application that exposes a single `/register_event` endpoint. Its sole responsibility is to receive an event, validate its structure, and publish it to a Kafka topic. This "fire-and-forget" approach makes the API extremely fast and resilient to back-pressure from downstream services.
- **Kafka & Zookeeper (`kafka`, `zookeeper` services):** The core message bus. Kafka provides a durable, scalable, and fault-tolerant log to store incoming events. Zookeeper is used by Kafka for cluster coordination.
- **Consumer (`consumer` service):** A simple Python script that runs as a background worker. It connects to Kafka, subscribes to the event topic, and processes messages one by one. For this demonstration, "processing" simply means logging the event to the console.
- **Load Generator (`load_test.py`):** A local Python script using `aiohttp` to send a large number of concurrent requests to the producer API to simulate high traffic and test the system's performance.

![Kafka Topology Diagram](kafka_topology.png)
*(You would need to create a simple diagram named `kafka_topology.png` showing [Load Test] -> [Producer API] -> [Kafka] -> [Consumer])*

## Environment Setup

### Prerequisites

- Docker
- Docker Compose
- Python 3.x with `aiohttp` installed (`pip install aiohttp`)

## How to Run

1.  **Build and Start All Services:** From the `task-3-kafka/` directory, run the following command. This will build the images and start all four containers. The `--wait` flag ensures that the command will not exit until the Kafka and Producer services are reported as healthy, preventing race conditions.

    ```bash
    docker-compose up --build -d --wait
    ```
    This may take 60-90 seconds on the first run as the services initialize.

2.  **Monitor the Consumer (Optional but Recommended):** In a separate terminal, follow the logs of the consumer to see events as they are processed.

    ```bash
    docker-compose logs -f consumer
    ```
    You should see a message indicating it is connected and waiting for messages.

3.  **Run the Load Test:** In another terminal, execute the load testing script.

    ```bash
    python3 load_test.py
    ```

4.  **Observe the Results:** Watch the `consumer` log terminal. You will see a flood of messages being processed, corresponding to the requests sent by the load test. The `load_test.py` script will print a summary of the requests per second (RPS) it achieved.

## How to Stop

To stop and remove all containers and networks, run:

```bash
docker-compose down
```