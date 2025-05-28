#!/usr/bin/env python3
from deployment_manager import DeploymentManagerPreProd
def main():
    deployment = DeploymentManagerPreProd()
    # Destroy the new VPS
    deployment.destroyNewVps()
    
    # Destroy the preprod environment
    deployment.deactivateOldVps()

    return 0

if __name__ == "__main__":
    main()