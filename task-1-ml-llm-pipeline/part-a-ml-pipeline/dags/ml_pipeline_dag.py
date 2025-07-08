 
from __future__ import annotations

import pendulum

from airflow.models.dag import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

# Hack to allow scripts to be imported from the /scripts directory
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)) + '/../scripts')

from _03_model_training import train_model
from _04_model_evaluation import evaluate_model
from _05_model_deployment import deploy_best_model

SPARK_MASTER = "spark://spark-master:7077"
PROCESSED_DATA_PATH_BASE = "/opt/airflow/processed_data"

with DAG(
    dag_id='ml_pipeline_orchestration',
    default_args={'owner': 'airflow'},
    description='A full-cycle ML pipeline using Airflow, MLflow, Spark, and Docker.',
    schedule='@daily',
    start_date=pendulum.datetime(2023, 1, 1, tz="UTC"),
    catchup=False,
    tags=['mlops', 'spark', 'mlflow'],
) as dag:
    
    start_pipeline = BashOperator(
        task_id='start_pipeline',
        bash_command='echo "Starting ML Pipeline..."',
    )
    
    data_ingestion = BashOperator(
        task_id='data_ingestion_spark',
        bash_command=(
            f"spark-submit --master {SPARK_MASTER} "
            "/opt/airflow/scripts/01_data_ingestion.py "
            "--input_path /opt/airflow/data/housing.csv "
            f"--output_path {PROCESSED_DATA_PATH_BASE}/ingested_data"
        )
    )

    feature_engineering = BashOperator(
        task_id='feature_engineering_spark',
        bash_command=(
            f"spark-submit --master {SPARK_MASTER} "
            "/opt/airflow/scripts/02_feature_engineering.py "
            f"--input_path {PROCESSED_DATA_PATH_BASE}/ingested_data "
            f"--output_path {PROCESSED_DATA_PATH_BASE}/featured_data"
        )
    )

    model_training = PythonOperator(
        task_id='model_training',
        python_callable=train_model,
        op_kwargs={
            'spark_path': f'file://{PROCESSED_DATA_PATH_BASE}/featured_data'
        },
    )

    model_evaluation = PythonOperator(
        task_id='model_evaluation',
        python_callable=evaluate_model,
    )
    
    model_deployment = PythonOperator(
        task_id='model_deployment',
        python_callable=deploy_best_model,
        op_kwargs={
            'output_model_path': '/opt/airflow/model/model.pkl'
        }
    )

    end_pipeline = BashOperator(
        task_id='end_pipeline',
        bash_command='echo "ML Pipeline Finished Successfully!"',
    )
    
    start_pipeline >> data_ingestion >> feature_engineering >> model_training >> model_evaluation >> model_deployment >> end_pipeline