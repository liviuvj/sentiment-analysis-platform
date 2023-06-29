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

SPARK_IMAGE_NAME = Variable.get("SPARK_IMAGE_NAME")
NLP_IMAGE_NAME = Variable.get("NLP_IMAGE_NAME")

MONGO_HOST = Variable.get("MONGO_HOST")
MONGO_PORT = Variable.get("MONGO_PORT")
MONGO_USER = Variable.get("MONGO_USER")
MONGO_PASSWORD = Variable.get("MONGO_PASSWORD")

CLICKHOUSE_HOST = Variable.get("CLICKHOUSE_HOST")
CLICKHOUSE_PORT = Variable.get("CLICKHOUSE_PORT")
CLICKHOUSE_USER = Variable.get("CLICKHOUSE_USER")
CLICKHOUSE_PASSWORD = Variable.get("CLICKHOUSE_PASSWORD")

AIRBYTE_CONNECTION_ID = "7d599bd8-7006-42c7-8b26-39c7e2b1a423"

# DAG definition
with DAG(
    "twitter_pipeline",
    description="Twitter data pipeline DAG",
    schedule="@once",
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=["twitter", "ETL"],
) as dag:
    dag.doc_md = """
    Twitter data pipeline.

    Executes the data extraction, transformation and loading
    into the final database for visualization.
    """

    t1 = BashOperator(
        task_id="print_date",
        bash_command="date",
    )

    t1.doc_md = dedent(
        """\
    #### Task Documentation
    You can document your task using the attributes `doc_md` (markdown),
    `doc` (plain text), `doc_rst`, `doc_json`, `doc_yaml` which gets
    rendered in the UI's Task Instance Details page.
    ![img](http://montcs.bloomu.edu/~bobmon/Semesters/2012-01/491/import%20soul.png)
    **Image Credit:** Randall Munroe, [XKCD](https://xkcd.com/license.html)
    """
    )

    task_sync_data = AirbyteTriggerSyncOperator(
        task_id="sync_data",
        airbyte_conn_id="AIRBYTE_CONNECTION",
        connection_id=AIRBYTE_CONNECTION_ID,
    )

    sensor_sync_data = AirbyteJobSensor(
        task_id="sensor_sync_data",
        airbyte_conn_id="AIRBYTE_CONNECTION",
        airbyte_job_id=task_sync_data.output,
    )

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
        docker_url="TCP://docker-socket-proxy:2375",
        image=SPARK_IMAGE_NAME,
        container_name="airflow-spark",
        auto_remove=True,
        network_mode="etl_network",
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
            "-i {{ params.TARGET_SPARK_TASKS_PATH }}/transform.scala"
            "; sleep 20",
        ],
    )

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
        docker_url="TCP://docker-socket-proxy:2375",
        image=NLP_IMAGE_NAME,
        container_name="airflow-nlp",
        auto_remove=True,
        network_mode="etl_network",
        mounts=[
            Mount(
                source=SOURCE_NLP_TASKS_PATH, target=TARGET_PATH_NLP_TASKS, type="bind"
            ),
        ],
        command=[
            "python",
            "-u",
            "{{ params.TARGET_NLP_TASKS_PATH }}/pipeline.py",
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

    t1 >> task_sync_data >> sensor_sync_data >> task_process_data >> task_nlp_inference
