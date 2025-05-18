#!/bin/bash
set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Building
docker build --platform=linux/amd64 -t password-gen:0.0.1 .

# Publishing
docker login
docker tag password-gen:0.0.1 bluesquid2/password-gen:0.0.1
docker push bluesquid2/password-gen:0.0.1

docker-compose --file ./config/docker/compose.web.yml --project-directory ./ up
