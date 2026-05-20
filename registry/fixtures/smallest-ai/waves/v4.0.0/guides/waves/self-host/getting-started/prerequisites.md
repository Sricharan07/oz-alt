> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Prerequisites

> What you need before deploying Smallest Self-Host

## Overview

Before deploying Smallest Self-Host, you'll need credentials from Smallest.ai and infrastructure with GPU support.

## Credentials from Smallest.ai

Contact **[support@smallest.ai](mailto:support@smallest.ai)** to obtain the following:

Your unique license key for validation. This is required for all deployments.

You'll add this to your configuration:

```yaml
global:
  licenseKey: "your-license-key-here"
```

Or as an environment variable:

```bash
LICENSE_KEY=your-license-key-here
```

Credentials to pull Docker images from `quay.io`:

* **Username**
* **Password**
* **Email**

Login to the registry:

```bash
docker login quay.io
```

For Kubernetes, you'll add these to your `values.yaml`:

```yaml
global:
  imageCredentials:
    create: true
    registry: quay.io
    username: "your-username"
    password: "your-password"
    email: "your-email@example.com"
```

Download URLs for the AI models (STT and/or TTS).

For Docker deployments, add to your `.env`:

```bash
MODEL_URL=your-model-url-here
```

For Kubernetes, add to `values.yaml`:

```yaml
models:
  asrModelUrl: "your-asr-model-url"
  ttsModelUrl: "your-tts-model-url"
```

## Infrastructure Requirements

* **NVIDIA GPU** with 16+ GB VRAM
* Recommended: A10, L4, L40s, T4, or A100
* NVIDIA Driver 525+ (for A10, A100, L4)
* NVIDIA Driver 470+ (for T4, V100)

- Docker 20.10+ or Podman 4.0+
- NVIDIA Container Toolkit
- For Kubernetes: GPU Operator or Device Plugin

### Minimum Resources

        Component

        CPU

        Memory

        GPU

        Storage

        Lightning ASR

        4-8 cores

        12-16 GB

        1x NVIDIA (16+ GB VRAM)

        50+ GB

        Lightning TTS

        4-8 cores

        12-16 GB

        1x NVIDIA (16+ GB VRAM)

        20+ GB

        API Server

        0.5-2 cores

        512 MB - 2 GB

        None

        1 GB

        License Proxy

        0.25-1 core

        256-512 MB

        None

        100 MB

        Redis

        0.5-1 core

        512 MB - 2 GB

        None

        1 GB

## Network Requirements

The License Proxy requires outbound HTTPS access to validate licenses:

        Endpoint

        Port

        Purpose

        api.smallest.ai

        443

        License validation and usage reporting

Ensure your firewall and network policies allow outbound HTTPS traffic to `api.smallest.ai`.

## Next Steps

Choose your deployment method and follow the specific prerequisites:

Setup requirements for Docker deployments including NVIDIA Container Toolkit installation.

Cluster requirements, GPU node setup, and Helm configuration for Kubernetes deployments.
