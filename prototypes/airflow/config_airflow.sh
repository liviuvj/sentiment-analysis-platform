#!/bin/bash

# Version 1.0
#
# Configuration script for Apache Airflow.

# Source env
source ../mongodb/.env
source ../spark/.env
source ../nlp/.env
source ../clickhouse/.env

# Set here variables to use inside the DAG configurations.
# The paths declared here must be ABSOLUTE, not relative.
# Must be cleaned of possible special characters before using them.
SPARK_TASKS_PATH=$(echo $SPARK_TASKS_PATH | tr -d "\n\r")
SPARK_IMAGE_NAME=$(echo $SPARK_IMAGE_NAME | tr -d "\n\r")
SPARK_PORT=$(echo $SPARK_PORT| tr -d "\n\r")
NLP_TASKS_PATH=$(echo $NLP_TASKS_PATH| tr -d "\n\r")
NLP_IMAGE_NAME=$(echo $NLP_IMAGE_NAME| tr -d "\n\r")
MONGO_HOST=$(echo $MONGODB_CONTAINER_NAME | tr -d "\n\r")
MONGO_PORT=$(echo $MONGODB_PORT | tr -d "\n\r")
MONGO_USER=$(echo $MONGODB_ROOT_USER | tr -d "\n\r")
MONGO_PASSWORD=$(echo $MONGODB_ROOT_PASSWORD | tr -d "\n\r")
CLICKHOUSE_HOST=$(echo $CLICKHOUSE_CONTAINER_NAME | tr -d "\n\r")
CLICKHOUSE_PORT=$(echo $CLICKHOUSE_PORT_NATIVE | tr -d "\n\r")
CLICKHOUSE_USER=$(echo $CLICKHOUSE_USER | tr -d "\n\r")
CLICKHOUSE_PASSWORD=$(echo $CLICKHOUSE_PASSWORD | tr -d "\n\r")
AIRBYTE_USER="airbyte"
AIRBYTE_PASSWORD="password"

# Use custom built image instead of default
sed -i "s/image: \${AIRFLOW_IMAGE_NAME:-apache\/airflow:2.6.2}/# &/" ./docker-compose.yaml
sed -i "s/# build: ./build:\n    dockerfile: airflow.dockerfile/" ./docker-compose.yaml

# Generate Fernet key to encrypt variables
FERNET_KEY=$(docker compose run --rm airflow-worker python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" | tr -d "\n")

# Change default Fernet key
sed -i "s/AIRFLOW__CORE__FERNET_KEY: ''/AIRFLOW__CORE__FERNET_KEY: '$FERNET_KEY'/" ./docker-compose.yaml

# Don't load examples
sed -i "s/AIRFLOW__CORE__LOAD_EXAMPLES: 'true'/AIRFLOW__CORE__LOAD_EXAMPLES: 'false'/" ./docker-compose.yaml

# Set DAG variables
docker compose run --rm airflow-worker bash -c "
    airflow variables set SPARK_TASKS_PATH $SPARK_TASKS_PATH;
    airflow variables set SPARK_IMAGE_NAME $SPARK_IMAGE_NAME;
    airflow variables set SPARK_PORT $SPARK_PORT;
    airflow variables set NLP_TASKS_PATH $NLP_TASKS_PATH;
    airflow variables set NLP_IMAGE_NAME $NLP_IMAGE_NAME;
    airflow variables set MONGO_HOST $MONGO_HOST;
    airflow variables set MONGO_PORT $MONGO_PORT;
    airflow variables set MONGO_USER $MONGO_USER;
    airflow variables set MONGO_PASSWORD $MONGO_PASSWORD;
    airflow variables set CLICKHOUSE_HOST $CLICKHOUSE_HOST;
    airflow variables set CLICKHOUSE_PORT $CLICKHOUSE_PORT;
    airflow variables set CLICKHOUSE_USER $CLICKHOUSE_USER;
    airflow variables set CLICKHOUSE_PASSWORD $CLICKHOUSE_PASSWORD;
    airflow connections add AIRBYTE_CONNECTION --conn-uri airbyte://$AIRBYTE_USER:$AIRBYTE_PASSWORD@host.docker.internal:8001;
    "
