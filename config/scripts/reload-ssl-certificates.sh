#!/bin/bash
set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# regenerate SSL certificates
docker-compose --file ${SCRIPT_DIR}/../docker/compose.certbot.yml --project-directory ${SCRIPT_DIR}/../../ up --exit-code-from certbot

# Ensure symlinks point to the new certificates
ln -f -s ./certbot/live/www.pagepress.com.au/fullchain.pem ${SCRIPT_DIR}/../ssl/ism-fullchain.pem
ln -f -s ./certbot/live/www.pagepress.com.au/privkey.pem ${SCRIPT_DIR}/../ssl/ism-key.pem

# reload nginx to apply the new certificates without downtime
docker exec ngnix nginx -s reload