> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Word timestamps

> Return word-level timing metadata from Pulse STT

Pre-RecordedReal-TimeWord timestamps provide precise timing information for each word in the transcription, enabling you to generate captions, subtitles, and align transcripts with audio playback. Use these offsets to generate captions, subtitle tracks, or to align transcripts with downstream analytics.## Enabling Word Timestamps### Pre-Recorded APIAdd `word_timestamps=true` to your Pulse STT query parameters. This works for both raw-byte uploads (`Content-Type: audio/wav`) and JSON requests with hosted audio URLs.#### Sample request```bash
# Download sample audio (or use your own file)
curl -sL -o audio.wav "https://github.com/smallest-inc/cookbook/raw/main/speech-to-text/getting-started/samples/audio.wav"

curl --request POST \
  --url "https://api.smallest.ai/waves/v1/pulse/get_text?language=en&word_timestamps=true" \
  --header "Authorization: Bearer $SMALLEST_API_KEY" \
  --header "Content-Type: audio/wav" \
  --data-binary "@audio.wav"
```### Real-Time WebSocket APIAdd `word_timestamps=true` to your WebSocket connection query parameters when connecting to the Pulse STT WebSocket API.```javascript
const url = new URL("wss://api.smallest.ai/waves/v1/pulse/get_text");
url.searchParams.append("language", "en");
url.searchParams.append("encoding", "linear16");
url.searchParams.append("sample_rate", "16000");
url.searchParams.append("word_timestamps", "true");

const ws = new WebSocket(url.toString(), {
  headers: {
    Authorization: `Bearer ${API_KEY}`,
  },
});
```## Output format & field of interestResponses include a `words` array with `word`, `start`, `end`, and `confidence` fields. When diarization is enabled, the array also includes `speaker` (integer ID for realtime, string label for pre-recorded) and `speaker_confidence` (0.0 to 1.0, realtime only) fields.### Pre-Recorded API Response```json
{
  "status": "success",
  "transcription": "Hello world.",
  "words": [
    { "start": 0.0, "end": 0.5, "speaker": "speaker_0", "word": "Hello" },
    { "start": 0.6, "end": 0.9, "speaker": "speaker_0", "word": "world." }
  ],
  "utterances": [
    { "text": "Hello world.", "start": 0.0, "end": 0.9, "speaker": "speaker_0" }
  ]
}
```The response of Pre-Recorded API includes the utterances field, which includes sentence level timestamps.### Real-Time WebSocket API Response```json
{
  "type": "transcription",
  "status": "success",
  "session_id": "00000000-0000-0000-0000-000000000001",
  "transcript": "Hello, how are you?",
  "is_final": true,
  "is_last": false,
  "language": "en",
  "words": [
    {
      "word": "Hello",
      "start": 0.0,
      "end": 0.5,
      "confidence": 0.98
    },
    {
      "word": "how",
      "start": 0.6,
      "end": 0.8,
      "confidence": 0.95
    },
    {
      "word": "are",
      "start": 0.8,
      "end": 1.0,
      "confidence": 0.97
    },
    {
      "word": "you?",
      "start": 1.0,
      "end": 1.3,
      "confidence": 0.99
    }
  ]
}
```When `diarize=true` is enabled, the `words` array also includes `speaker` (integer ID) and `speaker_confidence` (0.0 to 1.0) fields.## Response Fields

        Field

        Type

        When Included

        Description

        `word`

        string

        `word_timestamps=true`

        The transcribed word

        `start`

        number

        `word_timestamps=true`

        Start time in seconds

        `end`

        number

        `word_timestamps=true`

        End time in seconds

        `confidence`

        number

        `word_timestamps=true`

         (realtime only)

        Confidence score for the word (0.0 to 1.0)

        `speaker`

        integer (realtime) / string (pre-recorded)

        `diarize=true`

        Speaker label. Real-time API uses integer IDs (0, 1, ...), pre-recorded API uses string labels (speaker_0, speaker_1, ...)

        `speaker_confidence`

        number

        `diarize=true`

         (realtime only)

        Confidence score for the speaker assignment (0.0 to 1.0)

## Use Cases- **Caption generation**: Create synchronized captions for video or live streams
- **Subtitle tracks**: Generate SRT or VTT subtitle files
- **Analytics**: Align transcripts with audio playback for detailed analysis
- **Search**: Enable time-based search within audio content
