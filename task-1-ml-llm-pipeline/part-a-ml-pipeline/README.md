# Task 1, Part A: ML Pipeline Orchestration

This project demonstrates a full-cycle MLOps pipeline using Airflow, MLflow, Spark, and Docker to train and deploy a house price prediction model.

## Architecture Overview

- **Orchestration**: Apache Airflow schedules and manages the entire pipeline.
- **Data Processing**: Apache Spark is used for scalable data ingestion and feature engineering.
- **ML Lifecycle**: MLflow tracks experiments, versions models, and manages the model registry.
- **Model Serving**: A FastAPI application serves the deployed model via a REST API.
- **Containerization**: All services (Airflow, MLflow, Spark, API) are containerized with Docker for reproducibility.

### Data Flow

1.  **Data Ingestion**: The Airflow DAG triggers a Spark job to read the raw `housing.csv`, clean it, and save it as a Parquet file.
2.  **Feature Engineering**: A second Spark job reads the cleaned data and creates new features, saving the result as another Parquet file.
3.  **Model Training**: A Python task reads the featured data, trains a `scikit-learn` RandomForest model, and logs the model, parameters, and metrics to MLflow. The new model version is registered in the MLflow Model Registry.
4.  **Model Evaluation**: The next task fetches the latest model from the registry, checks its performance (RMSE) against a predefined threshold, and promotes it to the "Staging" stage if it passes.
5.  **Model Deployment**: The final task fetches the "Staging" model, saves it as a `.pkl` file to a shared volume, and promotes it to "Production" in the registry. The FastAPI service automatically loads this new model file.

## Environment Setup & How to Run

### Prerequisites

-   Docker and Docker Compose
-   A terminal or command prompt

### Steps

1.  **Place Data**: Download `housing.csv` from Kaggle and place it in the `task-1-ml-llm-pipeline/part-a-ml-pipeline/data/` directory.

2.  **Build and Start Services**: Navigate to the `task-1-ml-llm-pipeline/part-a-ml-pipeline/` directory and run:
    ```bash
    docker-compose up --build -d
    ```
    This will start all services. The `-d` flag runs them in detached mode. The initial setup might take a few minutes as Airflow initializes its database.

3.  **Access Services**:
    -   **Airflow UI**: `http://localhost:8080` (Login: admin / admin)
    -   **MLflow UI**: `http://localhost:5001`
    -   **Spark Master UI**: `http://localhost:9090`
    -   **Prediction API Docs**: `http://localhost:8000/docs`

4.  **Trigger the Pipeline**:
    -   In the Airflow UI, find the `ml_pipeline_orchestration` DAG.
    -   Unpause the DAG using the toggle on the left.
    -   Click the "play" button on the right to trigger a manual run.

5.  **Monitor Execution**:
    -   Watch the DAG run progress in the Airflow UI.
    -   Check the MLflow UI to see the new experiment run, logged parameters, metrics, and registered model versions.
    -   Check the Spark UI to see the completed `data_ingestion` and `feature_engineering` jobs.

6.  **Test the API**:
    -   Once the pipeline completes successfully, the model will be deployed.
    -   Go to the API docs at `http://localhost:8000/docs`.
    -   Use the `/predict` endpoint to test inference. Here is a sample JSON payload:
    ```json
    {
      "longitude": -122.23,
      "latitude": 37.88,
      "housing_median_age": 41.0,
      "total_rooms": 880.0,
      "total_bedrooms": 129.0,
      "population": 322.0,
      "households": 126.0,
      "median_income": 8.3252,
      "ocean_proximity": "NEAR BAY"
    }
    ```

7.  **Shutdown**: To stop all services and remove the containers, run:
    ```bash
    docker-compose down -v
    ```
    The `-v` flag removes the named volumes, including the Postgres database and logs.
