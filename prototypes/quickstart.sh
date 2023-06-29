#!/bin/bash

# Version 1.0
#
# Quickstart script for the project's prototype.

# Activate environment
source ../.venv/bin/activate

# Clone repository and run Airbyte platform
cd extraction
git clone --depth 1 https://github.com/airbytehq/airbyte.git
cd airbyte
./run-ab-platform.sh

# Create external networks
docker network create etl_network
docker network create --bridge etl_bridge

# Run MongoDB instance
cd ../../mongodb
docker compose up -d

# Configure data extraction and data loading pipeline
cd ../extraction
python config.py

# Run ClickHouse instance and connect to bridge network
cd ../clickhouse
docker compose up -d
until [ "$( docker container inspect -f '{{.State.Status}}' clickhouse )" = "running" ]; do
    sleep 0.1;
done;
docker network connect etl_bridge clickhouse

# Clone repository and add connector requirement
cd ../visualization
git clone https://github.com/apache/superset.git
./config.sh

# Run Superset platform
cd superset
docker-compose -f docker-compose-non-dev.yml pull
docker-compose -f docker-compose-non-dev.yml up -d
cd ..

# Wait until container is ready and add it to the bridge network
until [ "$( docker container inspect -f '{{.State.Status}}' superset_app )" = "running" ]; do
    sleep 0.1;
done;
docker network connect etl_bridge superset_app

# Fetch Airflow
cd airflow
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.6.2/docker-compose.yaml'

# Run configuration script
./config_airflow.sh

# Initialize database
docker compose up airflow-init

# Run Airflow platform
docker compose up -d