#!/bin/bash
set -e
terraform -chdir=terraform/create-vps destroy -var-file=../terraform.tfvars -auto-approve