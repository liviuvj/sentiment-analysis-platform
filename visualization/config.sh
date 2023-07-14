#!/bin/bash

# Version 1.0
#
# Configuration script for Apache Superset.

# Add ClickHouse connector requirement
touch ./superset/docker/requirements-local.txt
echo "clickhouse-connect>=0.4.1" >> ./superset/docker/requirements-local.txt

# Change default admin password
source .env
sed -i "0,/ADMIN_PASSWORD=\"admin\"/s//ADMIN_PASSWORD=$SUPERSET_ADMIN_PASSWORD/" ./superset/docker/docker-init.sh
