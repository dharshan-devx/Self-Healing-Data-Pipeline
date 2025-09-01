from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.dummy import DummyOperator
from datetime import datetime, timedelta
import random
import os
import subprocess

# -------------------------------------------------------------------
# Utility functions (simulate or call your scripts)
# -------------------------------------------------------------------

def produce_data():
    """Run Kafka producer to generate streaming data."""
    subprocess.run(["python", "/opt/airflow/data_source/producer.py"], check=True)

def validate_data(**context):
    """Run Great Expectations validation on raw data."""
    result = subprocess.run(
        ["great_expectations", "checkpoint", "run", "your_checkpoint"],
        capture_output=True, text=True
    )
    # If GE checkpoint fails, send to quarantine
    if result.returncode != 0:
        return "quarantine_data"
    return "load_to_postgres"

def quarantine_data():
    """Move bad records to quarantine folder."""
    os.makedirs("/opt/airflow/quarantine", exist_ok=True)
    with open("/opt/airflow/quarantine/bad_records.txt", "a") as f:
        f.write("Quarantined record at {}\n".format(datetime.utcnow()))

def load_to_postgres():
    """Load clean data into Postgres silver tables."""
    # Simplified example — you may replace with psycopg2/sqlalchemy code
    print("✅ Clean data loaded into Postgres (silver table).")

def spark_transform():
    """Run Spark job to process silver data → artifacts (gold)."""
    subprocess.run(["spark-submit", "/opt/airflow/spark_jobs/streaming_job.py"], check=True)

def healthcheck():
    """Dummy self-healing health check."""
    status = random.choice(["ok", "fail"])
    if status == "fail":
        raise Exception("❌ Healthcheck failed!")
    print("✅ All systems healthy.")

def notify():
    """Final notification step (simulate Slack/Email)."""
    print("📢 Pipeline finished successfully!")


# -------------------------------------------------------------------
# DAG definition
# -------------------------------------------------------------------

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email": ["alerts@example.com"],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    "mega_pipeline",
    default_args=default_args,
    description="Mega end-to-end self-healing data pipeline",
    schedule_interval="@daily",
    start_date=datetime(2025, 9, 1),
    catchup=False,
    tags=["mega", "pipeline", "self-healing"],
) as dag:

    start = DummyOperator(task_id="start")

    ingest = PythonOperator(
        task_id="produce_data",
        python_callable=produce_data,
    )

    validate = BranchPythonOperator(
        task_id="validate_data",
        python_callable=validate_data,
        provide_context=True,
    )

    quarantine = PythonOperator(
        task_id="quarantine_data",
        python_callable=quarantine_data,
    )

    load = PythonOperator(
        task_id="load_to_postgres",
        python_callable=load_to_postgres,
    )

    spark = PythonOperator(
        task_id="spark_transform",
        python_callable=spark_transform,
    )

    check = PythonOperator(
        task_id="healthcheck",
        python_callable=healthcheck,
    )

    notify_task = PythonOperator(
        task_id="notify",
        python_callable=notify,
    )

    end = DummyOperator(task_id="end")

    # -------------------------------------------------------------------
    # DAG Dependencies
    # -------------------------------------------------------------------
    start >> ingest >> validate
    validate >> quarantine >> end
    validate >> load >> spark >> check >> notify_task >> end
