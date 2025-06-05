#!/bin/bash

echo "Waiting for postgres..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.1
done
echo "PostgreSQL started"

echo "Applying database migrations..."
python manage.py makemigrations
python manage.py migrate

echo "Loading initial data (tags and ingredients)..."
python manage.py setup_initial_data

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting server..."
exec "$@"