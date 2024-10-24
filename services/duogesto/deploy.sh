#!/usr/bin/bash

mkdir -p backend/files
mkdir -p backend/prizes

rm -f .env
SECRETKEY=$(head -c 16 /dev/urandom | xxd -p)
echo $SECRETKEY
echo "SECRET_KEY=${SECRETKEY}" >> .env

docker compose up --build -d