> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Why Self-Host?

> Understand when self-hosting our models makes sense for your organization

## Overview

Using Smallest as a managed service has many benefits: it's fast to start developing with, requires no infrastructure setup, and eliminates all hardware, installation, configuration, backup, and maintenance-related costs. However, there are situations where a self-hosted deployment makes more sense.

## Performance Requirements

Certain use cases have very sensitive latency and load requirements. If you need ultra-low latency with voice AI services colocated with your other services, self-hosting can meet these requirements.

* **Real-time AI voicebots** requiring sub-100ms response times
* **Live transcription systems** for broadcasts or conferences
* **High-volume processing** with predictable costs
* **Edge deployments** with limited internet connectivity

- Colocate speech services with your application infrastructure
- Scale independently based on your specific workload patterns
- Zero network latency to external APIs
- Consistent performance regardless of internet conditions

### Zero Network Latency

When you self-host, your speech services run within your own infrastructure—whether that's the same data center, VPC, or even the same machine as your application. This eliminates the round-trip time to external APIs entirely.

        Scenario

        Network Latency

        Self-hosted

        1-5ms

        Same region

        20-50ms

        Cross-region

        100-200ms

        Edge/on-premises

        200-500ms+

For real-time voice applications like AI agents, every millisecond matters. Self-hosting keeps your latency predictable and minimal, regardless of where your users are located or the state of the public internet.

### Security & Data Privacy

One of the most common use cases for self-hosting Smallest is to satisfy security or data privacy requirements. In a typical self-hosted deployment, no audio, transcripts, or other identifying markers of the request content are sent to Smallest servers.

* **Healthcare applications** requiring HIPAA compliance
* **Financial services** with strict data governance
* **Government and defense** applications
* **Enterprise environments** with air-gapped networks

- Your audio data never leaves your infrastructure
- Transcripts remain entirely within your control
- No data stored beyond the duration of the API request
- Self-hosted deployments do not persist request/response data

### What Data is Reported?

In a typical self-hosted deployment, no audio or transcript data is sent to Smallest servers. Only usage metadata is reported to the license server for validation and billing purposes.

**Metadata reported:**

* Audio duration and character count
* Features requested (diarization, timestamps, etc.)
* Success/error response codes

**Never reported:**

* Audio content
* Transcripts or synthesis output
* Personally identifiable information

### Cost Optimization

For high-volume or predictable workloads, self-hosting can be more cost-effective than per-request API pricing.

        Benefit

        Description

        Predictable costs

        Infrastructure-based pricing, not usage-based

        Efficient utilization

        Predictable autoscaling maximizes resource efficiency

        Long-term savings

        Significant cost reduction for sustained high volumes

### Reliability & Grace Periods

Self-hosted deployments include built-in resilience against unforeseen network errors and temporary outages. The deployment won't suddenly stop working due to a transient network issue or external service disruption.

This means:

* **Continuous operation** during network interruptions or license server maintenance
* **Protection against unforeseen errors** — your services keep running while issues are resolved
* **Time to recover** — grace periods provide a buffer to restore connectivity without impacting your users

The License Proxy supports **grace periods** that allow your deployment to continue operating even if connectivity to the Smallest license server is temporarily lost.

## Customization & Control

Self-hosting provides complete control over your deployment:

Optimize compute resources for your specific workload patterns. Allocate more GPU power during peak hours and scale down during off-peak times.

Upgrade on your schedule. Test new versions in staging before production rollout. Roll back instantly if needed.

Deploy in private networks, VPCs, or air-gapped environments. Full control over ingress and egress traffic.

Direct integration with your monitoring, logging, and alerting infrastructure. Custom Prometheus metrics, Grafana dashboards, and alerting rules.

## When to Use Managed Service Instead

Self-hosting isn't always the right choice. Consider the managed Smallest API if:

* You're building a prototype or MVP
* Your audio processing volume is low or unpredictable
* You don't have DevOps resources to manage infrastructure
* You need to get started quickly without infrastructure setup

## Ready to Self-Host?

Return to the introduction for deployment options

Deploy in 15 minutes with Docker
