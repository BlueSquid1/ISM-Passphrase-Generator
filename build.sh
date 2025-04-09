#docker compose -f docker-compose.yml up --build
set -e

# Building
docker build -t password-gen:0.0.1 .

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

# docker build -t blueSquid1/password-gen:0.0.1 .
# docker push blueSquid1/password-gen:0.0.1

# Use minikube docker daemon.
# eval $(minikube docker-env)
# docker build -t go-server .
kubectl apply -f deployment.yaml
kubectl rollout status deployment/go-server --timeout=60s
kubectl wait --for=condition=ready pod -l app=go-server --timeout=60s
minikube service go-server-service