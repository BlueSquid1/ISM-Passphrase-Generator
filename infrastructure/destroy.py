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
    
    print("Destroying new VPS")
    deployMgr.destroyNewVps()
    print("Deactivating old VPS")
    deployMgr.deactivateOldVps()

    print("finished")
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deployment Destroyer")
    parser.add_argument('-e' ,'--environment', type=Environment, help='', choices=list(Environment), default=Environment.PREPROD)
    args = parser.parse_args()
    main(args.environment)