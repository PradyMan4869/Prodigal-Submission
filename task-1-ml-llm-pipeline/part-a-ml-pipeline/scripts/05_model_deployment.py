import mlflow
from mlflow.tracking import MlflowClient
import pickle
import os

MLFLOW_TRACKING_URI = "http://mlflow:5000"
MODEL_NAME = "RandomForestRegressor_Housing"

def deploy_best_model(output_model_path: str):
    client = MlflowClient(tracking_uri=MLFLOW_TRACKING_URI)
    
    try:
        staged_versions = client.get_latest_versions(name=MODEL_NAME, stages=["Staging"])
        if not staged_versions:
            print(f"No models in 'Staging' for '{MODEL_NAME}'. Deployment skipped.")
            # This is a valid state, so we don't raise an error. The pipeline can succeed without a new deployment.
            return

        model_to_deploy = staged_versions[0]
        print(f"Found model version {model_to_deploy.version} in Staging. Preparing for deployment.")

        # Load model from MLflow registry
        model_uri = f"models:/{MODEL_NAME}/Staging"
        loaded_model = mlflow.sklearn.load_model(model_uri)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_model_path), exist_ok=True)
        
        # Save the model to the shared volume for the API
        with open(output_model_path, "wb") as f_out:
            pickle.dump(loaded_model, f_out)
        
        print(f"Model successfully saved to {output_model_path}")

        # Transition the model to Production in the registry
        print(f"Transitioning model version {model_to_deploy.version} to Production.")
        client.transition_model_version_stage(
            name=MODEL_NAME,
            version=model_to_deploy.version,
            stage="Production",
            archive_existing_versions=True
        )
        print("Model transitioned to Production stage.")

    except Exception as e:
        print(f"An error occurred during model deployment: {e}")
        raise
