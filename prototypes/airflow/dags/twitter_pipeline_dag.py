from datetime import datetime, timedelta
from textwrap import dedent

from airflow import DAG
from airflow.models import Variable
from airflow.operators.bash import BashOperator
from airflow.providers.airbyte.operators.airbyte import AirbyteTriggerSyncOperator
from airflow.providers.airbyte.sensors.airbyte import AirbyteJobSensor
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount

# Variable definitions
SOURCE_SPARK_TASKS_PATH = Variable.get("SPARK_TASKS_PATH")
SOURCE_NLP_TASKS_PATH = Variable.get("NLP_TASKS_PATH")
TARGET_PATH_SPARK_TASKS = "/spark-tasks"
TARGET_PATH_NLP_TASKS = "/nlp-tasks"
SPARK_PORT = Variable.get("SPARK_PORT")

# Docker variables
SPARK_IMAGE_NAME = Variable.get("SPARK_IMAGE_NAME")
NLP_IMAGE_NAME = Variable.get("NLP_IMAGE_NAME")
DOCKER_PROXY_URL = "TCP://docker-socket-proxy:2375"
DOCKER_NETWORK = "etl_network"

# Input database variables
MONGO_HOST = Variable.get("MONGO_HOST")
MONGO_PORT = Variable.get("MONGO_PORT")
MONGO_USER = Variable.get("MONGO_USER")
MONGO_PASSWORD = Variable.get("MONGO_PASSWORD")

# Output database variables
CLICKHOUSE_HOST = Variable.get("CLICKHOUSE_HOST")
CLICKHOUSE_PORT = Variable.get("CLICKHOUSE_PORT")
CLICKHOUSE_USER = Variable.get("CLICKHOUSE_USER")
CLICKHOUSE_PASSWORD = Variable.get("CLICKHOUSE_PASSWORD")

# Airbyte connection ID
AIRBYTE_CONNECTION_ID = "7d599bd8-7006-42c7-8b26-39c7e2b1a423"

# DAG definition
with DAG(
    "twitter_pipeline",
    description="Twitter data pipeline DAG",
    schedule="@once",
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=["movie", "twitter", "ETL"],
) as dag:
    dag.doc_md = """
    ### Twitter data pipeline.

    Executes the data extraction, transformation and loading into the final database for visualization.
    """

    # TASK: Sync Data
    task_sync_data = AirbyteTriggerSyncOperator(
        task_id="sync_data",
        airbyte_conn_id="AIRBYTE_CONNECTION",
        connection_id=AIRBYTE_CONNECTION_ID,
    )

    task_sync_data.doc_md = dedent(
        """\
            #### Task Documentation: Sync Data

            This task launches the data synchronization of the established Airbyte connection,
            specified with the parameter `AIRBYTE_CONNECTION_ID`.
        """
    )

    # TASK: Sensor Sync Data
    sensor_sync_data = AirbyteJobSensor(
        task_id="sensor_sync_data",
        airbyte_conn_id="AIRBYTE_CONNECTION",
        airbyte_job_id=task_sync_data.output,
    )

    sensor_sync_data.doc_md = dedent(
        """\
            #### Task Documentation: Sensor Sync Data

            This task acts as a sensor for the previously executed Airbyte synchronization.
        """
    )

    # TASK: Process Data
    task_process_data = DockerOperator(
        task_id="process_data",
        dag=dag,
        do_xcom_push=True,
        params={
            "TARGET_SPARK_TASKS_PATH": TARGET_PATH_SPARK_TASKS,
            "MONGO_USER": MONGO_USER,
            "MONGO_PASSWORD": MONGO_PASSWORD,
            "MONGO_HOST": MONGO_HOST,
            "MONGO_PORT": MONGO_PORT,
        },
        api_version="auto",
        docker_url=DOCKER_PROXY_URL,
        image=SPARK_IMAGE_NAME,
        container_name="airflow-spark",
        auto_remove=True,
        network_mode=DOCKER_NETWORK,
        mounts=[
            Mount(
                source=SOURCE_SPARK_TASKS_PATH,
                target=TARGET_PATH_SPARK_TASKS,
                type="bind",
            ),
        ],
        port_bindings={
            "4040": SPARK_PORT,
        },
        command=[
            "/bin/bash",
            "-c",
            "spark-shell "
            '--conf "spark.mongodb.input.uri=mongodb://{{ params.MONGO_USER }}:{{ params.MONGO_PASSWORD }}@{{ params.MONGO_HOST }}:{{ params.MONGO_PORT }}/raw_twitter.airbyte_tmp_bgr__0133_tweets_advanced?authSource=admin" '
            '--conf "spark.mongodb.output.uri=mongodb://{{ params.MONGO_USER }}:{{ params.MONGO_PASSWORD }}@{{ params.MONGO_HOST }}:{{ params.MONGO_PORT }}/raw_twitter.airbyte_tmp_bgr__0133_tweets_advanced?authSource=admin" '
            "--packages org.mongodb.spark:mongo-spark-connector_2.12:3.0.1 "
            "-i {{ params.TARGET_SPARK_TASKS_PATH }}/transform_twitter.scala"
            "; sleep 30",
        ],
    )

    task_process_data.doc_md = dedent(
        """\
            #### Task Documentation: Process Data

            This task deploys a Docker container that runs the data processing with Apache Spark.

            The container needs the full host path to the NLP tasks `SOURCE_SPARK_TASKS_PATH` and `TARGET_PATH_SPARK_TASKS.
            Also the following connection parameters for the input and output databases:
                - `MONGO_USER`
                - `MONGO_PASSWORD`
                - `MONGO_HOST`
                - `MONGO_PORT`
                - `MONGO_DATABASE`
        """
    )

    # TASK: NLP Inference
    task_nlp_inference = DockerOperator(
        task_id="nlp_inference",
        dag=dag,
        do_xcom_push=True,
        params={
            "TARGET_NLP_TASKS_PATH": TARGET_PATH_NLP_TASKS,
            "MONGO_USER": MONGO_USER,
            "MONGO_PASSWORD": MONGO_PASSWORD,
            "MONGO_HOST": MONGO_HOST,
            "MONGO_PORT": MONGO_PORT,
            "CLICKHOUSE_USER": CLICKHOUSE_USER,
            "CLICKHOUSE_PASSWORD": CLICKHOUSE_PASSWORD,
            "CLICKHOUSE_HOST": CLICKHOUSE_HOST,
            "CLICKHOUSE_PORT": CLICKHOUSE_PORT,
        },
        api_version="auto",
        docker_url=DOCKER_PROXY_URL,
        image=NLP_IMAGE_NAME,
        container_name="airflow-nlp",
        auto_remove=True,
        network_mode=DOCKER_NETWORK,
        mounts=[
            Mount(
                source=SOURCE_NLP_TASKS_PATH, target=TARGET_PATH_NLP_TASKS, type="bind"
            ),
        ],
        command=[
            "python",
            "-u",
            "{{ params.TARGET_NLP_TASKS_PATH }}/pipeline.py",
            "twitter",
            "{{ params.MONGO_USER }}",
            "{{ params.MONGO_PASSWORD }}",
            "{{ params.MONGO_HOST }}",
            "{{ params.MONGO_PORT }}",
            "{{ params.CLICKHOUSE_USER }}",
            "{{ params.CLICKHOUSE_PASSWORD }}",
            "{{ params.CLICKHOUSE_HOST }}",
            "{{ params.CLICKHOUSE_PORT }}",
        ],
    )

    task_nlp_inference.doc_md = dedent(
        """\
            #### Task Documentation: NLP Inference

            This task deploys a Docker container that runs the NLP inference with HuggingFace Transformers.

            The container needs the full host path to the NLP tasks `SOURCE_NLP_TASKS_PATH` and `TARGET_NLP_TASKS_PATH.
            Also the following connection parameters for the input and output databases:
                - `MONGO_USER`
                - `MONGO_PASSWORD`
                - `MONGO_HOST`
                - `MONGO_PORT`
                - `CLICKHOUSE_USER`
                - `CLICKHOUSE_PASSWORD`
                - `CLICKHOUSE_HOST`
                - `CLICKHOUSE_PORT`
        """
    )

    # DAG task order
    task_sync_data >> sensor_sync_data >> task_process_data >> task_nlp_inference
