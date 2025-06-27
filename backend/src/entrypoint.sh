#!/bin/bash

echo "Waiting for postgres..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.4
done

python manage.py migrate
python manage.py setup_initial_data
python manage.py collectstatic --noinput

echo "Starting server..."
exec "$@"