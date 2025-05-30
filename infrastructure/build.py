#!/usr/bin/env python3

import argparse

from deployment_manager import DeploymentManager, DeploymentManagerPreProd, DeploymentManagerProd, Environment

def main(environment: Environment):
    deployMgr : DeploymentManager = None
    if environment == Environment.PREPROD:
        deployMgr = DeploymentManagerPreProd()
    elif environment == Environment.PROD:
        deployMgr = DeploymentManagerProd()
    else:
        raise ValueError(f"Unsupported environment: {environment}")
    
    print("Generating new VPS")
    newIpAddress = deployMgr.generateNewVps()
    print(f"New VPS IP: {newIpAddress}")
    print("getting current server IP")
    currentIpAddress = deployMgr.getCurrentServerIp()
    print(f"Current server IP: {currentIpAddress}")

    if currentIpAddress is None:
        # Can't get the current server IP, This is probably because it's the first time.
        # Just use the new VPS as the IP for the first time
        currentIpAddress = newIpAddress

    print("Running Ansible on new VPS")
    deployMgr.runAnsibleOnNewVps(newIpAddress, currentIpAddress)

    # run integration tests
    print("Running integration tests")
    testsPassed = deployMgr.runIntegrationTests()
    if not testsPassed:
        return 0xFF
    
    print("Integration tests passed")

    print("Switching to new VPS")
    deployMgr.switchToNewVps()

    print("Deactivating old VPS")
    deployMgr.deactivateOldVps()

    print("finished")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Blue Green Deployment Manager")
    parser.add_argument('-e' ,'--environment', type=Environment, help='', choices=list(Environment), default=Environment.PREPROD)
    args = parser.parse_args()
    main(args.environment)