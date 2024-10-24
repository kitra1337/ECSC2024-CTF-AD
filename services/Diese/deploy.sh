#!/bin/bash

SHARE_SECRET=$(hexdump -vn16 -e'4/4 "%08X" 1 "\n"' /dev/urandom);
DB_PASS=$(hexdump -vn16 -e'4/4 "%08X" 1 "\n"' /dev/urandom);

if [[ ! -f ".env" ]]
then
    echo "SHARE_SECRET=${SHARE_SECRET}" >> .env
    echo "DB_PASS=${DB_PASS}" >> .env
fi

docker compose up --build --remove-orphans -d