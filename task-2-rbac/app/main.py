from fastapi import FastAPI
from .database import engine, Base, SessionLocal
from tenacity import retry, stop_after_attempt, wait_fixed, after_log
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# This is the tenacity retry decorator. It will try to connect 5 times, waiting 5 seconds between tries.
@retry(
    stop=stop_after_attempt(5),
    wait=wait_fixed(5),
    after=after_log(logger, logging.INFO),
)
def init_db():
    try:
        # Try to create a session to check the connection.
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        logger.info("Database connection successful.")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise e

# The on_startup event handler for FastAPI
def create_tables_on_startup():
    logger.info("--- Initializing database ---")
    init_db()
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully.")

app = FastAPI(
    title="Prodigal AI - RBAC Task",
    on_startup=[create_tables_on_startup] # Use the startup event
)

# Your routers and root endpoint go here...
from .routers import auth, rbac, rbac_guest
app.include_router(auth.router)
app.include_router(rbac.router)
app.include_router(rbac_guest.router)

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to the RBAC API. Visit /docs for documentation."}