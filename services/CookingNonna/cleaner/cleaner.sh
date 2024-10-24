#!/bin/sh

while true; do
    date -uR
    find /tmp/data -type f -name password -cmin +30 -exec bash -c 'rm -rf $(dirname $1)' _ {} \;
    sleep 60
done