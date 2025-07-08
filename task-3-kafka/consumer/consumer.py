import os
import json
import logging
import time
from kafka import KafkaConsumer
from kafka.errors import KafkaError

# --- Configuration ---
KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
TOPIC_NAME = os.environ.get('TOPIC_NAME', 'events_topic')
CONSUMER_GROUP = os.environ.get('CONSUMER_GROUP', 'logging_group')

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_consumer():
    """
    Creates and returns a Kafka consumer, with retry logic for initial connection.
    """
    retries = 5
    for i in range(retries):
        try:
            consumer = KafkaConsumer(
                TOPIC_NAME,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(','),
                group_id=CONSUMER_GROUP,
                auto_offset_reset='earliest',  # Start reading at the earliest message
                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                # This ensures we don't get stuck waiting for a full batch
                consumer_timeout_ms=1000 
            )
            logger.info(f"Successfully connected to Kafka and subscribed to topic '{TOPIC_NAME}'")
            return consumer
        except KafkaError as e:
            logger.error(f"Failed to connect to Kafka (attempt {i+1}/{retries}): {e}")
            time.sleep(5) # Wait before retrying
    return None

def main():
    """
    Main loop to consume messages from Kafka.
    """
    consumer = create_consumer()

    if not consumer:
        logger.critical("Could not create Kafka consumer after multiple retries. Exiting.")
        return

    logger.info("Consumer started. Waiting for messages...")
    try:
        while True:
            # The poll method fetches messages. The timeout (in ms) is how long to block.
            # A dictionary of topic-partition to list of records is returned.
            for topic_partition, messages in consumer.poll(timeout_ms=5000).items():
                for message in messages:
                    # 'message' is a ConsumerRecord object
                    logger.info(
                        f"Received message: Partition={message.partition}, "
                        f"Offset={message.offset}, Key={message.key.decode('utf-8')}, "
                        f"Value={message.value}"
                    )
                    # In a real application, this is where you would:
                    # - Store the data in a database
                    # - Trigger another process
                    # - Perform some computation
    except KeyboardInterrupt:
        logger.info("Shutting down consumer...")
    finally:
        if consumer:
            consumer.close()

if __name__ == '__main__':
    main()