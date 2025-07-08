import mlflow
from mlflow.tracking import MlflowClient

MLFLOW_TRACKING_URI = "http://mlflow:5000"
MODEL_NAME = "RandomForestRegressor_Housing"

def evaluate_model():
    client = MlflowClient(tracking_uri=MLFLOW_TRACKING_URI)
    
    try:
        latest_versions = client.get_latest_versions(name=MODEL_NAME, stages=["None"])
        if not latest_versions:
            print("No new models in 'None' stage found to evaluate.")
            return

        latest_model = latest_versions[0]
        run_id = latest_model.run_id
        
        print(f"Evaluating model version {latest_model.version} from run {run_id}")
        
        run_data = client.get_run(run_id).data
        rmse = run_data.metrics.get("rmse")

        if rmse is None:
            raise ValueError("RMSE metric not found for the latest model run.")

        print(f"Model RMSE from training run: {rmse}")
        
        # Simple evaluation: If RMSE is below a threshold, transition to Staging
        threshold = 60000 
        if rmse < threshold:
            print(f"RMSE {rmse:.2f} is below threshold {threshold}. Transitioning model to Staging.")
            client.transition_model_version_stage(
                name=MODEL_NAME,
                version=latest_model.version,
                stage="Staging",
                archive_existing_versions=True
            )
        else:
            print(f"RMSE {rmse:.2f} exceeds threshold {threshold}. Archiving model.")
            client.transition_model_version_stage(
                name=MODEL_NAME,
                version=latest_model.version,
                stage="Archived"
            )

    except Exception as e:
        print(f"An error occurred during model evaluation: {e}")
        raise
