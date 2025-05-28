#!/usr/bin/env python3

import argparse

from deployment_manager import DeploymentManager, DeploymentManagerPreProd, Environment

def main(environment: Environment):
    deployMgr : DeploymentManager = None
    if environment == Environment.PREPROD:
        deployMgr = DeploymentManagerPreProd()
    else:
        raise ValueError(f"Unsupported environment: {environment}")
    
    newIpAddress = deployMgr.generateNewServer()
    currentIpAddress = deployMgr.getCurrentServerIp()
    if currentIpAddress is None:
        # Can't get the current server IP, This is probably because it's the first time.
        # Just use the new VPS as the IP for the first time
        currentIpAddress = newIpAddress
    deployMgr.runAnsibleOnNewVps(newIpAddress, currentIpAddress)

    # run integration tests
    testsPassed = deployMgr.runIntegrationTests()
    if not testsPassed:
        return 0xFF

    deployMgr.switchToNewVps()

    deployMgr.deactivateOldVps()

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Blue Green Deployment Manager")
    parser.add_argument('-e' ,'--environment', type=Environment, help='', choices=list(Environment), default=Environment.PREPROD)
    args = parser.parse_args()
    main(args.environment)