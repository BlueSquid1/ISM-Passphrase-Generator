test running a pod:
```
kubectl run testpod --image=busybox --restart=Never -- sleep 3600
kubectl exec testpod -- nslookup kubernetes.default
```

see external ip addresses:
`kubectl get service -A`