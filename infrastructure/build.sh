#!/bin/bash
set -e
terraform -chdir=terraform apply -auto-approve
inventory_json=$(terraform -chdir=terraform output -raw node_details)
python3 terraform-to-ansible.py -i $inventory_json -o ./ansible/inventory.ini
ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -i ./ansible/inventory.ini ./ansible/main.yml