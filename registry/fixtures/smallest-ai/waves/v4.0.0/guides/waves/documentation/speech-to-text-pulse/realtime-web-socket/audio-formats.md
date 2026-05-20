> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Audio Specifications

> Supported audio encoding formats and requirements for real-time WebSocket transcription

## Supported Encoding Formats

The Pulse STT WebSocket API supports the following audio encoding formats for real-time streaming:

        Encoding

        Description

        Use Case

        linear16

        16-bit linear PCM

        Recommended for best quality

        linear32

        32-bit linear PCM

        High-fidelity audio

        alaw

        A-law encoding

        Telephony systems

        mulaw

        μ-law encoding

        Telephony systems (North America)

        opus

        Opus compressed audio

        Low bandwidth, high quality

        ogg_opus

        Ogg Opus container

        Ogg container with Opus codec

## Supported Sample Rates

Sample rate is the number of times the audio signal is measured per second. A higher sample rate naturally implies audio of better detail and higher quality. However it increases the size of the audio file.

The WebSocket API supports the following sample rates:

* **8000 Hz**
* **16000 Hz**
* **22050 Hz**
* **24000 Hz**
* **44100 Hz**
* **48000 Hz**

## Audio Requirements

### Chunk Size

The recommended size is `4096 bytes` per chunk.

Sending audio in consistent 4096-byte chunks helps maintain optimal latency and processing efficiency. It minimizes the tradeoff between processing latency and network latency, finding the right fit between number of requests and the size of each request.

### Channels

Currently, we support only single-channel (mono) transcription. Multi-channel support is coming soon.

### Streaming Rate

For optimal real-time performance:

* Stream chunks at regular intervals (e.g., every 50-100ms)
* Maintain consistent chunk sizes when possible
* Avoid sending chunks too rapidly or too slowly

## Format Recommendations

### Best Quality (Default)

Use 16 kHz mono Linear PCM (`linear16`) for the optimal mix of accuracy and processing speed:

```
Encoding: linear16
Sample Rate: 16000 Hz
Channels: Mono
Chunk Size: 4096 bytes
```

### Telephony Quality

Use 8 kHz μ-law or A-law encoding for low bandwidth usage:

```
Encoding: mulaw or alaw
Sample Rate: 8000 Hz
Channels: Mono
Chunk Size: 4096 bytes
```

### High Fidelity

For broadcast or high-quality scenarios, use higher sample rates:

```
Encoding: linear16 or linear32
Sample Rate: 44100 or 48000 Hz
Channels: Mono
Chunk Size: 4096 bytes
```

## Audio Preprocessing

Before streaming audio to the WebSocket API, ensure your audio is:

1. **Converted to the correct format**: Use the specified encoding (linear16, linear32, alaw, mulaw, opus, or ogg\_opus)
2. **Set to the correct sample rate**: Match the `sample_rate` parameter in your WebSocket URL
3. **Mono channel**: Downmix stereo or multi-channel audio to mono
4. **Properly chunked**: Split audio into 4096-byte chunks for streaming

### Example: Converting Audio for Streaming

```python
import numpy as np
import soundfile as sf

# Read audio file
audio, sample_rate = sf.read('input.wav')

# Convert to mono if stereo
if len(audio.shape) > 1:
    audio = np.mean(audio, axis=1)

# Resample to 16 kHz if needed
if sample_rate != 16000:
    from scipy import signal
    audio = signal.resample(audio, int(len(audio) * 16000 / sample_rate))

# Convert to 16-bit PCM
audio_int16 = (audio * 32767).astype(np.int16)

# Split into 4096-byte chunks
chunk_size = 4096
chunks = [audio_int16[i:i+chunk_size//2] for i in range(0, len(audio_int16), chunk_size//2)]
```

## Query Parameters

Specify encoding and sample rate in the WebSocket connection URL:

```javascript
const url = new URL("wss://api.smallest.ai/waves/v1/pulse/get_text");
url.searchParams.append("encoding", "linear16");
url.searchParams.append("sample_rate", "16000");
```
