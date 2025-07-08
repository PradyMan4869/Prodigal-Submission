# Summary: ML Pipeline Orchestration

This document outlines the challenges faced, architectural decisions made, and potential improvements for the ML pipeline task.

## Challenges Faced

1.  **Inter-Service Communication in Docker**: The primary challenge was orchestrating communication between multiple services (Airflow, Spark, MLflow, FastAPI) within a Docker Compose setup. This required careful configuration of networks, service names, and shared volumes. For instance, Airflow needs to submit jobs to `spark://spark-master:7077`, and all Python scripts need to connect to `http://mlflow:5000`.

2.  **Data Sharing and State Management**: Ensuring that data processed by one stage (e.g., Spark) is available to the next (e.g., PythonOperator for training) required using shared Docker volumes (`spark_data_volume`). Similarly, the final trained model needed to be placed on a shared volume (`shared_model_volume`) for the API service to access it.

3.  **Dependency Management**: Maintaining consistent library versions (especially `scikit-learn`) across the Airflow environment (where the model is trained and pickled) and the FastAPI environment (where it's unpickled and used) was crucial to avoid serialization errors. This was solved by pinning the version in `requirements.txt` for the API.

## Architectural Decisions

1.  **Decoupled Components**: Each component (orchestration, processing, tracking, serving) was designed as a separate, containerized service. This follows microservices principles, making the system modular, scalable, and easier to maintain.

2.  **Spark for ETL**: While Pandas could have handled the dataset size, using Spark for data ingestion and feature engineering was a deliberate choice to demonstrate proficiency in distributed data processing, which is essential for scaling to larger datasets.

3.  **MLflow as the "Single Source of Truth" for Models**: Instead of passing model files directly between Airflow tasks, we used MLflow as a central model registry. The pipeline logs a model, evaluates it, and promotes it through stages (`None` -> `Staging` -> `Production`). The deployment task then fetches the "blessed" model from the registry. This is a robust MLOps pattern that provides auditability, versioning, and governance.

4.  **Airflow for Orchestration**: Airflow was chosen for its maturity, extensive provider ecosystem, and powerful scheduling capabilities. The "Bonus" of daily retraining is implemented simply by setting `schedule='@daily'` in the DAG definition.

## Scope for Improvement

1.  **Configuration Management**: Currently, configurations like MLflow URI or model names are hardcoded in the scripts. In a production system, these should be externalized using Airflow Variables or a dedicated configuration management tool.

2.  **CI/CD Integration**: The entire setup could be integrated into a CI/CD pipeline (e.g., GitHub Actions). This would automate testing, building Docker images, and deploying the entire stack to a staging or production environment.

3.  **Advanced Model Evaluation**: The current evaluation is a simple metric threshold check. A more robust process would involve a separate, held-out test dataset, checking for data drift, and comparing the new model's performance against the currently deployed "Production" model (champion-challenger model).

4.  **Security**: The current setup uses basic auth for Airflow and has no auth on other services. In production, all endpoints should be secured, and secrets (like database passwords) should be managed using a tool like HashiCorp Vault or AWS Secrets Manager, not hardcoded in compose files.

5.  **Data Validation**: Adding a data validation step (e.g., using a library like Great Expectations) after ingestion would make the pipeline more robust by ensuring data quality before it enters the training process.
