#!/usr/bin/env python3

import subprocess
import json
import logging
import os
from enum import Enum

class Environment(Enum):
    PREPROD = "preprod"
    PROD = "prod"

    def __str__(self):
        return self.value

class DeploymentManager:    
    def getCurrentServerIp(self) -> str:
        raise NotImplementedError("This method should be implemented by subclasses")

    def generateNewServer(self):
        subprocess.run(["terraform", "-chdir=terraform/create-vps", "init"], check=True)
        subprocess.run(["terraform", "-chdir=terraform/create-vps", "apply", "-var-file=../terraform.tfvars", "-auto-approve"], check=True)
        result = subprocess.run(["terraform", "-chdir=terraform/create-vps", "output", "-raw", "node_details"], stdout=subprocess.PIPE, check=True)
        # get the new node details
        generatedNodes = json.loads(result.stdout)
        if len(generatedNodes) != 1:
            raise Exception("There should only be one node generated")
        
        generatedIp = generatedNodes[0]['ip_address']
        return generatedIp
    
    def runAnsibleOnNewVps(self, newVpsIp, currentVpsIp):
        ansibleHostsPath = './ansible/inventory.ini'
        with open(ansibleHostsPath, 'w') as f:
            f.write(f"current_vps ansible_host={currentVpsIp}\n")
            f.write(f"new_vps ansible_host={newVpsIp}\n")

        ansibleEnv = os.environ.copy()
        ansibleEnv["ANSIBLE_HOST_KEY_CHECKING"] = "False"
        ansibleEnv["ANSIBLE_PIPELINING"] = "True"
        subprocess.run(["ansible-playbook", "-i", ansibleHostsPath, "./ansible/main.yml"], env=ansibleEnv, check=True)

    def runIntegrationTests(self) -> bool:
        return True

    def switchToNewVps(self):
        raise NotImplementedError("This method should be implemented by subclasses")

    def deactivateOldVps(self):
        raise NotImplementedError("This method should be implemented by subclasses")
    
    def destroyNewVps(self):
        subprocess.run(["terraform", "-chdir=terraform/create-vps", "destroy", "-var-file=../terraform.tfvars", "-auto-approve"], check=True)


class DeploymentManagerPreProd(DeploymentManager):
    def getCurrentServerIp(self) -> str | None:
        # need to spin up the preprod environment
        subprocess.run(["terraform", "-chdir=terraform/recreate-preprod", "init"], check=True)
        applyResult = subprocess.run(["terraform", "-chdir=terraform/recreate-preprod", "apply", "-var-file=../terraform.tfvars", "-auto-approve"])
        if applyResult.returncode != 0:
            logging.error("Failed to apply preprod environment")
            return None
        result = subprocess.run(["terraform", "-chdir=terraform/recreate-preprod", "output", "-raw", "node_details"], stdout=subprocess.PIPE, check=True, shell=True)
        if result.returncode != 0:
            logging.error("Failed to get preprod node details")
            return None
        preprodNodes = json.loads(result.stdout)
        if len(preprodNodes) != 1:
            raise Exception("There should only be one node in the preprod environment")
        
        preprodIp = preprodNodes[0]['ip_address']
        return preprodIp
    
    def switchToNewVps(self):
        # snapshot the new preprod server
        subprocess.run(["terraform", "-chdir=terraform/snapshot-vps", "apply", "-var-file=../terraform.tfvars", "-auto-approve"], check=True)

    def deactivateOldVps(self):
        subprocess.run(["terraform", "-chdir=terraform/recreate-preprod", "destroy", "-var-file=../terraform.tfvars", "-auto-approve"], check=True)

class DeploymentManagerProd(DeploymentManager):
    def getCurrentServerIp(self) -> str:
        pass
    
    def switchToNewVps(self):
        subprocess.run(["terraform", "-chdir=terraform/update-dns", "apply", "-var-file=../terraform.tfvars", "-auto-approve"], check=True)

    def deactivateOldVps(self):
        pass