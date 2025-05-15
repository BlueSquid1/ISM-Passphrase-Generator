#!/bin/bash
set -e

keep_snapshot=true
if [ "$1" == "-f" ]; then
    keep_snapshot=false
fi
if [ "$keep_snapshot" = false ]; then
    terraform -chdir=terraform/snapshot-vps destroy -var-file=../terraform.tfvars -auto-approve
fi

terraform -chdir=terraform/create-vps destroy -var-file=../terraform.tfvars -auto-approve --var="use_base_image=$keep_snapshot"