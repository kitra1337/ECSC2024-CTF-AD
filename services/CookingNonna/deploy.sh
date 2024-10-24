#!/bin/sh

mkdir -p data
chmod 777 data
docker compose up --build -d
