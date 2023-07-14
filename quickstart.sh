#!/bin/bash

# Version 1.0
#
# Quickstart script for the project's prototype.

set -e

# Activate environment
source .venv/bin/activate

# Clone repository and run Airbyte platform
cd extraction
git clone --depth 1 https://github.com/airbytehq/airbyte.git
cd airbyte
bash run-ab-platform.sh -b

# Create external networks
docker network create etl_network
docker network create etl_bridge

# Run MongoDB instance
cd ../../mongodb
docker compose up -d
echo ">> MongoDB up and running!"

# Configure data extraction and data loading pipeline
cd ../extraction
echo ">> Waiting for Airbyte..." 
sleep 60
python config.py
echo ">> Airbyte up and running!"

# Build custom spark image
cd ../spark
echo "SPARK_TASKS_PATH=$PWD/spark-tasks" >> .env
source .env
docker build -t $SPARK_IMAGE_NAME .
echo ">> Apache Spark up and ready!"

# Build NLP image
cd ../nlp
echo "NLP_TASKS_PATH=$PWD/nlp-tasks" >> .env
source .env
docker build -t $NLP_IMAGE_NAME .
echo ">> HuggingFace Transformers up and ready!"

# Run ClickHouse instance and connect to bridge network
cd ../clickhouse
docker compose up -d
until [ "$( docker container inspect -f '{{.State.Status}}' clickhouse )" = "running" ]; do
    sleep 0.1;
done;
docker network connect etl_bridge clickhouse
echo ">> ClickHouse up and running!"

# Clone repository and add connector requirement
cd ../visualization
git clone https://github.com/apache/superset.git
bash config.sh

# # Run Superset platform
cd superset
docker-compose -f docker-compose-non-dev.yml pull
docker-compose -f docker-compose-non-dev.yml up -d
cd ../

# Wait until container is ready and add it to the bridge network
until [ "$( docker container inspect -f '{{.State.Status}}' superset_app )" = "running" ]; do
    sleep 0.1;
done;
docker network connect etl_bridge superset_app

# # Run script to import dashboard and datasets
source .env
source ../clickhouse/.env
sleep 60
curl -L "https://drive.google.com/uc?export=download&id=15e7Uu5cEPASdB73Ug1qHUBUMj9hQSo7_" --output dashboard_export.zip
python -u import_dashboard.py $SUPERSET_ADMIN_PASSWORD $CLICKHOUSE_PASSWORD
cd ..

echo ">> Apache Superset up and running!"

# Fetch Airflow
cd airflow
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.6.2/docker-compose.yaml'

# Initialize database
docker compose up airflow-init
sleep 60

# Run configuration script
bash config_airflow.sh

# Run Airflow platform
docker compose up -d
docker compose -f docker-compose.proxy.yaml up -d
cd ..
echo ">> Apache Airflow up and running!"

# Run centralized web access point
cd web
chmod +x app/entrypoint.sh
docker compose up -d
echo ">> Web app up and running!"
