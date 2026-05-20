> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Quick Start

> Deploy Smallest Self-Host on Kubernetes with Helm

Kubernetes deployment is currently available for **ASR (Speech-to-Text)** only. For TTS deployments, use [Docker](/waves/self-host/docker-setup/tts-deployment/quick-start).

Ensure you've completed all [prerequisites](/waves/self-host/kubernetes-setup/prerequisites/hardware-requirements) before starting.

## Add Helm Repository

```bash
helm repo add smallest-self-host https://smallest-inc.github.io/smallest-self-host
helm repo update
```

## Create Namespace

```bash
kubectl create namespace smallest
kubectl config set-context --current --namespace=smallest
```

## Configure Values

Create a `values.yaml` file:

```yaml values.yaml
global:
  licenseKey: "your-license-key-here"
  imageCredentials:
    create: true
    registry: quay.io
    username: "your-registry-username"
    password: "your-registry-password"
    email: "your-email@example.com"

models:
  asrModelUrl: "your-model-url-here"

scaling:
  replicas:
    lightningAsr: 1
    licenseProxy: 1

lightningAsr:
  nodeSelector:
  tolerations:

redis:
  enabled: true
  auth:
    enabled: true
```

Replace placeholder values with credentials provided by Smallest.ai support.

## Install

```bash
helm install smallest-self-host smallest-self-host/smallest-self-host \
  -f values.yaml \
  --namespace smallest
```

Monitor the deployment:

```bash
kubectl get pods -w
```

        Component

        Startup Time

        Ready Indicator

        Redis

        \~30s

        1/1 Running

        License Proxy

        \~1m

        1/1 Running

        Lightning ASR

        2-10m

        1/1 Running

         (model download on first run)

        API Server

        \~30s

        1/1 Running

Model downloads are cached when using shared storage (EFS). Subsequent starts complete in under a minute.

## Verify Installation

```bash
kubectl get pods,svc
```

All pods should show `Running` status with the following services available:

        Service

        Port

        Description

        api-server

        7100

        REST API endpoint

        lightning-asr-internal

        2269

        ASR inference service

        license-proxy

        3369

        License validation

        redis-master

        6379

        Request queue

## Test the API

Port forward and send a health check:

```bash
kubectl port-forward svc/api-server 7100:7100
```

```bash
curl http://localhost:7100/health
```

## Autoscaling

Enable automatic scaling based on real-time inference load:

```yaml values.yaml
scaling:
  auto:
    enabled: true
```

This deploys HorizontalPodAutoscalers that scale based on active requests:

        Component

        Metric

        Default Target

        Behavior

        Lightning ASR

        asr_active_requests

        4 per pod

        Scales GPU workers based on inference queue depth

        API Server

        lightning_asr_replica_count

        2:1 ratio

        Maintains API capacity proportional to ASR workers

### How It Works

1. **Lightning ASR** exposes `asr_active_requests` metric on port 9090
2. **Prometheus** scrapes this metric via ServiceMonitor
3. **Prometheus Adapter** makes it available to the Kubernetes metrics API
4. **HPA** scales pods when average requests per pod exceeds target

### Configuration

```yaml values.yaml
scaling:
  auto:
    enabled: true
    lightningAsr:
      hpa:
        minReplicas: 1
        maxReplicas: 10
        targetActiveRequests: 4
```

### Verify Autoscaling

```bash
kubectl get hpa
```

```
NAME            REFERENCE                  TARGETS   MINPODS   MAXPODS   REPLICAS
lightning-asr   Deployment/lightning-asr   0/4       1         10        1
api-server      Deployment/api-server      1/2       1         10        1
```

The `TARGETS` column shows `current/target`. When current exceeds target, pods scale up.

Autoscaling requires the Prometheus stack. It's included as a dependency and enabled by default.

## Helm Operations

```bash Upgrade
helm upgrade smallest-self-host smallest-self-host/smallest-self-host \
  -f values.yaml -n smallest
```

```bash Rollback
helm rollback smallest-self-host -n smallest
```

```bash Uninstall
helm uninstall smallest-self-host -n smallest
```

```bash View Config
helm get values smallest-self-host -n smallest
```

## Troubleshooting

        Issue

        Cause

        Resolution

        Pods

        Pending

        Insufficient resources or missing GPU nodes

        Check

        kubectl describe pod

         for scheduling errors

        ImagePullBackOff

        Invalid registry credentials

        Verify

        imageCredentials

         in values.yaml

        CrashLoopBackOff

        Invalid license or insufficient memory

        Check logs with

        kubectl logs  --previous

        Slow model download

        Large model size (~20GB)

        Use shared storage (EFS) for caching

For detailed troubleshooting, see [Troubleshooting Guide](/waves/self-host/kubernetes-setup/troubleshooting).

## Next Steps

EKS-specific configuration

Shared storage for faster cold starts

Fine-tune scaling behavior and thresholds

Grafana dashboards and alerting
