> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Debugging Guide

> Advanced debugging techniques for Smallest Self-Host

## Overview

This guide covers advanced debugging techniques for troubleshooting complex issues with Smallest Self-Host.

## Debugging Tools

### Docker Debugging

#### Enter Running Container

```bash
docker exec -it  /bin/bash
```

Inside the container:

```bash
ls -la
ps aux
df -h
nvidia-smi
env
```

#### Debug Failed Container

View logs of crashed container:

```bash
docker logs
docker logs  --tail=100 --follow
```

Inspect container configuration:

```bash
docker inspect
```

#### Network Debugging

Check container networking:

```bash
docker network ls
docker network inspect
docker exec  ping license-proxy
docker exec  curl http://license-proxy:3369/health
```

### Kubernetes Debugging

#### Debug Pod

Interactive debug container:

```bash
kubectl debug  -it --image=ubuntu --target=
```

Copy debug tools into pod:

```bash
kubectl cp ./debug-script.sh :/tmp/debug.sh
kubectl exec -it  -- bash /tmp/debug.sh
```

#### Ephemeral Debug Container

Add temporary container to running pod:

```bash
kubectl debug -it  --image=nicolaka/netshoot --target=lightning-asr
```

Inside debug container:

```bash
nslookup license-proxy
curl http://api-server:7100/health
tcpdump -i eth0
```

#### Get Previous Logs

If pod crashed and restarted:

```bash
kubectl logs  --previous
kubectl logs  -c  --previous
```

## Network Debugging

### Test Service Connectivity

From inside cluster:

```bash
kubectl run netdebug --rm -it --restart=Never \
  --image=nicolaka/netshoot \
  --namespace=smallest \
  -- bash
```

Inside debug pod:

```bash
nslookup api-server
nslookup license-proxy
nslookup lightning-asr

curl http://api-server:7100/health
curl http://license-proxy:3369/health

traceroute api-server
ping -c 3 lightning-asr
```

### DNS Resolution

Check DNS is working:

```bash
kubectl run dnstest --rm -it --restart=Never \
  --image=busybox \
  -- nslookup kubernetes.default
```

Check CoreDNS logs:

```bash
kubectl logs -n kube-system -l k8s-app=kube-dns
```

### Network Policies

List network policies:

```bash
kubectl get networkpolicy -n smallest
kubectl describe networkpolicy  -n smallest
```

Temporarily disable for testing:

```bash
kubectl delete networkpolicy  -n smallest
```

Remember to recreate network policies after testing!

## Performance Debugging

### Resource Usage

Check pod resource consumption:

```bash
kubectl top pods -n smallest
kubectl top pods -n smallest --sort-by=memory
kubectl top pods -n smallest --sort-by=cpu
```

Check node resource usage:

```bash
kubectl top nodes
kubectl describe node  | grep -A 10 "Allocated resources"
```

### GPU Debugging

Check GPU availability in pod:

```bash
kubectl exec -it  -- nvidia-smi

kubectl exec -it  -- nvidia-smi dmon
```

Watch GPU utilization:

```bash
kubectl exec -it  -- watch -n 1 nvidia-smi
```

Check GPU events:

```bash
kubectl exec -it  -- nvidia-smi -q -d MEMORY,UTILIZATION,POWER,CLOCK,PERFORMANCE
```

### Application Profiling

Profile Lightning ASR:

```bash
kubectl exec -it  -- sh -c 'apt-get update && apt-get install -y python3-pip && pip3 install py-spy'

kubectl exec -it  -- py-spy top --pid 1
```

Memory profiling:

```bash
kubectl exec -it  -- sh -c 'cat /proc/1/status | grep -i mem'
```

## Log Analysis

### Structured Log Parsing

Extract errors from logs:

```bash
kubectl logs  | grep -i "error\|exception\|failed"
```

Count errors:

```bash
kubectl logs  | grep -i "error" | wc -l
```

Show errors with context:

```bash
kubectl logs  | grep -B 5 -A 5 "error"
```

### Log Aggregation

Combine logs from all replicas:

```bash
kubectl logs -l app=lightning-asr -n smallest --tail=100 --all-containers=true
```

Follow logs from multiple pods:

```bash
kubectl logs -l app=lightning-asr -f --max-log-requests=10
```

### Parse JSON Logs

Using `jq`:

```bash
kubectl logs  | jq 'select(.level=="error")'
kubectl logs  | jq 'select(.duration > 1000)'
kubectl logs  | jq '.message' -r
```

## Database Debugging

### Redis Debugging

Connect to Redis:

```bash
kubectl exec -it  -- redis-cli
```

Inside Redis CLI:

```redis
AUTH your-password
INFO
DBSIZE
KEYS *
GET some_key
MONITOR
```

Check Redis memory:

```redis
INFO memory
```

Check slow queries:

```redis
SLOWLOG GET 10
```

## API Debugging

### Test API Endpoints

Health check:

```bash
kubectl port-forward svc/api-server 7100:7100
curl http://localhost:7100/health
```

Test transcription:

```bash
curl -X POST http://localhost:7100/v1/listen \
  -H "Authorization: Token ${LICENSE_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www2.cs.uic.edu/~i101/SoundFiles/StarWars60.wav"}' \
  -v
```

### Request Tracing

Add request ID tracking:

```bash
curl -X POST http://localhost:7100/v1/listen \
  -H "Authorization: Token ${LICENSE_KEY}" \
  -H "X-Request-ID: debug-123" \
  -H "Content-Type: application/json" \
  -d '{"url": "..."}' \
  -v
```

Grep logs for request:

```bash
kubectl logs -l app=api-server | grep "debug-123"
kubectl logs -l app=lightning-asr | grep "debug-123"
```

### Packet Capture

Capture network traffic:

```bash
kubectl exec -it  -- apt-get update && apt-get install -y tcpdump

kubectl exec -it  -- tcpdump -i any -w /tmp/capture.pcap port 7100

kubectl cp :/tmp/capture.pcap ./capture.pcap
```

Analyze with Wireshark or:

```bash
tcpdump -r capture.pcap -A
```

## Event Debugging

### Watch Events

Real-time events:

```bash
kubectl get events -n smallest --watch
```

Filter by type:

```bash
kubectl get events -n smallest --field-selector type=Warning
```

Sort by timestamp:

```bash
kubectl get events -n smallest --sort-by='.lastTimestamp'
```

### Event Analysis

Count events by reason:

```bash
kubectl get events -n smallest -o json | jq '.items | group_by(.reason) | map({reason: .[0].reason, count: length})'
```

## Metrics Debugging

### Check Prometheus Metrics

Port forward Prometheus:

```bash
kubectl port-forward -n default svc/smallest-prometheus-stack-prometheus 9090:9090
```

Query metrics:

Open [http://localhost:9090](http://localhost:9090) and run:

```promql
asr_active_requests
rate(asr_total_requests[5m])
asr_gpu_utilization
```

### Check Custom Metrics

Verify metrics available to HPA:

```bash
kubectl get --raw "/apis/custom.metrics.k8s.io/v1beta1" | jq .
```

Query specific metric:

```bash
kubectl get --raw "/apis/custom.metrics.k8s.io/v1beta1/namespaces/smallest/pods/*/asr_active_requests" | jq .
```

## Debugging Checklists

### Startup Issues Checklist

```bash
kubectl describe pod  | grep -A 10 "Events"
```

```bash
kubectl get secrets -n smallest
kubectl describe secret
```

```bash
kubectl describe node  | grep "Allocated resources" -A 10
```

```bash
kubectl logs  --all-containers=true
```

### Performance Issues Checklist

```bash
kubectl top pods -n smallest
kubectl top nodes
```

```bash
kubectl exec  -- nvidia-smi
```

```bash
kubectl get hpa
kubectl describe hpa lightning-asr
```

```bash
kubectl get --raw "/apis/custom.metrics.k8s.io/v1beta1"
```

## Advanced Techniques

### Enable Debug Logging

Increase log verbosity:

```yaml
lightningAsr:
  env:
    - name: LOG_LEVEL
      value: "DEBUG"
```

### Simulate Failures

Test error handling:

```bash
kubectl delete pod
kubectl drain  --ignore-daemonsets
```

### Load Testing

Generate load:

```bash
kubectl run load-test --rm -it --image=williamyeh/hey \
  -- -z 5m -c 50 http://api-server:7100/health
```

### Chaos Engineering

Test resilience (requires Chaos Mesh):

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: pod-failure
spec:
  action: pod-failure
  mode: one
  selector:
    namespaces:
      - smallest
    labelSelectors:
      app: lightning-asr
  duration: "30s"
```

## What's Next?

Learn to interpret logs and errors

Quick fixes for frequent problems
