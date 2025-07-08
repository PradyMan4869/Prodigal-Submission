import os
import pickle
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ML Model Prediction API", version="1.0.0")

model = None
MODEL_PATH = os.environ.get("MODEL_PATH", "/app/model/model.pkl")

class HousingFeatures(BaseModel):
    longitude: float
    latitude: float
    housing_median_age: float
    total_rooms: float
    total_bedrooms: float
    population: float
    households: float
    median_income: float
    ocean_proximity: str

@app.on_event("startup")
def load_model():
    global model
    try:
        if os.path.exists(MODEL_PATH):
            with open(MODEL_PATH, "rb") as f:
                model = pickle.load(f)
            logger.info(f"Model loaded successfully from {MODEL_PATH}")
        else:
            logger.warning(f"Model file not found at {MODEL_PATH}. The /predict endpoint will not work until a model is deployed.")
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        model = None

@app.get("/", tags=["General"])
def read_root():
    return {"message": "Welcome to the California Housing Price Prediction API"}

@app.get("/health", tags=["General"])
def health_check():
    status = "OK" if model is not None else "Model not loaded"
    return {"status": status, "model_path": MODEL_PATH}

@app.post("/predict", tags=["Prediction"])
def predict(features: HousingFeatures):
    if model is None:
        raise HTTPException(status_code=503, detail="Model is not loaded. Please trigger the Airflow pipeline to train and deploy a model.")

    try:
        input_data = pd.DataFrame([features.dict()])
        prediction = model.predict(input_data)
        return {"predicted_median_house_value": prediction[0]}
    except Exception as e:
        logger.error(f"Error during prediction: {e}")
        raise HTTPException(status_code=400, detail=f"Error processing prediction: {str(e)}")
