#!/usr/bin/env python3

import subprocess
import json
import logging
import os
import socket
from enum import Enum

class Environment(Enum):
    PREPROD = "preprod"
    PROD = "prod"

    def __str__(self):
        return self.value

class DeploymentManager:
    def runCmd(self, cmd: list[str], check = True, env: dict[str, str] = None) -> subprocess.CompletedProcess:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
        if result.returncode != 0:
            print(f"Command: {result.args} failed with return code: {result.returncode}")
            print("--- STDOUT ---")
            print(result.stdout)
            print("--- STDERR ---")
            print(result.stderr)
            if check:
                raise Exception(f"Command failed: {result.args}")
        return result
        

    def getCurrentServerIp(self) -> str | None:
        raise NotImplementedError("This method should be implemented by subclasses")

    def generateNewVps(self, vpsName: str) -> str:
        self.runCmd(["terraform", "-chdir=terraform/create-vps", "init"])
        self.runCmd(["terraform", "-chdir=terraform/create-vps", "apply", "-var-file=../terraform.tfvars", f"-var=vps_name={vpsName}", "-auto-approve"])
        result = self.runCmd(["terraform", "-chdir=terraform/create-vps", "output", "-raw", "node_details"])
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
        self.runCmd(["ansible-playbook", "-i", ansibleHostsPath, "./ansible/main.yml"], env=ansibleEnv)

    def runIntegrationTests(self) -> bool:
        return True

    def switchToNewVps(self):
        raise NotImplementedError("This method should be implemented by subclasses")

    def deactivateOldVps(self):
        raise NotImplementedError("This method should be implemented by subclasses")
    
    def destroyNewVps(self, vpsName: str):
        self.runCmd(["terraform", "-chdir=terraform/create-vps", "destroy", "-var-file=../terraform.tfvars", f"-var=vps_name={vpsName}", "-auto-approve"])


class DeploymentManagerPreProd(DeploymentManager):
    vpsName: str = "preprod-web"

    def getCurrentServerIp(self) -> str | None:
        # need to spin up the preprod environment
        self.runCmd(["terraform", "-chdir=terraform/recreate-preprod", "init"])
        applyResult = self.runCmd(["terraform", "-chdir=terraform/recreate-preprod", "apply", "-var-file=../terraform.tfvars", "-auto-approve"], check=False)
        if applyResult.returncode != 0:
            logging.error("Failed to apply preprod environment")
            return None
        result = self.runCmd(["terraform", "-chdir=terraform/recreate-preprod", "output", "-raw", "node_details"])
        if result.returncode != 0:
            logging.error("Failed to get preprod node details")
            return None
        preprodNodes = json.loads(result.stdout)
        if len(preprodNodes) != 1:
            raise Exception("There should only be one node in the preprod environment")
        
        preprodIp = preprodNodes[0]['ip_address']
        return preprodIp
    
    def generateNewVps(self) -> str:
        return super().generateNewVps(self.vpsName)
    
    def switchToNewVps(self):
        # snapshot the new preprod server
        self.runCmd(["terraform", "-chdir=terraform/snapshot-vps", "apply", "-var-file=../terraform.tfvars", f"-var=vps_name={self.vpsName}", "-auto-approve"])

    def deactivateOldVps(self):
        self.runCmd(["terraform", "-chdir=terraform/recreate-preprod", "destroy", "-var-file=../terraform.tfvars", "-auto-approve"])

    def destroyNewVps(self):
        super().destroyNewVps(self.vpsName)

class DeploymentManagerProd(DeploymentManager):
    vpsName: str = "prod-web"

    def getCurrentServerIp(self) -> str | None:
        try:
            return socket.gethostbyname('www.pagepress.com.au')
        except socket.gaierror:
            logging.error("Failed to resolve the current server IP")
            return None

    def generateNewVps(self) -> str:
        return super().generateNewVps("prod_web")
    
    def switchToNewVps(self):
        self.runCmd(["terraform", "-chdir=terraform/update-dns", "apply", "-var-file=../terraform.tfvars", f"-var=vps_name={self.vpsName}", "-auto-approve"])

    def deactivateOldVps(self):
        pass

    def destroyNewVps(self, vpsName: str):
        super().destroyNewVps(vpsName)
        
        # Remove the DNS entry from the new VPS.
        self.runCmd(["terraform", "-chdir=terraform/update-dns", "destroy", "-var-file=../terraform.tfvars", f"-var=vps_name={vpsName}", "-auto-approve"])