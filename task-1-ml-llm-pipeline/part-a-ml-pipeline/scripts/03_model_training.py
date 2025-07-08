import mlflow
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.metrics import mean_squared_error
import numpy as np

MLFLOW_TRACKING_URI = "http://mlflow:5000"
MLFLOW_EXPERIMENT_NAME = "CaliforniaHousing_Prediction"
MODEL_REGISTRY_NAME = "RandomForestRegressor_Housing"

def train_model(spark_path: str):
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)

    df = pd.read_parquet(spark_path.replace("file://", ""))
    X = df.drop("median_house_value", axis=1)
    y = df["median_house_value"]

    categorical_features = ["ocean_proximity"]
    numerical_features = X.columns.drop(categorical_features)

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numerical_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ], remainder='passthrough')

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    with mlflow.start_run() as run:
        print("Starting MLflow run...")
        n_estimators, max_depth = 100, 10
        mlflow.log_params({"n_estimators": n_estimators, "max_depth": max_depth})

        rf_pipeline = Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('regressor', RandomForestRegressor(n_estimators=n_estimators, max_depth=max_depth, random_state=42, n_jobs=-1))
        ])

        print("Training model...")
        rf_pipeline.fit(X_train, y_train)

        predictions = rf_pipeline.predict(X_test)
        rmse = np.sqrt(mean_squared_error(y_test, predictions))
        
        print(f"RMSE: {rmse}")
        mlflow.log_metric("rmse", rmse)
        
        mlflow.sklearn.log_model(
            sk_model=rf_pipeline,
            artifact_path="model",
            registered_model_name=MODEL_REGISTRY_NAME
        )
        print(f"Model logged to MLflow with name: {MODEL_REGISTRY_NAME}")
