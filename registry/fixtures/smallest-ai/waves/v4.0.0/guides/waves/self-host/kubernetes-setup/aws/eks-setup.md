> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# AWS EKS Setup

> Create and configure an EKS cluster for Smallest Self-Host with GPU support

## Overview

This guide walks you through creating an Amazon EKS cluster optimized for running Smallest Self-Host with GPU acceleration.

## Prerequisites

Install and configure AWS CLI:

```bash
aws --version
aws configure
```

Install eksctl (EKS cluster management tool):

```bash
brew install eksctl
```

Verify:

```bash
eksctl version
```

Install kubectl:

```bash
brew install kubectl
```

Ensure your AWS user/role has permissions to:

* Create EKS clusters
* Manage EC2 instances
* Create IAM roles
* Manage VPC resources

## Cluster Configuration

### Option 1: Quick Start with eksctl

Create a cluster with GPU nodes using a single command:

```bash
eksctl create cluster \
  --name smallest-cluster \
  --region us-east-1 \
  --version 1.28 \
  --nodegroup-name cpu-nodes \
  --node-type t3.large \
  --nodes 2 \
  --nodes-min 1 \
  --nodes-max 3 \
  --managed
```

Then add GPU node group:

```bash
eksctl create nodegroup \
  --cluster smallest-cluster \
  --region us-east-1 \
  --name gpu-nodes \
  --node-type g5.xlarge \
  --nodes 1 \
  --nodes-min 0 \
  --nodes-max 5 \
  --managed \
  --node-labels "workload=gpu,nvidia.com/gpu=true" \
  --node-taints "nvidia.com/gpu=true:NoSchedule"
```

This creates a cluster with separate CPU and GPU node groups, allowing for cost-effective scaling.

### Option 2: Using Cluster Config File

Create a cluster configuration file for more control:

```yaml cluster-config.yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: smallest-cluster
  region: us-east-1
  version: "1.28"

iam:
  withOIDC: true

managedNodeGroups:
  - name: cpu-nodes
    instanceType: t3.large
    minSize: 1
    maxSize: 3
    desiredCapacity: 2
    volumeSize: 50
    ssh:
      allow: false
    labels:
      workload: cpu
    tags:
      Environment: production
      Application: smallest-self-host

  - name: gpu-nodes
    instanceType: g5.xlarge
    minSize: 0
    maxSize: 5
    desiredCapacity: 1
    volumeSize: 100
    ssh:
      allow: false
    labels:
      workload: gpu
      nvidia.com/gpu: "true"
      node.kubernetes.io/instance-type: g5.xlarge
    taints:
      - key: nvidia.com/gpu
        value: "true"
        effect: NoSchedule
    tags:
      Environment: production
      Application: smallest-self-host
      NodeType: gpu
    iam:
      withAddonPolicies:
        autoScaler: true
        ebs: true
        efs: true

addons:
  - name: vpc-cni
  - name: coredns
  - name: kube-proxy
  - name: aws-ebs-csi-driver
```

Create the cluster:

```bash
eksctl create cluster -f cluster-config.yaml
```

Cluster creation takes 15-20 minutes. Monitor progress in the AWS CloudFormation console.

## GPU Instance Types

Choose the right GPU instance type for your workload:

        Instance Type

        GPU

        VRAM

        vCPUs

        RAM

        $/hour*

        Recommended For

        g5.xlarge

        1x A10G

        24 GB

        4

        16 GB

        $1.00

        Development, testing

        g5.2xlarge

        1x A10G

        24 GB

        8

        32 GB

        $1.21

        Small production

        g5.4xlarge

        1x A10G

        24 GB

        16

        64 GB

        $1.63

        Medium production

        g5.12xlarge

        4x A10G

        96 GB

        48

        192 GB

        $5.67

        High-volume production

        p3.2xlarge

        1x V100

        16 GB

        8

        61 GB

        $3.06

        Legacy workloads

  \* Approximate on-demand pricing in us-east-1, subject to change

**Recommendation**: Start with `g5.xlarge` for development and testing. Scale to `g5.2xlarge` or higher for production.

## Verify Cluster

### Check Cluster Status

```bash
eksctl get cluster --name smallest-cluster --region us-east-1
```

### Verify Node Groups

```bash
eksctl get nodegroup --cluster smallest-cluster --region us-east-1
```

### Configure kubectl

```bash
aws eks update-kubeconfig --name smallest-cluster --region us-east-1
```

Verify access:

```bash
kubectl get nodes
```

Expected output:

```
NAME                         STATUS   ROLES    AGE   VERSION
ip-xxx-cpu-1                 Ready       5m    v1.28.x
ip-xxx-cpu-2                 Ready       5m    v1.28.x
ip-xxx-gpu-1                 Ready       5m    v1.28.x
```

### Verify GPU Nodes

Check GPU availability:

```bash
kubectl get nodes -l workload=gpu -o json | \
  jq '.items[].status.capacity'
```

Look for `nvidia.com/gpu` in the output:

```json
{
  "cpu": "4",
  "memory": "15944904Ki",
  "nvidia.com/gpu": "1",
  "pods": "29"
}
```

## Install NVIDIA Device Plugin

The NVIDIA device plugin enables GPU scheduling in Kubernetes.

### Using Helm (Recommended)

The Smallest Self-Host chart includes the NVIDIA GPU Operator. Enable it in your values:

```yaml values.yaml
gpu-operator:
  enabled: true
```

### Manual Installation

If installing separately:

```bash
kubectl create -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.0/nvidia-device-plugin.yml
```

Verify:

```bash
kubectl get pods -n kube-system | grep nvidia
```

## Install EBS CSI Driver

Required for persistent volumes:

### Using eksctl

```bash
eksctl create addon \
  --name aws-ebs-csi-driver \
  --cluster smallest-cluster \
  --region us-east-1
```

### Using AWS Console

1. Navigate to EKS → Clusters → smallest-cluster → Add-ons
2. Click "Add new"
3. Select "Amazon EBS CSI Driver"
4. Click "Add"

### Verify EBS CSI Driver

```bash
kubectl get pods -n kube-system -l app=ebs-csi-controller
```

## Install EFS CSI Driver (Optional)

Recommended for shared model storage across pods.

### Create IAM Policy

```bash
curl -o iam-policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-efs-csi-driver/master/docs/iam-policy-example.json

aws iam create-policy \
  --policy-name AmazonEKS_EFS_CSI_Driver_Policy \
  --policy-document file://iam-policy.json
```

### Create IAM Service Account

```bash
eksctl create iamserviceaccount \
  --cluster smallest-cluster \
  --region us-east-1 \
  --namespace kube-system \
  --name efs-csi-controller-sa \
  --attach-policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/AmazonEKS_EFS_CSI_Driver_Policy \
  --approve
```

Replace `YOUR_ACCOUNT_ID` with your AWS account ID.

### Install EFS CSI Driver

```bash
kubectl apply -k "github.com/kubernetes-sigs/aws-efs-csi-driver/deploy/kubernetes/overlays/stable/?ref=release-1.7"
```

Verify:

```bash
kubectl get pods -n kube-system -l app=efs-csi-controller
```

## Enable Cluster Autoscaler

See the [Cluster Autoscaler](/waves/self-host/kubernetes-setup/autoscaling/cluster-autoscaler) guide for detailed setup.

Quick setup:

```bash
eksctl create iamserviceaccount \
  --cluster smallest-cluster \
  --region us-east-1 \
  --namespace kube-system \
  --name cluster-autoscaler \
  --attach-policy-arn arn:aws:iam::aws:policy/AutoScalingFullAccess \
  --approve \
  --override-existing-serviceaccounts
```

## Cost Optimization

### Use Spot Instances for GPU Nodes

Reduce costs by up to 70% with Spot instances:

```yaml cluster-config.yaml
managedNodeGroups:
  - name: gpu-nodes-spot
    instanceType: g5.xlarge
    minSize: 0
    maxSize: 5
    desiredCapacity: 1
    spot: true
    instancesDistribution:
      maxPrice: 0.50
      instanceTypes: ["g5.xlarge", "g5.2xlarge"]
      onDemandBaseCapacity: 0
      onDemandPercentageAboveBaseCapacity: 0
      spotAllocationStrategy: capacity-optimized
```

Spot instances can be interrupted with 2-minute warning. Ensure your application handles graceful shutdowns.

### Right-Size Node Groups

Start small and scale based on metrics:

```yaml
managedNodeGroups:
  - name: gpu-nodes
    minSize: 0
    maxSize: 10
    desiredCapacity: 1
```

Set `minSize: 0` to scale down to zero during off-hours.

### Enable Cluster Autoscaler

Automatically adjust node count based on demand:

```yaml values.yaml
cluster-autoscaler:
  enabled: true
  autoDiscovery:
    clusterName: smallest-cluster
  awsRegion: us-east-1
```

## Security Best Practices

### Enable Private Endpoint

```bash
eksctl utils update-cluster-endpoint \
  --cluster smallest-cluster \
  --region us-east-1 \
  --private-access=true \
  --public-access=false
```

### Enable Logging

```bash
eksctl utils update-cluster-logging \
  --cluster smallest-cluster \
  --region us-east-1 \
  --enable-types all \
  --approve
```

### Update Security Groups

Restrict inbound access to API server:

```bash
aws ec2 describe-security-groups \
  --filters "Name=tag:aws:eks:cluster-name,Values=smallest-cluster"
```

Update rules to allow only specific IPs.

## Troubleshooting

### GPU Nodes Not Ready

Check NVIDIA device plugin:

```bash
kubectl get pods -n kube-system | grep nvidia
kubectl describe node
```

### Pods Stuck in Pending

Check node capacity:

```bash
kubectl describe pod
kubectl get nodes -o json | jq '.items[].status.allocatable'
```

### EBS Volumes Not Mounting

Verify EBS CSI driver:

```bash
kubectl get pods -n kube-system -l app=ebs-csi-controller
kubectl logs -n kube-system -l app=ebs-csi-controller
```

## What's Next?

Configure IAM roles for service accounts

Advanced GPU node configuration and optimization

Set up shared file storage for models

Enable automatic node scaling
