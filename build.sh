#!/bin/bash
set -e

# Building
docker build --platform=linux/amd64 -t password-gen:0.0.1 .

# Publishing
docker login
docker tag password-gen:0.0.1 bluesquid2/password-gen:0.0.1
docker push bluesquid2/password-gen:0.0.1

# start kubernetes
#minikube delete
if minikube status --format='{{.Host}}' | grep -q "Running"; then
    echo "Minikube is already running."
else
    echo "Starting Minikube..."
    minikube start
fi

kubectl apply -f deployment.yaml
kubectl wait --for=condition=Ready pod/passphrase-generator --timeout=60s
minikube service passphrase-generator-service