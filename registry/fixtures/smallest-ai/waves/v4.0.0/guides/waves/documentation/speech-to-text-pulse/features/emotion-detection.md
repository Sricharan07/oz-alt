> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Emotion detection

> Capture per-emotion confidence scores from Pulse STT responses

Pre-Recorded## Enabling emotion detectionInclude `emotion_detection=true` in your Pulse STT query parameters.### Sample request```bash
# Download sample audio (or use your own file)
curl -sL -o audio.wav "https://github.com/smallest-inc/cookbook/raw/main/speech-to-text/getting-started/samples/audio.wav"

curl --request POST \
  --url "https://api.smallest.ai/waves/v1/pulse/get_text?language=en&emotion_detection=true" \
  --header "Authorization: Bearer $SMALLEST_API_KEY" \
  --header "Content-Type: audio/wav" \
  --data-binary "@audio.wav"
```Emotion detection is currently supported only for Pre-Recorded API. Real-Time API support is coming soon.## Output format & field of interestThe response adds an `emotions` object containing floating-point scores (0–1) for happiness, sadness, disgust, fear, and anger. Use these fields to monitor sentiment, trigger QA alerts, or enrich customer analytics.### Sample response```json
{
  "transcription": "Hello world.",
  "emotions": {
    "happiness": 0.80,
    "sadness": 0.15,
    "disgust": 0.02,
    "fear": 0.03,
    "anger": 0.05
  }
}
```
