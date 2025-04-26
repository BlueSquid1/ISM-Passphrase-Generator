#!/bin/bash
set -e
terraform -chdir=terraform/create-vps init
terraform -chdir=terraform/create-vps apply -var-file=../terraform.tfvars -auto-approve
inventory_json=$(terraform -chdir=terraform/create-vps output -raw node_details)
python3 terraform-to-ansible.py -i $inventory_json -o ./ansible/inventory.ini
ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -i ./ansible/inventory.ini ./ansible/main.yml
terraform -chdir=terraform/snapshot-vps init
terraform -chdir=terraform/snapshot-vps apply -var-file=../terraform.tfvars -auto-approve