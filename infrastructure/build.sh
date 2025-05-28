#!/bin/bash
set -e

# recreate preprod
terraform -chdir=terraform/recreate-preprod init
terraform -chdir=terraform/recreate-preprod apply -var-file=../terraform.tfvars -auto-approve --var="use_base_image=true"
preprod_inventory=$(terraform -chdir=terraform/create-vps output -raw node_details)

exit 0
# recreate current VPS from snapshot
terraform -chdir=terraform/create-vps init
terraform -chdir=terraform/create-vps apply -var-file=../terraform.tfvars -auto-approve --var="use_base_image=true"

# Create new VPS from scratch
terraform -chdir=terraform/create-vps apply -var-file=../terraform.tfvars -auto-approve --var="use_base_image=true"
inventory_json=$(terraform -chdir=terraform/create-vps output -raw node_details)
python3 terraform-to-ansible.py -i $inventory_json -o ./ansible/inventory.ini
# ANSIBLE_PIPELINING speeds up the playbook execution
ANSIBLE_HOST_KEY_CHECKING=False ANSIBLE_PIPELINING=True ansible-playbook -i ./ansible/inventory.ini ./ansible/main.yml

# snapshot the VPS
terraform -chdir=terraform/snapshot-vps init
terraform -chdir=terraform/snapshot-vps apply -var-file=../terraform.tfvars -auto-approve