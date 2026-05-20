> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Punctuation Formatting

> Control punctuation and capitalization formatting in real-time transcripts

Real-TimePunctuation formatting controls whether transcript text is returned with punctuation and capitalization applied, or as raw lowercase text. This is enabled by default.## Enabling Punctuation FormattingPunctuation Formatting is currently only available for the Real-Time WebSocket API.Add the `format` parameter to your WebSocket connection query parameters. Options: `true` (default), `false`.### Real-Time WebSocket API```javascript
const url = new URL("wss://api.smallest.ai/waves/v1/pulse/get_text");
url.searchParams.append("language", "en");
url.searchParams.append("encoding", "linear16");
url.searchParams.append("sample_rate", "16000");
url.searchParams.append("format", "false"); // disable formatting

const ws = new WebSocket(url.toString(), {
  headers: {
    Authorization: `Bearer ${API_KEY}`,
  },
});
```## Example Output### With `format=true` (default)```json
{
  "transcript": "Hello there, how can I help you today?",
  "is_final": true
}
```### With `format=false````json
{
  "transcript": "hello there how can i help you today",
  "is_final": true
}
```## When to Use| Use case                           | Recommended setting                                          |
| ---------------------------------- | ------------------------------------------------------------ |
| Live captions and subtitles        | `format=true` - human-readable output                        |
| Meeting transcription              | `format=true` - properly formatted text                      |
| Feeding into LLMs or NLP pipelines | `format=false` - raw text avoids double-formatting           |
| Search indexing                    | `format=false` - normalized text for consistent matching     |
| Custom post-processing             | `format=false` - apply your own punctuation and casing rules |
