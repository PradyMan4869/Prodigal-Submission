import os
import json
import logging
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from kafka import KafkaProducer
from kafka.errors import KafkaError

# --- Configuration ---
KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
TOPIC_NAME = os.environ.get('TOPIC_NAME', 'events_topic')

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- FastAPI App Initialization ---
# We will create the producer during the startup event
app = FastAPI(
    title="High-Throughput Event API",
    description="An API to register events and send them to a Kafka topic.",
    version="1.0.0"
)

# --- State for Kafka Producer ---
# Use a dictionary to hold the producer state so we can modify it in the startup event
kafka_state = {"producer": None}

# --- Startup Event to Create Producer ---
@app.on_event("startup")
def startup_event():
    logger.info("Application startup: Initializing Kafka producer...")
    retries = 10
    for i in range(retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(','),
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                retries=5,
            )
            # This is a blocking call to ensure connection before we proceed
            if producer.bootstrap_connected():
                kafka_state["producer"] = producer
                logger.info(f"Successfully connected to Kafka at {KAFKA_BOOTSTRAP_SERVERS}")
                return
        except KafkaError as e:
            logger.error(f"Failed to connect to Kafka (attempt {i+1}/{retries}): {e}")
            time.sleep(5)
    
    logger.critical("Could not create Kafka producer after multiple retries. The service will be unhealthy.")

# --- Pydantic Models ---
class Event(BaseModel):
    event_type: str = Field(..., example="user_login")
    user_id: str = Field(..., example="user-123")
    payload: dict = Field(..., example={"source_ip": "192.168.1.100"})

# --- API Endpoints ---
@app.post("/register_event")
async def register_event(event: Event):
    producer = kafka_state.get("producer")
    if not producer:
        raise HTTPException(status_code=503, detail="Kafka producer not available. Service is unhealthy.")
        
    try:
        key = event.user_id.encode('utf-8')
        producer.send(TOPIC_NAME, key=key, value=event.dict())
        return {"status": "success", "message": "Event has been queued for processing."}
    except KafkaError as e:
        logger.error(f"Failed to send message to Kafka: {e}")
        raise HTTPException(status_code=500, detail="Failed to queue event.")

@app.get("/health")
def health_check():
    producer = kafka_state.get("producer")
    if producer and producer.bootstrap_connected():
        return {"status": "ok", "kafka_connected": True}
    return {"status": "error", "kafka_connected": False, "detail": "Kafka producer is not connected."}