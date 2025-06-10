#!/bin/bash
#

if [ -z "${TOKEN}" ]; then
    TOKEN=$1; shift 1;
fi

URL=$1

QUOTED=$(echo "${URL}" | python -c "from urllib.parse import quote; import sys; print(quote(sys.stdin.read(), safe=''))")

RESPONSE=$(wget --quiet -O- --header "Authorization: Bearer ${TOKEN}" "https://registration-service.kb.dev.seecr.nl/location/${QUOTED}")

echo "RESPONSE: ${RESPONSE}"

