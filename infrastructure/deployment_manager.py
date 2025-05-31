#!/usr/bin/env python3

import subprocess
import json
import logging
import os
import socket
from enum import Enum

FILE_PATH = os.path.dirname(os.path.realpath(__file__))

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
        

    def getCurrentServerIp(self, noCreating : bool = False) -> str | None:
        raise NotImplementedError("This method should be implemented by subclasses")

    def generateNewVps(self, vpsName: str, ignorePreviousBuild : bool) -> str:
        self.runCmd(["terraform", "-chdir=terraform/create-vps", "init"])
        if ignorePreviousBuild:
            self.runCmd(["terraform", "-chdir=terraform/create-vps", "state", "rm", "digitalocean_droplet.web"], check=False)
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

    def switchToNewVps(self, vpsIpAddress: str):
        raise NotImplementedError("This method should be implemented by subclasses")

    def deactivateOldVps(self, vpsIpAddress: str):
        raise NotImplementedError("This method should be implemented by subclasses")
    
    def destroyNewVps(self, vpsName: str):
        self.runCmd(["terraform", "-chdir=terraform/create-vps", "destroy", "-var-file=../terraform.tfvars", f"-var=vps_name={vpsName}", "-auto-approve"], check=False)


class DeploymentManagerPreProd(DeploymentManager):
    vpsName: str = "preprod-web"

    def getCurrentServerIp(self, noCreating : bool = False) -> str | None:
        if noCreating:
            return None
        
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
        return super().generateNewVps(self.vpsName, ignorePreviousBuild=False)
    
    def switchToNewVps(self, vpsIpAddress: str):
        # snapshot the new preprod server
        self.runCmd(["terraform", "-chdir=terraform/snapshot-vps", "init"])
        self.runCmd(["terraform", "-chdir=terraform/snapshot-vps", "apply", "-var-file=../terraform.tfvars", f"-var=vps_name={self.vpsName}", "-auto-approve"])

    def deactivateOldVps(self, vpsIpAddress: str):
        self.runCmd(["terraform", "-chdir=terraform/recreate-preprod", "destroy", "-var-file=../terraform.tfvars", "-auto-approve"], check=False)

    def destroyNewVps(self, vpsIpAddress: str):
        super().destroyNewVps(self.vpsName)

class DeploymentManagerProd(DeploymentManager):
    vpsName: str = "prod-web"

    def getCurrentServerIp(self, noCreating : bool = False) -> str | None:
        try:
            return socket.gethostbyname('www.pagepress.com.au')
        except socket.gaierror:
            logging.error("Failed to resolve the current server IP")
            return None

    def generateNewVps(self) -> str:
        # Always generate a new VPS for production, even if it already exists.
        return super().generateNewVps(self.vpsName, ignorePreviousBuild=True)
    
    def switchToNewVps(self, vpsIpAddress: str):
        self.runCmd(["terraform", "-chdir=terraform/update-dns", "init"])
        self.runCmd(["terraform", "-chdir=terraform/update-dns", "apply", "-var-file=../terraform.tfvars", f"-var=ip_address={vpsIpAddress}", "-auto-approve"])

    def deactivateOldVps(self, vpsIpAddress: str | None):
        if vpsIpAddress is None:
            return
        self.runCmd(["terraform", "-chdir=terraform/get-vps", "init"])
        self.runCmd(["terraform", "-chdir=terraform/get-vps", "apply", "-var-file=../terraform.tfvars", f"-var=vps_name={self.vpsName}", f"-var=ip_address={vpsIpAddress}", "-auto-approve"])
        result = self.runCmd(["terraform", "-chdir=terraform/get-vps", "output", "-raw", "node_details"])
        oldVps = json.loads(result.stdout)
        if len(oldVps) != 1:
            raise Exception(f"There should only be one node in the old VPS but got: {oldVps}")
        
        oldVpsId = oldVps[0]['droplet_id']
        # Terraform needs a root module to destroy resources.
        with open("/tmp/main.tf", "w") as f:
            content = """
                # Use the DigitalOcean terraform provider.
                terraform {
                required_providers {
                    digitalocean = {
                    source = "digitalocean/digitalocean"
                    version = "~> 2.0"
                    }
                }
                }
                variable "do_token" { }
                provider "digitalocean" { token = var.do_token }
                resource "digitalocean_droplet" "web" {
                    name = "placeholder"
                    image = "ubuntu-20-04-x64"
                    size = "s-1vcpu-1gb"
                }
            """
            f.write(content)
        self.runCmd(["terraform", "-chdir=/tmp", "init"])
        self.runCmd(["terraform", "-chdir=/tmp", "import", f"-var-file={FILE_PATH}/terraform/terraform.tfvars", "digitalocean_droplet.web", f"{oldVpsId}"])
        self.runCmd(["terraform", "-chdir=/tmp", "destroy", f"-var-file={FILE_PATH}/terraform/terraform.tfvars", "-target=digitalocean_droplet.web", "-auto-approve"])

    def destroyNewVps(self, vpsIpAddress: str):
        # Remove the DNS entry from the new VPS.
        self.runCmd(["terraform", "-chdir=terraform/update-dns", "destroy", "-var-file=../terraform.tfvars", f"-var=ip_address={vpsIpAddress}", "-auto-approve"], check=False)

        super().destroyNewVps(self.vpsName)