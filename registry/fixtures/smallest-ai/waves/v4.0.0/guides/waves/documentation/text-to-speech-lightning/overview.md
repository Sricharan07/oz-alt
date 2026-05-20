> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Overview

> Lightning TTS API — generate speech from text with 217 voices across 12 languages, 44.1 kHz audio, ~200ms TTFB, and streaming support.

The Lightning TTS API converts text into natural speech via `https://api.smallest.ai/waves/v1`. 217 voices across 12 languages, 44.1 kHz native sample rate, \~200ms TTFB, with sync, SSE, and WebSocket streaming.

**Hear Lightning v3.1 (voice: magnus):**

  Your browser does not support the audio element.

Generate your first audio in under 60 seconds.

## Synthesis Modes

Choose the synthesis mode that best fits your application's needs:

Generate complete audio files with a single HTTP request. Ideal for pre-rendering content, batch processing, and applications where immediate streaming isn't required.

Receive audio chunks as they're generated via WebSocket. Perfect for real-time voice assistants, live narration, and low-latency conversational AI.

## Available Model

Our current TTS model. 44.1 kHz audio output, \~200ms TTFB, expressive human-like speech, and voice cloning. Supports 12 languages plus `auto` — English, Hindi, Spanish, and 9 Indian languages.

**Lightning v2 is deprecated.** New integrations should use Lightning v3.1. The v2 endpoints remain available for existing callers but are not recommended for new work.

## Feature Highlights

Optimized streaming pipeline delivers \~200ms time-to-first-byte (TTFB) for real-time applications. Lightning v3.1 achieves even faster response times for conversational AI.

Create custom voice profiles by uploading audio samples. Instant voice cloning works with just a few seconds of audio, while professional voice cloning delivers studio-quality results.

Multilingual support — English, Hindi, Spanish, and 9 Indian languages (Marathi, Kannada, Tamil, Bengali, Gujarati, Telugu, Malayalam, Punjabi, Odia). Plus `auto` for code-switching within a single session. See the [Lightning v3.1 model card](/waves/model-cards/text-to-speech/lightning-v-3-1#supported-languages) for the per-language voice count.

Choose from PCM, WAV, MP3, or μ-law encoding. Configurable sample rates from 8kHz to 44kHz to match your application's requirements.

Adjust speech rate with a simple multiplier. Slow down for clarity or speed up for faster content delivery without pitch distortion.

Define custom pronunciations for brand names, technical terms, and acronyms. Ensure consistent, accurate pronunciation across all synthesized audio.

Lightning v3.1 produces 44 kHz audio with natural prosody and expressiveness. Perfect for audiobooks, podcasts, and premium voice experiences.

Persistent connections for continuous audio streaming. Ideal for voice bots and interactive applications where latency is critical.

## Supported Languages

        Language

        Code

        Lightning v3.1

        English

        en

        Yes

        Hindi

        hi

        Yes

        Tamil

        ta

        Yes

        Kannada

        kn

        Yes

        Malayalam

        ml

        Yes

        Telugu

        te

        Yes

        Gujarati

        gu

        Yes

        Marathi

        mr

        Yes

        Bengali

        bn

        Yes

        Punjabi

        pa

        Yes

        Odia

        or

        Yes

        Spanish

        es

        Yes

For per-language voice counts, see the [Lightning v3.1 model card](/waves/model-cards/text-to-speech/lightning-v-3-1#supported-languages).

## Explore

First API call in 60 seconds

Real-time audio via WebSocket

Clone from 5-15 seconds of audio

20+ open-source examples on GitHub

See what developers have built

Lightning v3.1 specs and benchmarks
