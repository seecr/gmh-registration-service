#!/bin/bash
#

read -s -p "Password: " PASSWD

TOKEN=$(wget --quiet \
    -O- "https://registration-service.kb.dev.seecr.nl/token" \
    --post-data='{"username": "seecr", "password": "'${PASSWD}'"}' \
    --header 'Content-type: application/json')

echo "TOKEN: ${TOKEN}"

