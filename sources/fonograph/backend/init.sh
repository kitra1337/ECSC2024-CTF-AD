#!/bin/sh

while ! wget db:3306;
do
    echo "."
    sleep 1
done

python db.py
gunicorn -b 0.0.0.0:5000 --worker-class eventlet -w 1 app:app
