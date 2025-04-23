test running a pod:
```
kubectl run testpod --image=busybox --restart=Never -- sleep 3600
kubectl exec testpod -- nslookup kubernetes.default
```

See all user defined pods:
`kubectl get pods -o wide`

See all user defined services:
`kubectl get svc`

See all nodes:
`kubectl get nodes -o wide`

Use minikube docker daemon.
```
eval $(minikube docker-env)
docker build -t go-server .
```

## Thoughts on how to do CI/CD
dev -> unit tests -> pre-prod -> approves pull request -> prod

dev - an environment where engineers can independently develop their features
unit tests - runs when compiling code on dev and in the CI/CD pipeline on pull requests
pre-prod - uses terraform to make VPSs on digital ocean. Does E2E testing. Uses save states to save money and to make rollback easy.
approves pull request - reviewer checks code and does smoke testing in pre-prod. When they approve the change the save states in pre-prod are updated
prod - changes are deployed with the same ansible and terraform script to prod. If there is an issue detected in prod will use blue/green deployments to rollback. Fix will come as another pull request rather than repairing the prod VPSs.

## Thoughts on branching stratgeries
- keep it simple. Releases will be from trunk. 