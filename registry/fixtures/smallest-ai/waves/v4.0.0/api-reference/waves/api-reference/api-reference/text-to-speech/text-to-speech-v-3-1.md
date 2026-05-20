> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Lightning v3.1 WebSocket

GET /waves/v1/lightning-v3.1/get_speech/stream

# Lightning v3.1 WebSocket

Synthesize speech over a persistent WebSocket. Audio chunks come back as text arrives — the fit-for-purpose path when *text itself* is streaming, like LLM token output.

## When to use this

- **Use this** when text is generated incrementally and you want audio to start playing as soon as the first words are produced — LLM streaming, live captioning, voice agents.
- **Use SSE streaming** when you have the full text up front but want low-latency playback.
- **Use sync `/get_speech`** when latency isn't critical and a single buffer is easier to handle.

## How it works

1. Open a WebSocket to `wss://api.smallest.ai/waves/v1/lightning-v3.1/get_speech/stream` with `Authorization: Bearer `.
2. Send a JSON message per text chunk: `{ "voice_id": "magnus", "text": "...", "continue": true, "flush": false, ... }`. Set `continue: true` to keep the session open between sends.
3. The server pushes back JSON messages with `data.audio` (base64 PCM) and a `status` field (`chunk`, `complete`).
4. When you're done sending text, push one final message with `flush: true` and an empty `text` — the server finishes the buffer and sends `status: "complete"`.

## Concurrency and rate limits

- 1 concurrency unit = 1 active TTS request at a time.
- You can open up to 5 WebSocket connections per concurrency unit.
- Requests beyond your concurrency limit are rejected with an error — queue on your side.

Examples: 3 concurrency = up to 15 open sockets, but only 3 active synth requests at once.

## Examples

**Python** (using `smallestai>=4.4.0` — the 4.3.1 compatibility shim):
```python
from smallestai.waves import WavesStreamingTTS, TTSConfig

config = TTSConfig(voice_id="magnus", api_key="YOUR_API_KEY", sample_rate=24000)
tts = WavesStreamingTTS(config)

def text_chunks():
    # Pretend this is your LLM streaming tokens.
    for word in ["Hello,", " I am", " streaming", " speech."]:
        yield word

with open("speech.pcm", "wb") as out:
    for audio_chunk in tts.synthesize_streaming(text_chunks(), continue_stream=True, auto_flush=True):
        out.write(audio_chunk)
```

For new code, you can also use the namespaced Fern client: `client.waves.lightning_v31tts.connect(...)` which returns a typed socket you drive yourself.

**JavaScript / TypeScript** (using `ws`)
```typescript
import WebSocket from "ws";

const ws = new WebSocket("wss://api.smallest.ai/waves/v1/lightning-v3.1/get_speech/stream", {
  headers: { Authorization: `Bearer ${process.env.SMALLEST_API_KEY}` },
});

ws.on("open", () => {
  for (const text of ["Hello,", " I am", " streaming", " speech."]) {
    ws.send(JSON.stringify({
      voice_id: "magnus",
      text,
      sample_rate: 24000,
      continue: true,
      flush: false,
    }));
  }
  // Final flush
  ws.send(JSON.stringify({ voice_id: "magnus", text: "", flush: true }));
});

ws.on("message", (raw) => {
  const msg = JSON.parse(raw.toString());
  if (msg.status === "complete") return ws.close();
  const pcm = Buffer.from(msg.data.audio, "base64");
  // … hand pcm to your audio pipeline
});
```

## Common gotchas

- **`continue: true` keeps the session alive.** Without it, the server closes after the first chunk. Send `flush: true` with empty `text` when you're done.
- **44.1 kHz is supported but most pipelines want 24 kHz.** Match your downstream sample rate to avoid resampling.
- **Backpressure**: if you push text faster than the server can synthesize, audio chunks queue server-side. Watch for `complete_backoff_ms` in responses.
- **One concurrency unit = one in-flight synth.** Holding 5 sockets open doesn't get you 5× throughput unless you upgrade concurrency.
- **JavaScript / TypeScript**: the official `smallestai` npm package predates Lightning v3.1, so connect with the `ws` library directly as shown above.

Reference: https://docs.smallest.ai/waves/api-reference/api-reference/text-to-speech/text-to-speech-v-3-1

## AsyncAPI Specification

```yaml
asyncapi: 2.6.0
info:
  title: Text to Speech V3.1
  version: subpackage_textToSpeechV31.Text to Speech V3.1
  description: >
    # Lightning v3.1 WebSocket

    Synthesize speech over a persistent WebSocket. Audio chunks come back as
    text arrives — the fit-for-purpose path when *text itself* is streaming,
    like LLM token output.

    ## When to use this

    - **Use this** when text is generated incrementally and you want audio to
    start playing as soon as the first words are produced — LLM streaming, live
    captioning, voice agents.

    - **Use SSE streaming** when you have the full text up front but want
    low-latency playback.

    - **Use sync `/get_speech`** when latency isn't critical and a single buffer
    is easier to handle.

    ## How it works

    1. Open a WebSocket to
    `wss://api.smallest.ai/waves/v1/lightning-v3.1/get_speech/stream` with
    `Authorization: Bearer `.

    2. Send a JSON message per text chunk: `{ "voice_id": "magnus", "text":
    "...", "continue": true, "flush": false, ... }`. Set `continue: true` to
    keep the session open between sends.

    3. The server pushes back JSON messages with `data.audio` (base64 PCM) and a
    `status` field (`chunk`, `complete`).

    4. When you're done sending text, push one final message with `flush: true`
    and an empty `text` — the server finishes the buffer and sends `status:
    "complete"`.

    ## Concurrency and rate limits

    - 1 concurrency unit = 1 active TTS request at a time.

    - You can open up to 5 WebSocket connections per concurrency unit.

    - Requests beyond your concurrency limit are rejected with an error — queue
    on your side.

    Examples: 3 concurrency = up to 15 open sockets, but only 3 active synth
    requests at once.

    ## Examples

    **Python** (using `smallestai>=4.4.0` — the 4.3.1 compatibility shim):

    ```python

    from smallestai.waves import WavesStreamingTTS, TTSConfig

    config = TTSConfig(voice_id="magnus", api_key="YOUR_API_KEY",
    sample_rate=24000)

    tts = WavesStreamingTTS(config)

    def text_chunks():
        # Pretend this is your LLM streaming tokens.
        for word in ["Hello,", " I am", " streaming", " speech."]:
            yield word

    with open("speech.pcm", "wb") as out:
        for audio_chunk in tts.synthesize_streaming(text_chunks(), continue_stream=True, auto_flush=True):
            out.write(audio_chunk)
    ```

    For new code, you can also use the namespaced Fern client:
    `client.waves.lightning_v31tts.connect(...)` which returns a typed socket
    you drive yourself.

    **JavaScript / TypeScript** (using `ws`)

    ```typescript

    import WebSocket from "ws";

    const ws = new
    WebSocket("wss://api.smallest.ai/waves/v1/lightning-v3.1/get_speech/stream",
    {
      headers: { Authorization: `Bearer ${process.env.SMALLEST_API_KEY}` },
    });

    ws.on("open", () => {
      for (const text of ["Hello,", " I am", " streaming", " speech."]) {
        ws.send(JSON.stringify({
          voice_id: "magnus",
          text,
          sample_rate: 24000,
          continue: true,
          flush: false,
        }));
      }
      // Final flush
      ws.send(JSON.stringify({ voice_id: "magnus", text: "", flush: true }));
    });

    ws.on("message", (raw) => {
      const msg = JSON.parse(raw.toString());
      if (msg.status === "complete") return ws.close();
      const pcm = Buffer.from(msg.data.audio, "base64");
      // … hand pcm to your audio pipeline
    });

    ```

    ## Common gotchas

    - **`continue: true` keeps the session alive.** Without it, the server
    closes after the first chunk. Send `flush: true` with empty `text` when
    you're done.

    - **44.1 kHz is supported but most pipelines want 24 kHz.** Match your
    downstream sample rate to avoid resampling.

    - **Backpressure**: if you push text faster than the server can synthesize,
    audio chunks queue server-side. Watch for `complete_backoff_ms` in
    responses.

    - **One concurrency unit = one in-flight synth.** Holding 5 sockets open
    doesn't get you 5× throughput unless you upgrade concurrency.

    - **JavaScript / TypeScript**: the official `smallestai` npm package
    predates Lightning v3.1, so connect with the `ws` library directly as shown
    above.
channels:
  /waves/v1/lightning-v3.1/get_speech/stream:
    description: >
      # Lightning v3.1 WebSocket

      Synthesize speech over a persistent WebSocket. Audio chunks come back as
      text arrives — the fit-for-purpose path when *text itself* is streaming,
      like LLM token output.

      ## When to use this

      - **Use this** when text is generated incrementally and you want audio to
      start playing as soon as the first words are produced — LLM streaming,
      live captioning, voice agents.

      - **Use SSE streaming** when you have the full text up front but want
      low-latency playback.

      - **Use sync `/get_speech`** when latency isn't critical and a single
      buffer is easier to handle.

      ## How it works

      1. Open a WebSocket to
      `wss://api.smallest.ai/waves/v1/lightning-v3.1/get_speech/stream` with
      `Authorization: Bearer `.

      2. Send a JSON message per text chunk: `{ "voice_id": "magnus", "text":
      "...", "continue": true, "flush": false, ... }`. Set `continue: true` to
      keep the session open between sends.

      3. The server pushes back JSON messages with `data.audio` (base64 PCM) and
      a `status` field (`chunk`, `complete`).

      4. When you're done sending text, push one final message with `flush:
      true` and an empty `text` — the server finishes the buffer and sends
      `status: "complete"`.

      ## Concurrency and rate limits

      - 1 concurrency unit = 1 active TTS request at a time.

      - You can open up to 5 WebSocket connections per concurrency unit.

      - Requests beyond your concurrency limit are rejected with an error —
      queue on your side.

      Examples: 3 concurrency = up to 15 open sockets, but only 3 active synth
      requests at once.

      ## Examples

      **Python** (using `smallestai>=4.4.0` — the 4.3.1 compatibility shim):

      ```python

      from smallestai.waves import WavesStreamingTTS, TTSConfig

      config = TTSConfig(voice_id="magnus", api_key="YOUR_API_KEY",
      sample_rate=24000)

      tts = WavesStreamingTTS(config)

      def text_chunks():
          # Pretend this is your LLM streaming tokens.
          for word in ["Hello,", " I am", " streaming", " speech."]:
              yield word

      with open("speech.pcm", "wb") as out:
          for audio_chunk in tts.synthesize_streaming(text_chunks(), continue_stream=True, auto_flush=True):
              out.write(audio_chunk)
      ```

      For new code, you can also use the namespaced Fern client:
      `client.waves.lightning_v31tts.connect(...)` which returns a typed socket
      you drive yourself.

      **JavaScript / TypeScript** (using `ws`)

      ```typescript

      import WebSocket from "ws";

      const ws = new
      WebSocket("wss://api.smallest.ai/waves/v1/lightning-v3.1/get_speech/stream",
      {
        headers: { Authorization: `Bearer ${process.env.SMALLEST_API_KEY}` },
      });

      ws.on("open", () => {
        for (const text of ["Hello,", " I am", " streaming", " speech."]) {
          ws.send(JSON.stringify({
            voice_id: "magnus",
            text,
            sample_rate: 24000,
            continue: true,
            flush: false,
          }));
        }
        // Final flush
        ws.send(JSON.stringify({ voice_id: "magnus", text: "", flush: true }));
      });

      ws.on("message", (raw) => {
        const msg = JSON.parse(raw.toString());
        if (msg.status === "complete") return ws.close();
        const pcm = Buffer.from(msg.data.audio, "base64");
        // … hand pcm to your audio pipeline
      });

      ```

      ## Common gotchas

      - **`continue: true` keeps the session alive.** Without it, the server
      closes after the first chunk. Send `flush: true` with empty `text` when
      you're done.

      - **44.1 kHz is supported but most pipelines want 24 kHz.** Match your
      downstream sample rate to avoid resampling.

      - **Backpressure**: if you push text faster than the server can
      synthesize, audio chunks queue server-side. Watch for
      `complete_backoff_ms` in responses.

      - **One concurrency unit = one in-flight synth.** Holding 5 sockets open
      doesn't get you 5× throughput unless you upgrade concurrency.

      - **JavaScript / TypeScript**: the official `smallestai` npm package
      predates Lightning v3.1, so connect with the `ws` library directly as
      shown above.
    bindings:
      ws:
        headers:
          type: object
          properties:
            Authorization:
              type: string
    publish:
      operationId: text-to-speech-v-3-1-publish
      summary: LightningV31TtsResponse
      description: Receive audio data chunks and completion status from the server.
      message:
        name: LightningV31TtsResponse
        title: LightningV31TtsResponse
        description: Receive audio data chunks and completion status from the server.
        payload:
          $ref: >-
            #/components/schemas/lightningV31Stream_lightningV31TtsResponse.message
    subscribe:
      operationId: text-to-speech-v-3-1-subscribe
      summary: LightningV31TtsRequest
      description: >-
        Send a JSON message with voice_id, text, and optional parameters to
        generate speech audio.
      message:
        name: LightningV31TtsRequest
        title: LightningV31TtsRequest
        description: >-
          Send a JSON message with voice_id, text, and optional parameters to
          generate speech audio.
        payload:
          $ref: >-
            #/components/schemas/lightningV31Stream_lightningV31TtsRequest.message
servers:
  Production:
    url: wss://api.smallest.ai/
    protocol: wss
components:
  schemas:
    ChannelsLightningV31StreamMessagesLightningV31TtsResponseMessageStatus:
      type: string
      enum:
        - chunk
        - complete
      description: >-
        Status of the TTS request, `chunk` indicates incoming audio chunk,
        `complete` indicates completion.
      title: ChannelsLightningV31StreamMessagesLightningV31TtsResponseMessageStatus
    ChannelsLightningV31StreamMessagesLightningV31TtsResponseMessageData:
      type: object
      properties:
        audio:
          type: string
          description: Base64-encoded audio chunk
      title: ChannelsLightningV31StreamMessagesLightningV31TtsResponseMessageData
    lightningV31Stream_lightningV31TtsResponse.message:
      type: object
      properties:
        session_id:
          type: string
          description: >-
            Internal session identifier (system-generated, stable for the
            WebSocket connection lifetime).
        request_id:
          type: string
          description: >-
            Internal request identifier (system-generated UUID, unique per TTS
            synthesis).
        external_session_id:
          type: string
          description: Echoed client-provided session_id (omitted if not provided).
        external_request_id:
          type: string
          description: Echoed client-provided request_id (omitted if not provided).
        status:
          $ref: >-
            #/components/schemas/ChannelsLightningV31StreamMessagesLightningV31TtsResponseMessageStatus
          description: >-
            Status of the TTS request, `chunk` indicates incoming audio chunk,
            `complete` indicates completion.
        data:
          $ref: >-
            #/components/schemas/ChannelsLightningV31StreamMessagesLightningV31TtsResponseMessageData
      title: lightningV31Stream_lightningV31TtsResponse.message
    ChannelsLightningV31StreamMessagesLightningV31TtsRequestMessageLanguage:
      type: string
      enum:
        - auto
        - en
        - hi
        - mr
        - kn
        - ta
        - bn
        - gu
        - te
        - ml
        - pa
        - or
        - es
      default: en
      description: >
        Language code for synthesis. Influences pronunciation, number/date

        normalization, and phoneme selection.

        - Indian: `en`, `hi`, `mr`, `kn`, `ta`, `bn`, `gu`, `te`, `ml`, `pa`,
        `or`

        - European: `es` (Spanish)

        - `auto` — auto-detect from input text
      title: ChannelsLightningV31StreamMessagesLightningV31TtsRequestMessageLanguage
    lightningV31Stream_lightningV31TtsRequest.message:
      type: object
      properties:
        voice_id:
          type: string
          description: The ID of the voice to use
        text:
          type: string
          description: The text to convert to speech
        max_buffer_flush_ms:
          type: integer
          default: 0
          description: >-
            The maximum time (in ms) to wait for more input before generating
            output. It flushes when either this time is reached or enough input
            is received for optimal output—whichever comes first. This is useful
            for input streams. Defaults to 0
        continue:
          type: boolean
          default: false
          description: >-
            This setting controls whether the system should buffer and wait for
            more input after receiving the current one. If not set, it assumes
            no more input is coming.
        flush:
          type: boolean
          default: false
          description: >-
            This setting controls whether the system should flush the current
            buffer.
        complete_backoff_ms:
          type: number
          format: double
          default: 4000
          description: >-
            The time in ms to wait after the last chunk is sent before sending
            the complete response. Default is 4000ms. Maximum is 10000ms.
        language:
          $ref: >-
            #/components/schemas/ChannelsLightningV31StreamMessagesLightningV31TtsRequestMessageLanguage
          default: en
          description: >
            Language code for synthesis. Influences pronunciation, number/date

            normalization, and phoneme selection.

            - Indian: `en`, `hi`, `mr`, `kn`, `ta`, `bn`, `gu`, `te`, `ml`,
            `pa`, `or`

            - European: `es` (Spanish)

            - `auto` — auto-detect from input text
        sample_rate:
          type: integer
          default: 44100
          description: 'Audio sample rate in Hz. Supported values: 8000, 16000, 24000, 44100'
        speed:
          type: number
          format: double
          default: 1
          description: Speaking speed multiplier
        session_id:
          type: string
          description: >-
            Optional client-provided session identifier for correlation. Only
            alphanumeric characters, hyphens, underscores, and dots allowed. Max
            128 characters. Echoed back in responses as `external_session_id`.
        request_id:
          type: string
          description: >-
            Optional client-provided request identifier for correlation. Only
            alphanumeric characters, hyphens, underscores, and dots allowed. Max
            128 characters. Echoed back in responses as `external_request_id`.
      required:
        - voice_id
        - text
      title: lightningV31Stream_lightningV31TtsRequest.message

```
