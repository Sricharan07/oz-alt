> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Pulse (Realtime)

GET /waves/v1/pulse/get_text

Transcribe audio in real time over a persistent WebSocket. The fit-for-purpose path for live captioning, voice agents, and any flow where you need partial transcripts as the user is still speaking.

## When to use this

- **Use this** for live audio: microphone input, voice-agent turns, simultaneous interpretation, low-latency captioning. Partial results stream back while audio is still arriving.
- **Use the pre-recorded REST endpoint** (`POST /waves/v1/pulse/get_text`) when you have a complete file. Single request, single response, less plumbing.

## How it works

1. Open a WebSocket to `wss://api.smallest.ai/waves/v1/pulse/get_text` with `Authorization: Bearer ` and the session params (`language`, `sample_rate`, `encoding`, etc.) as query string.
2. Stream raw PCM (or your chosen `encoding`) over the socket as binary frames.
3. The server pushes back JSON `transcriptionResponse` messages — partial results (`is_final: false`) as you speak, finalized text (`is_final: true`) when an utterance closes.
4. Send a `finalize` message to force end-of-utterance, or `close_stream` to end the session.

## Examples

**Python** (real-time mic input)
```python
import asyncio, json, websockets, pyaudio

URL = "wss://api.smallest.ai/waves/v1/pulse/get_text?language=en&sample_rate=16000&encoding=linear16&word_timestamps=true"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

async def stream_mic():
    pa = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=320)
    async with websockets.connect(URL, additional_headers=HEADERS) as ws:
        async def send_audio():
            while True:
                await ws.send(stream.read(320))
        async def recv_transcripts():
            async for msg in ws:
                data = json.loads(msg)
                tag = "FINAL " if data.get("is_final") else "partial"
                print(f"[{tag}] {data.get('transcript')}")
        await asyncio.gather(send_audio(), recv_transcripts())

asyncio.run(stream_mic())
```

**JavaScript / TypeScript** (using `ws`)
```typescript
import WebSocket from "ws";
import { readFileSync } from "node:fs";

const params = new URLSearchParams({
  language: "en", sample_rate: "16000", encoding: "linear16", word_timestamps: "true",
});
const ws = new WebSocket(`wss://api.smallest.ai/waves/v1/pulse/get_text?${params}`, {
  headers: { Authorization: `Bearer ${process.env.SMALLEST_API_KEY}` },
});

ws.on("open", () => {
  const audio = readFileSync("./call.pcm"); // 16-bit mono PCM at 16 kHz
  for (let i = 0; i  {
  const data = JSON.parse(raw.toString());
  const tag = data.is_final ? "FINAL " : "partial";
  console.log(`[${tag}] ${data.transcript}`);
  if (data.is_last) ws.close();
});
```

## Common gotchas

- **Match `sample_rate` to your audio.** The server will not resample for you — sending 44.1 kHz audio with `sample_rate=16000` produces garbage transcripts.
- **`finalize` vs `close_stream`**: `finalize` ends the current utterance and triggers a final transcript without closing the session. `close_stream` ends the session entirely.
- **`keywords` is WebSocket-only.** Pass them on connect for proper-noun / jargon boosting; not available on the REST endpoint.
- **`format`/`punctuate`/`capitalize`** are accepted at the wire level today. They currently return the same transcript regardless of value — pass them in your integration so it works as the behavior changes.
- **PII/PCI redaction (`redact_pii`, `redact_pci`)** runs server-side on finalized transcripts only — partials may show the unredacted text briefly before being replaced.
- **JavaScript / TypeScript**: the official `smallestai` npm package predates the Pulse model, so connect with the `ws` library directly as shown above.

Reference: https://docs.smallest.ai/waves/api-reference/api-reference/speech-to-text/speech-to-text

## AsyncAPI Specification

```yaml
asyncapi: 2.6.0
info:
  title: Speech to Text
  version: subpackage_speechToText.Speech to Text
  description: >
    Transcribe audio in real time over a persistent WebSocket. The
    fit-for-purpose path for live captioning, voice agents, and any flow where
    you need partial transcripts as the user is still speaking.

    ## When to use this

    - **Use this** for live audio: microphone input, voice-agent turns,
    simultaneous interpretation, low-latency captioning. Partial results stream
    back while audio is still arriving.

    - **Use the pre-recorded REST endpoint** (`POST /waves/v1/pulse/get_text`)
    when you have a complete file. Single request, single response, less
    plumbing.

    ## How it works

    1. Open a WebSocket to `wss://api.smallest.ai/waves/v1/pulse/get_text` with
    `Authorization: Bearer ` and the session params (`language`,
    `sample_rate`, `encoding`, etc.) as query string.

    2. Stream raw PCM (or your chosen `encoding`) over the socket as binary
    frames.

    3. The server pushes back JSON `transcriptionResponse` messages — partial
    results (`is_final: false`) as you speak, finalized text (`is_final: true`)
    when an utterance closes.

    4. Send a `finalize` message to force end-of-utterance, or `close_stream` to
    end the session.

    ## Examples

    **Python** (real-time mic input)

    ```python

    import asyncio, json, websockets, pyaudio

    URL =
    "wss://api.smallest.ai/waves/v1/pulse/get_text?language=en&sample_rate=16000&encoding=linear16&word_timestamps=true"

    HEADERS = {"Authorization": f"Bearer {API_KEY}"}

    async def stream_mic():
        pa = pyaudio.PyAudio()
        stream = pa.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=320)
        async with websockets.connect(URL, additional_headers=HEADERS) as ws:
            async def send_audio():
                while True:
                    await ws.send(stream.read(320))
            async def recv_transcripts():
                async for msg in ws:
                    data = json.loads(msg)
                    tag = "FINAL " if data.get("is_final") else "partial"
                    print(f"[{tag}] {data.get('transcript')}")
            await asyncio.gather(send_audio(), recv_transcripts())

    asyncio.run(stream_mic())

    ```

    **JavaScript / TypeScript** (using `ws`)

    ```typescript

    import WebSocket from "ws";

    import { readFileSync } from "node:fs";

    const params = new URLSearchParams({
      language: "en", sample_rate: "16000", encoding: "linear16", word_timestamps: "true",
    });

    const ws = new
    WebSocket(`wss://api.smallest.ai/waves/v1/pulse/get_text?${params}`, {
      headers: { Authorization: `Bearer ${process.env.SMALLEST_API_KEY}` },
    });

    ws.on("open", () => {
      const audio = readFileSync("./call.pcm"); // 16-bit mono PCM at 16 kHz
      for (let i = 0; i  {
      const data = JSON.parse(raw.toString());
      const tag = data.is_final ? "FINAL " : "partial";
      console.log(`[${tag}] ${data.transcript}`);
      if (data.is_last) ws.close();
    });

    ```

    ## Common gotchas

    - **Match `sample_rate` to your audio.** The server will not resample for
    you — sending 44.1 kHz audio with `sample_rate=16000` produces garbage
    transcripts.

    - **`finalize` vs `close_stream`**: `finalize` ends the current utterance
    and triggers a final transcript without closing the session. `close_stream`
    ends the session entirely.

    - **`keywords` is WebSocket-only.** Pass them on connect for proper-noun /
    jargon boosting; not available on the REST endpoint.

    - **`format`/`punctuate`/`capitalize`** are accepted at the wire level
    today. They currently return the same transcript regardless of value — pass
    them in your integration so it works as the behavior changes.

    - **PII/PCI redaction (`redact_pii`, `redact_pci`)** runs server-side on
    finalized transcripts only — partials may show the unredacted text briefly
    before being replaced.

    - **JavaScript / TypeScript**: the official `smallestai` npm package
    predates the Pulse model, so connect with the `ws` library directly as shown
    above.
channels:
  /waves/v1/pulse/get_text:
    description: >
      Transcribe audio in real time over a persistent WebSocket. The
      fit-for-purpose path for live captioning, voice agents, and any flow where
      you need partial transcripts as the user is still speaking.

      ## When to use this

      - **Use this** for live audio: microphone input, voice-agent turns,
      simultaneous interpretation, low-latency captioning. Partial results
      stream back while audio is still arriving.

      - **Use the pre-recorded REST endpoint** (`POST /waves/v1/pulse/get_text`)
      when you have a complete file. Single request, single response, less
      plumbing.

      ## How it works

      1. Open a WebSocket to `wss://api.smallest.ai/waves/v1/pulse/get_text`
      with `Authorization: Bearer ` and the session params (`language`,
      `sample_rate`, `encoding`, etc.) as query string.

      2. Stream raw PCM (or your chosen `encoding`) over the socket as binary
      frames.

      3. The server pushes back JSON `transcriptionResponse` messages — partial
      results (`is_final: false`) as you speak, finalized text (`is_final:
      true`) when an utterance closes.

      4. Send a `finalize` message to force end-of-utterance, or `close_stream`
      to end the session.

      ## Examples

      **Python** (real-time mic input)

      ```python

      import asyncio, json, websockets, pyaudio

      URL =
      "wss://api.smallest.ai/waves/v1/pulse/get_text?language=en&sample_rate=16000&encoding=linear16&word_timestamps=true"

      HEADERS = {"Authorization": f"Bearer {API_KEY}"}

      async def stream_mic():
          pa = pyaudio.PyAudio()
          stream = pa.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=320)
          async with websockets.connect(URL, additional_headers=HEADERS) as ws:
              async def send_audio():
                  while True:
                      await ws.send(stream.read(320))
              async def recv_transcripts():
                  async for msg in ws:
                      data = json.loads(msg)
                      tag = "FINAL " if data.get("is_final") else "partial"
                      print(f"[{tag}] {data.get('transcript')}")
              await asyncio.gather(send_audio(), recv_transcripts())

      asyncio.run(stream_mic())

      ```

      **JavaScript / TypeScript** (using `ws`)

      ```typescript

      import WebSocket from "ws";

      import { readFileSync } from "node:fs";

      const params = new URLSearchParams({
        language: "en", sample_rate: "16000", encoding: "linear16", word_timestamps: "true",
      });

      const ws = new
      WebSocket(`wss://api.smallest.ai/waves/v1/pulse/get_text?${params}`, {
        headers: { Authorization: `Bearer ${process.env.SMALLEST_API_KEY}` },
      });

      ws.on("open", () => {
        const audio = readFileSync("./call.pcm"); // 16-bit mono PCM at 16 kHz
        for (let i = 0; i  {
        const data = JSON.parse(raw.toString());
        const tag = data.is_final ? "FINAL " : "partial";
        console.log(`[${tag}] ${data.transcript}`);
        if (data.is_last) ws.close();
      });

      ```

      ## Common gotchas

      - **Match `sample_rate` to your audio.** The server will not resample for
      you — sending 44.1 kHz audio with `sample_rate=16000` produces garbage
      transcripts.

      - **`finalize` vs `close_stream`**: `finalize` ends the current utterance
      and triggers a final transcript without closing the session.
      `close_stream` ends the session entirely.

      - **`keywords` is WebSocket-only.** Pass them on connect for proper-noun /
      jargon boosting; not available on the REST endpoint.

      - **`format`/`punctuate`/`capitalize`** are accepted at the wire level
      today. They currently return the same transcript regardless of value —
      pass them in your integration so it works as the behavior changes.

      - **PII/PCI redaction (`redact_pii`, `redact_pci`)** runs server-side on
      finalized transcripts only — partials may show the unredacted text briefly
      before being replaced.

      - **JavaScript / TypeScript**: the official `smallestai` npm package
      predates the Pulse model, so connect with the `ws` library directly as
      shown above.
    bindings:
      ws:
        headers:
          type: object
          properties:
            Authorization:
              type: string
            language:
              $ref: '#/components/schemas/pulseStream_language'
              default: multi-eu
            encoding:
              $ref: '#/components/schemas/pulseStream_encoding'
              default: linear16
            sample_rate:
              $ref: '#/components/schemas/pulseStream_sample_rate'
              default: '16000'
            word_timestamps:
              $ref: '#/components/schemas/pulseStream_word_timestamps'
              default: 'true'
            sentence_timestamps:
              $ref: '#/components/schemas/pulseStream_sentence_timestamps'
              default: 'false'
            redact_pii:
              $ref: '#/components/schemas/pulseStream_redact_pii'
              default: 'false'
            redact_pci:
              $ref: '#/components/schemas/pulseStream_redact_pci'
              default: 'false'
            numerals:
              $ref: '#/components/schemas/pulseStream_numerals'
              default: auto
            format:
              $ref: '#/components/schemas/pulseStream_format'
              default: 'true'
            punctuate:
              $ref: '#/components/schemas/pulseStream_punctuate'
              default: 'true'
            capitalize:
              $ref: '#/components/schemas/pulseStream_capitalize'
              default: 'true'
            eou_timeout_ms:
              type: string
              default: 800
            diarize:
              $ref: '#/components/schemas/pulseStream_diarize'
              default: 'false'
            keywords:
              type: string
            itn_normalize:
              $ref: '#/components/schemas/pulseStream_itn_normalize'
              default: 'false'
            finalize_on_words:
              $ref: '#/components/schemas/pulseStream_finalize_on_words'
              default: 'true'
            max_words:
              type: integer
    publish:
      operationId: speech-to-text-publish
      summary: receiveTranscription
      description: Get real-time transcription results as audio is processed
      message:
        name: receiveTranscription
        title: receiveTranscription
        description: Get real-time transcription results as audio is processed
        payload:
          $ref: '#/components/schemas/pulseStream_pulseTranscriptionResponse.message'
    subscribe:
      operationId: speech-to-text-subscribe
      summary: Client messages
      message:
        oneOf:
          - $ref: >-
              #/components/messages/subpackage_speechToText.Speech to
              Text-client-0-sendAudioData
          - $ref: >-
              #/components/messages/subpackage_speechToText.Speech to
              Text-client-1-sendFinalizeSignal
          - $ref: >-
              #/components/messages/subpackage_speechToText.Speech to
              Text-client-2-sendCloseStreamSignal
servers:
  Production:
    url: wss://api.smallest.ai/
    protocol: wss
components:
  messages:
    subpackage_speechToText.Speech to Text-client-0-sendAudioData:
      name: sendAudioData
      title: sendAudioData
      description: Stream audio data in chunks for real-time transcription
      payload:
        $ref: '#/components/schemas/pulseStream_pulseAudioData.message'
    subpackage_speechToText.Speech to Text-client-1-sendFinalizeSignal:
      name: sendFinalizeSignal
      title: sendFinalizeSignal
      description: >-
        Force an immediate is_final transcript for pending speech without ending
        the session. Useful in agentic pipelines.
      payload:
        $ref: '#/components/schemas/pulseStream_pulseFinalizeSignal.message'
    subpackage_speechToText.Speech to Text-client-2-sendCloseStreamSignal:
      name: sendCloseStreamSignal
      title: sendCloseStreamSignal
      description: >-
        Signal that audio streaming is complete. The server flushes remaining
        audio, delivers final transcripts, and responds with is_last=true.
      payload:
        $ref: '#/components/schemas/pulseStream_pulseCloseStreamSignal.message'
  schemas:
    pulseStream_language:
      type: string
      enum:
        - it
        - es
        - en
        - pt
        - hi
        - de
        - fr
        - uk
        - ru
        - kn
        - ml
        - pl
        - mr
        - gu
        - cs
        - sk
        - te
        - or
        - nl
        - bn
        - lv
        - et
        - ro
        - pa
        - fi
        - sv
        - bg
        - ta
        - hu
        - da
        - lt
        - mt
        - multi
        - multi-eu
      default: multi-eu
      description: |
        Language code for transcription. Set explicitly to the known
        language for best accuracy.

        Use `multi-eu` for unknown European-language audio (auto-detects
        across the European set: de, en, fr, it, nl, pt, ru, es). Use
        `multi` for full multilingual auto-detection across all supported
        languages.

        Omitting `language` routes to `multi-eu`, which can mis-detect on
        non-European audio (e.g., returning Russian for English input).
        Always pass `language` explicitly when the source language is known.
      title: pulseStream_language
    pulseStream_encoding:
      type: string
      enum:
        - linear16
        - linear32
        - alaw
        - mulaw
        - opus
        - ogg_opus
      default: linear16
      description: |
        Audio encoding of the bytes you stream over the socket. The
        server uses this to decode incoming frames — set it to match
        what your client is sending.

        - `linear16`, `linear32` — raw PCM (16-bit and 32-bit). Pair
          with the appropriate `sample_rate`.
        - `alaw`, `mulaw` — 8 kHz telephony codecs. Pair with
          `sample_rate=8000`.
        - `opus`, `ogg_opus` — Opus compressed audio (raw and Ogg
          container).

        Streaming-only — the pre-recorded REST endpoint
        (`POST /pulse/get_text`) auto-detects the format from the
        file's container header and ignores this parameter.
      title: pulseStream_encoding
    pulseStream_sample_rate:
      type: string
      enum:
        - '8000'
        - '16000'
        - '22050'
        - '24000'
        - '44100'
        - '48000'
      default: '16000'
      description: |
        Audio sample rate in Hz of the bytes you stream. Must match
        the actual rate of your audio source. Streaming-only — the
        pre-recorded REST endpoint reads the rate from the file's
        container.
      title: pulseStream_sample_rate
    pulseStream_word_timestamps:
      type: string
      enum:
        - 'true'
        - 'false'
      default: 'true'
      description: Include word-level timestamps in transcription
      title: pulseStream_word_timestamps
    pulseStream_sentence_timestamps:
      type: string
      enum:
        - 'true'
        - 'false'
      default: 'false'
      description: Include sentence-level timestamps (utterances) in transcription
      title: pulseStream_sentence_timestamps
    pulseStream_redact_pii:
      type: string
      enum:
        - 'true'
        - 'false'
      default: 'false'
      description: Redact personally identifiable information (name, surname, address, etc)
      title: pulseStream_redact_pii
    pulseStream_redact_pci:
      type: string
      enum:
        - 'true'
        - 'false'
      default: 'false'
      description: >-
        Redact payment card information (credit card, CVV, zip, account number,
        etc)
      title: pulseStream_redact_pci
    pulseStream_numerals:
      type: string
      enum:
        - 'true'
        - 'false'
        - auto
      default: auto
      description: >
        Convert spoken numerals into digit form (e.g., 'twenty five' to '25').
        `auto` enables automatic detection based on context.

        For new integrations we recommend `itn_normalize=true` instead — it
        covers digits as well as dates, currencies, phone numbers, and other
        spoken-form entities, and gives more consistent results across
        languages.
      title: pulseStream_numerals
    pulseStream_format:
      type: string
      enum:
        - 'true'
        - 'false'
      default: 'true'
      description: |
        Master formatting switch for transcript responses. When `false`,
        forces `punctuate=false`, `capitalize=false`, and also disables
        Inverse Text Normalization (ITN) so it cannot silently reintroduce
        punctuation or casing.

        When `true`, the `punctuate` and `capitalize` params take effect
        independently. Leave `format=true` and use those two to fine-tune.
      title: pulseStream_format
    pulseStream_punctuate:
      type: string
      enum:
        - 'true'
        - 'false'
      default: 'true'
      description: |
        When `false`, strips end-of-sentence punctuation (`.`, `,`, `?`, `!`)
        from the transcript, `words[].word`, and `utterances[].transcript`.
        Does not affect casing — use `capitalize` for that. Overridden to
        `false` when `format=false`.
      title: pulseStream_punctuate
    pulseStream_capitalize:
      type: string
      enum:
        - 'true'
        - 'false'
      default: 'true'
      description: |
        When `false`, lowercases the entire transcript output (final
        transcript, `words[].word`, and `utterances[].transcript`). Does
        not affect punctuation — use `punctuate` for that. Overridden to
        `false` when `format=false`.
      title: pulseStream_capitalize
    pulseStream_diarize:
      type: string
      enum:
        - 'true'
        - 'false'
      default: 'false'
      description: Enable speaker diarization to identify different speakers in the audio
      title: pulseStream_diarize
    pulseStream_itn_normalize:
      type: string
      enum:
        - 'true'
        - 'false'
      default: 'false'
      description: >-
        Enable Inverse Text Normalization to convert spoken-form entities
        (numbers, dates, currencies, phone numbers, etc.) into written form in
        finalized transcripts.
      title: pulseStream_itn_normalize
    pulseStream_finalize_on_words:
      type: string
      enum:
        - 'true'
        - 'false'
      default: 'true'
      description: >-
        When false, disables automatic word-count-based finalization. Use with
        itn_normalize for agentic pipelines where you control finalization via
        the finalize message.
      title: pulseStream_finalize_on_words
    ChannelsPulseStreamMessagesPulseTranscriptionResponseMessageWordsItems:
      type: object
      properties:
        word:
          type: string
          description: The transcribed word
        start:
          type: number
          format: double
          description: Start time in seconds
        end:
          type: number
          format: double
          description: End time in seconds
        confidence:
          type: number
          format: double
          description: Confidence score for the word (0.0 to 1.0)
        speaker:
          type: integer
          description: Speaker label (when diarization is enabled)
        speaker_confidence:
          type: number
          format: double
          description: Confidence score for the speaker assignment (0.0 to 1.0)
      title: ChannelsPulseStreamMessagesPulseTranscriptionResponseMessageWordsItems
    ChannelsPulseStreamMessagesPulseTranscriptionResponseMessageUtterancesItems:
      type: object
      properties:
        text:
          type: string
          description: The transcribed sentence
        start:
          type: number
          format: double
          description: Start time in seconds
        end:
          type: number
          format: double
          description: End time in seconds
        speaker:
          type: integer
          description: Speaker label (when diarization is enabled)
      title: >-
        ChannelsPulseStreamMessagesPulseTranscriptionResponseMessageUtterancesItems
    pulseStream_pulseTranscriptionResponse.message:
      type: object
      properties:
        session_id:
          type: string
          description: Unique identifier for the transcription session
        transcript:
          type: string
          description: Partial or complete transcription text for the current segment
        is_final:
          type: boolean
          default: false
          description: Indicates if this is the final transcription for the current segment
        is_last:
          type: boolean
          default: false
          description: Indicates if this is the last transcription in the session
        from_finalize:
          type: boolean
          default: false
          description: >-
            True when this final transcript was triggered by a manual finalize
            message rather than automatic finalization
        words:
          type: array
          items:
            $ref: >-
              #/components/schemas/ChannelsPulseStreamMessagesPulseTranscriptionResponseMessageWordsItems
          description: Word-level timestamps (when word_timestamps=true)
        utterances:
          type: array
          items:
            $ref: >-
              #/components/schemas/ChannelsPulseStreamMessagesPulseTranscriptionResponseMessageUtterancesItems
          description: Sentence-level timestamps (when sentence_timestamps=true)
        language:
          type: string
          description: Detected primary language code, only returned when `is_final=True`
        languages:
          type: array
          items:
            type: string
          description: >-
            List of codes of languages detected in the audio, only returned when
            `is_final=True`
        redacted_entities:
          type: array
          items:
            type: string
          description: >-
            List of redacted entity placeholders (when redact_pii or redact_pci
            is enabled)
      required:
        - session_id
      title: pulseStream_pulseTranscriptionResponse.message
    pulseStream_pulseAudioData.message:
      type: string
      format: binary
      description: >-
        Raw audio data chunk, transmitted in binary format using the selected
        encoding
      title: pulseStream_pulseAudioData.message
    ChannelsPulseStreamMessagesPulseFinalizeSignalMessageType:
      type: string
      enum:
        - finalize
      description: >-
        Flush current audio buffer and force an immediate is_final transcript.
        The session remains open for more audio.
      title: ChannelsPulseStreamMessagesPulseFinalizeSignalMessageType
    pulseStream_pulseFinalizeSignal.message:
      type: object
      properties:
        type:
          $ref: >-
            #/components/schemas/ChannelsPulseStreamMessagesPulseFinalizeSignalMessageType
          description: >-
            Flush current audio buffer and force an immediate is_final
            transcript. The session remains open for more audio.
      required:
        - type
      title: pulseStream_pulseFinalizeSignal.message
    ChannelsPulseStreamMessagesPulseCloseStreamSignalMessageType:
      type: string
      enum:
        - close_stream
      description: >-
        Signal the end of the audio stream. The server flushes remaining audio,
        delivers final transcripts, and responds with is_last=true.
      title: ChannelsPulseStreamMessagesPulseCloseStreamSignalMessageType
    pulseStream_pulseCloseStreamSignal.message:
      type: object
      properties:
        type:
          $ref: >-
            #/components/schemas/ChannelsPulseStreamMessagesPulseCloseStreamSignalMessageType
          description: >-
            Signal the end of the audio stream. The server flushes remaining
            audio, delivers final transcripts, and responds with is_last=true.
      required:
        - type
      title: pulseStream_pulseCloseStreamSignal.message

```
