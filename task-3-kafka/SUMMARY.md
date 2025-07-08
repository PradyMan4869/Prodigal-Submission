 
# Task 3 Summary: High-Throughput API Ingestion

This document describes the challenges, architectural decisions, and potential improvements for the Kafka-based event ingestion system.

## Challenges Faced

1.  **Service Startup Order & Race Conditions:** The primary challenge was managing the startup dependencies between the services.
    - The `producer` and `consumer` services would often start before the `kafka` broker was fully initialized and ready to accept connections, leading to connection errors.
    - The `producer` API itself had an internal race condition where its web server would start accepting traffic before its internal `KafkaProducer` client had successfully connected to the broker.

2.  **Healthcheck Brittleness:** Initial attempts to create a healthcheck for the Kafka container using its own command-line tools (`kafka-topics`) proved unreliable within the minimal Docker image environment, as the tools were not on the default path or required specific configurations. A similar issue occurred with the `producer` healthcheck when `curl` was not present in the base image.

## Architectural Decisions

1.  **Decoupled Architecture:** The core design decision was to decouple the API from the worker via a message queue (Kafka). This is a standard pattern for building scalable and resilient systems. It allows the API to remain responsive under heavy load and ensures no data is lost if the processing workers are temporarily slow or unavailable.

2.  **Multi-Stage Healthchecks in Docker Compose:** To solve the race conditions, a robust, multi-stage healthcheck strategy was implemented in `docker-compose.yml`:
    - The `kafka` service uses the `cub kafka-ready` command, which is the officially recommended tool for health-checking Confluent platform images.
    - The `producer` service has its own `/health` endpoint that only returns success when its internal Kafka client is connected.
    - The `depends_on` condition `service_healthy` was used to create a dependency graph, ensuring that `kafka` is fully ready before the `producer` and `consumer` even attempt to start.

3.  **Application-Level Retry Logic:** The `producer`'s FastAPI application was modified to initialize its Kafka client during a startup event, wrapped in a `tenacity`-style retry loop. This makes the application itself resilient and guarantees it will not report as healthy until it is fully ready to perform its function.

4.  **Explicit `curl` Installation:** To fix the failing producer healthcheck, `curl` was explicitly installed in the `producer`'s Dockerfile via `apt-get`. This decision highlights the importance of not assuming the presence of common tools in minimal base images.

## Scope for Improvement

1.  **Error Handling & Dead-Letter Queue (DLQ):** The current consumer logs messages but doesn't handle processing failures. A production system would implement a try/except block around the processing logic. If processing fails after several retries, the message would be sent to a separate "dead-letter queue" (another Kafka topic) for manual inspection, preventing a single bad message from blocking the entire consumer.

2.  **Scalable Consumers:** While the architecture is scalable, we only deployed one consumer instance. In Kubernetes or by using `docker-compose scale`, we could easily run multiple instances of the consumer within the same `consumer_group`. Kafka would automatically balance the topic partitions among them, increasing processing throughput.

3.  **Schema Enforcement:** The current system sends raw JSON. In a production environment, a schema registry (like Confluent Schema Registry) should be used with a format like Avro or Protobuf. This enforces a contract between the producer and consumer, prevents data corruption from schema changes, and provides more efficient serialization.

4.  **Monitoring and Metrics:** The system lacks observability. A production setup would integrate with Prometheus and Grafana. The producer would expose metrics like the number of events produced, and the consumer would expose metrics like messages processed and consumer lag (how far behind it is from the latest message).
