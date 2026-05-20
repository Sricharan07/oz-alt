> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Metrics Overview

> Key Pulse STT metrics for quality and latency.

Pulse STT evaluations revolve around four pillars:

1. **Accuracy** – how close transcripts are to the ground truth.
2. **Latency & throughput** – how quickly and efficiently results arrive.
3. **Enrichment quality** – how reliable diarization, timestamps, and metadata are.

## Accuracy metrics

### Word Error Rate (WER)

* Formula: `WER = (Substitutions + Deletions + Insertions) / Total Words`.
* Interprets overall transcript fidelity; normalize casing/punctuation before computing.

### Character Error Rate (CER)

* Parallel to WER but at the character level; useful for languages with compact scripts or heavy compounding.

### Sentence accuracy

* Percentage of sentences that match ground truth exactly.
* Tracks readability for QA/customer-support recaps.

## Latency & throughput

### Time to First Result (TTFR)

* Measures the delay between request start and first interim token.
* For real-time agents, keep TTFR below \~30 ms to maintain natural turn-taking.

### End-to-end latency

* Wall-clock time from submission to final transcript.
* Report p50/p90/p95 to capture outliers introduced by long files or retries.

### Real-Time Factor (RTF)

* `RTF = Processing Time / Audio Duration`.
* Values less than 1 indicate faster-than-real-time processing; Pulse STT typically runs near 0.4 RTF on clean inputs.

## Enrichment quality

        Metric

        What to watch

        Why it matters

        Diarization accuracy

        % of words with correct

        speaker_id

        Call-center QA, coaching, compliance

        Word timestamp drift

        Gap between predicted and reference timestamps

        Subtitle alignment and editing

        Sentence-level timestamps

        % of audio covered by

        utterances

         segments

        Chaptering, meeting notes

        Emotion/gender precision

        Confidence distribution

        Routing, analytics, compliance flags

## Coverage & robustness

* **Language detection accuracy**: share of files that land on the intended ISO 639-1 code or auto-detected language.
* **Noise robustness**: WER delta at multiple SNR levels (clean vs. +5 dB noise, etc.).
* **Accent/domain diversity**: track WER per accent or scenario (support, media, meetings) to avoid blind spots.

## Operational metrics

* **Requests per second / concurrent sessions**: validate you stay within quota and plan scaling needs.
* **Cost per minute**: Pulse STT bills per second at \$0.025/minute list price—include enrichment toggles when modeling cost.
* **Retry volume**: differentiate infrastructure retries (HTTP 5xx) from transcription failures to spot upstream vs downstream issues.

## Reporting checklist

1. Describe dataset composition (language, accent, domain, duration).
2. Publish WER/CER, TTFR, and RTF with averages and percentiles.
3. Include enrichment coverage (how many segments include diarization/timestamps).
4. Summarize cost/latency impact when enabling optional features.
5. Link to reproducible scripts or notebooks for auditing.
