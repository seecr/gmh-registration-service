#!/bin/bash
#

if [ -z "${TOKEN}" ]; then
    TOKEN=$1;
    shift 1;
fi

NBN=$1

RESPONSE=$(wget --quiet \
    -O- "https://registration-service.kb.dev.seecr.nl/nbn/${NBN}/locations" \
    --header "Authorization: Bearer ${TOKEN}")

echo "RESPONSE: ${RESPONSE}"

