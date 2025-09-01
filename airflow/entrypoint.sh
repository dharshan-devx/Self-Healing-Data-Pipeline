#!/usr/bin/env bash

# Fail on error
set -e

# Wait for Postgres
echo "⏳ Waiting for Postgres at $POSTGRES_HOST:$POSTGRES_PORT..."
while ! nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
  sleep 1
done
echo "✅ Postgres is ready!"

# Run DB migrations
echo "📦 Running Airflow migrations..."
airflow db migrate

# Create default admin user if not exists
if ! airflow users list | grep -q "airflow@example.com"; then
  echo "👤 Creating default Airflow user..."
  airflow users create \
    --username airflow \
    --password airflow \
    --firstname airflow \
    --lastname airflow \
    --role Admin \
    --email airflow@example.com
else
  echo "👤 Default Airflow user already exists. Skipping creation."
fi

echo "🚀 Starting Airflow with command: $@"
exec airflow "$@"
