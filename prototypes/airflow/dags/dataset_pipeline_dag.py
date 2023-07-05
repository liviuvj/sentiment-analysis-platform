from datetime import datetime, timedelta
from textwrap import dedent

from airflow import DAG
from airflow.models import Variable
from airflow.operators.bash import BashOperator
from airflow.providers.airbyte.operators.airbyte import AirbyteTriggerSyncOperator
from airflow.providers.airbyte.sensors.airbyte import AirbyteJobSensor
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount

# Path variables
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
MONGO_DATABASE = "raw_dataset"

# Output database variables
CLICKHOUSE_HOST = Variable.get("CLICKHOUSE_HOST")
CLICKHOUSE_PORT = Variable.get("CLICKHOUSE_PORT")
CLICKHOUSE_USER = Variable.get("CLICKHOUSE_USER")
CLICKHOUSE_PASSWORD = Variable.get("CLICKHOUSE_PASSWORD")

# Airbyte connection IDs
AIRBYTE_MOVIE_CONNECTION_ID = "90b92596-0605-406c-8833-11a5549ad36e"
AIRBYTE_SEASON8_CONNECTION_ID = "a960b92e-4d05-4765-9140-01fcf3c5d3b7"
AIRBYTE_JON_CONNECTION_ID = "a63cbbc8-082b-4401-9bb1-b9aacadc0a53"
AIRBYTE_DAENERYS_CONNECTION_ID = "e6994db5-b24d-49d1-ac22-c33395de4313"

# Name of the data source
DATA_SOURCE = "dataset"

# Grace sleep period for Apache Spark
# to keep up the container after task completion
SLEEP_TIME = "30"

# Dynamic configuration for multiple similar DAGs
dynamic_config = {
    "movie": {"connection_id": AIRBYTE_MOVIE_CONNECTION_ID,
              "search_query": "movie",},
    "season8": {"connection_id": AIRBYTE_SEASON8_CONNECTION_ID,
                "search_query": "season 8"},
    "jon": {"connection_id": AIRBYTE_JON_CONNECTION_ID,
            "search_query": "Jon"},
    "daenerys": {"connection_id": AIRBYTE_DAENERYS_CONNECTION_ID,
                 "search_query": "Daenerys"},
}



for config_name, config in dynamic_config.items():

    DAG_ID = f"dataset_pipeline_{config_name}"
    DAG_DESCRIPTION = f"Dataset ({config_name}) data pipeline DAG"
    DAG_TAGS = [config_name, DATA_SOURCE, "ETL"]

    # DAG definition
    with DAG(
        DAG_ID,
        description=DAG_DESCRIPTION,
        schedule="@once",
        start_date=datetime(2023, 1, 1),
        catchup=False,
        tags=DAG_TAGS,
    ) as dag:
        dag.doc_md = f"""
        ### {DAG_DESCRIPTION}.

        Executes the data extraction, transformation and loading
        into the final database for visualization.
        """

        # TASK: Sync Data
        task_sync_data = AirbyteTriggerSyncOperator(
            task_id="sync_data",
            airbyte_conn_id="AIRBYTE_CONNECTION",
            connection_id=config["connection_id"],
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
                "DATA_SOURCE": DATA_SOURCE,
                "SEARCH_QUERY": config["search_query"],
                "COLLECTION": config_name,
                "TARGET_SPARK_TASKS_PATH": TARGET_PATH_SPARK_TASKS,
                "SLEEP_TIME": SLEEP_TIME,
                "MONGO_USER": MONGO_USER,
                "MONGO_PASSWORD": MONGO_PASSWORD,
                "MONGO_HOST": MONGO_HOST,
                "MONGO_PORT": MONGO_PORT,
                "MONGO_DATABASE": MONGO_DATABASE
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
                '--conf "spark.mongodb.input.uri=mongodb://{{ params.MONGO_USER }}:{{ params.MONGO_PASSWORD }}@{{ params.MONGO_HOST }}:{{ params.MONGO_PORT }}/{{ params.MONGO_DATABASE }}.{{ params.COLLECTION }}?authSource=admin" '
                '--conf "spark.mongodb.output.uri=mongodb://{{ params.MONGO_USER }}:{{ params.MONGO_PASSWORD }}@{{ params.MONGO_HOST }}:{{ params.MONGO_PORT }}/{{ params.MONGO_DATABASE }}.{{ params.COLLECTION }}?authSource=admin" '
                "--packages org.mongodb.spark:mongo-spark-connector_2.12:3.0.1 "
                '--conf "spark.DATA_SOURCE={{ params.DATA_SOURCE }}" --conf "spark.SEARCH_QUERY={{ params.SEARCH_QUERY }}" '
                "-i {{ params.TARGET_SPARK_TASKS_PATH }}/transform_dataset.scala"
                "; sleep {{ params.SLEEP_TIME}}",
            ],
        )

        task_process_data.doc_md = dedent(
            """\
                #### Task Documentation: Process Data

                This task deploys a Docker container that runs the data processing with Apache Spark.

                The container needs the following:
                - The full host path to the processing tasks `SOURCE_SPARK_TASKS_PATH` & `TARGET_PATH_SPARK_TASKS`
                - The name of the collection to retrieve the data from `COLLECTION`
                - The name of the data source `DATA_SOURCE`
                - The query used to gather the data `SEARCH_QUERY`
                - The sleep period to keep up the container after task completion `SLEEP_TIME`

                And the database connection parameters:
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
                "DATA_SOURCE": DATA_SOURCE,
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
                "{{ params.DATA_SOURCE }}",
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

                The container needs the full host path to the NLP tasks `SOURCE_NLP_TASKS_PATH` & `TARGET_PATH_NLP_TASKS`
                and the source of the data `DATA_SOURCE`.

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
