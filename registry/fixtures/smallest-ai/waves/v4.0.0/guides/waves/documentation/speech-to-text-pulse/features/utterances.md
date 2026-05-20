> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Sentence-level timestamps

> Use the utterances array to capture longer segments with speaker labels

Pre-RecordedReal-TimeSentence-level timestamps (utterances) are supported in both **Pre-Recorded** and **Real-Time** transcription APIs. The `utterances` array aggregates contiguous words into sentence-level segments, providing structured timing information for longer audio chunks.## Enabling sentence-level timestamps### Pre-Recorded APIFor the Pre-Recorded API, set `word_timestamps=true` in your query parameters. When word timestamps are enabled, the response includes both `words` and `utterances` arrays.**Required dependency:** `word_timestamps=true` must be enabled for utterances to appear in the response. Without it, the `utterances` array will be empty. For the Real-Time API, also set `sentence_timestamps=true`.```bash
# Download sample audio (or use your own file)
curl -sL -o audio.wav "https://github.com/smallest-inc/cookbook/raw/main/speech-to-text/getting-started/samples/audio.wav"

curl --request POST \
  --url "https://api.smallest.ai/waves/v1/pulse/get_text?language=en&word_timestamps=true&diarize=true" \
  --header "Authorization: Bearer $SMALLEST_API_KEY" \
  --header "Content-Type: audio/wav" \
  --data-binary "@audio.wav"
```### Real-Time API (WebSocket)For the Real-Time WebSocket API, set `sentence_timestamps=true` as a query parameter when establishing the WebSocket connection.```javascript
const url = new URL("wss://api.smallest.ai/waves/v1/pulse/get_text");
url.searchParams.append("language", "en");
url.searchParams.append("sentence_timestamps", "true");

const ws = new WebSocket(url.toString(), {
  headers: {
    Authorization: `Bearer ${API_KEY}`,
  },
});
```## Output formatEach `utterances` entry contains `text`, `start`, `end`, and optional `speaker` fields (when diarization is enabled). Use these sentence-level timestamps when you need to display readable captions, synchronize larger chunks of audio, or store structured call summaries.## Sample response### Pre-Recorded API```json
{
  "status": "success",
  "transcription": "Hello world. How are you?",
  "words": {...}
  "utterances": [
    { "text": "Hello world.", "start": 0.0, "end": 0.9, "speaker": "speaker_0" },
    { "text": "How are you?", "start": 1.0, "end": 2.1, "speaker": "speaker_1" }
  ]
}
```This response has the `speaker` field due to `diarize` being enabled in the query.### Real-Time API (WebSocket)```json
{
  "session_id": "sess_12345abcde",
  "transcript": "Hello world. How are you?",
  "is_final": true,
  "is_last": false,
  "language": "en",
  "utterances": [
    { "text": "Hello world.", "start": 0.0, "end": 0.9 },
    { "text": "How are you?", "start": 1.0, "end": 2.1 }
  ]
}
```When `diarize=true` is enabled, the `utterances` array also includes a `speaker` field (integer ID) for real-time API responses. For example: `{ "text": "Hello world.", "start": 0.0, "end": 0.9, "speaker": 0 }`
