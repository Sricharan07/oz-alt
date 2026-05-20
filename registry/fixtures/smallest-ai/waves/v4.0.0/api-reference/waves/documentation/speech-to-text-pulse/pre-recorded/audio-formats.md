> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Audio Specifications

> Supported formats, codecs, and recommendations for pre-recorded audio

## Input Methods

Our API supports two input methods for transcribing audio:

        Method

        Content Type

        Use Case

        Raw Bytes

        application/octet-stream

        Upload audio files directly from your system

        Audio URL

        application/json

        Process audio files hosted on a remote server

## Supported Formats

The Pulse STT API supports a wide range of audio formats for pre-recorded transcription.

        Format

        Extension

        Codec

        Notes

        WAV

        .wav

        PCM, Linear PCM

        Recommended for best quality

        MP3

        .mp3

        MPEG Audio Layer III

        Widely compatible

        FLAC

        .flac

        Free Lossless Audio Codec

        Lossless compression

        OGG

        .ogg

        Vorbis, Opus

        Open source format

        M4A

        .m4a

        AAC, ALAC

        Apple format

        WebM

        .webm

        Opus, Vorbis

        Web-optimized

## Audio Requirements

### Sample Rate

* **Recommended**: 16 kHz (16,000 Hz)
* **Supported range**: All frequencies
* **Optimal**: 16 kHz mono for speech recognition

### Channels

Currently we support only single channel transcription. We are bringing in multi-channel support soon.

### Limits

* **Maximum size**: No limit on file size
* **Session timeout**: 10 minutes per Session

It is recommended to split the file into chunks and then upload them in parallel for faster processing.

## Format Recommendations

### Best Quality

Use 16 kHz mono Linear PCM (`audio/wav`) for the optimal mix of accuracy and processing speed. This configuration mirrors Waves’ recommended production setup for real-time speech workloads.

```
Format: WAV (Linear PCM)
Sample Rate: 16 kHz
Channels: Mono
Bit Depth: 16-bit
```

### Balanced (Telephony & Voice)

Use 8 kHz μ-law encoded with 8-bit encoding for low bandwidth usage. It provides standard quality for voice-only applications like phone calls.

```
Format: MP3 or μ-law
Sample Rate: 8 kHz
Channels: Mono
Bitrate: 64–96 kbps
```

### Web-Optimized / High Fidelity

For broadcast, captioning, or multimedia scenarios, it is recommended to capture higher sample rates (44.1–48 kHz). Due to the higher quality requirements, bandwidth and processing times would be on the higher side.

```
Format: WebM (Opus) or FLAC
Sample Rate: 44.1–48 kHz
Channels: Mono or Stereo (downmix before upload)
Bitrate: 96–160 kbps
```
