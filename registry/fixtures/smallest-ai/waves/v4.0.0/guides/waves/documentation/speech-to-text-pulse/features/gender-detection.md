> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Gender detection

> Predict speaker gender alongside every transcription

Pre-Recorded## Enabling gender detectionAppend `gender_detection=true` to your Pulse STT query string.### Sample request```bash
# Download sample audio (or use your own file)
curl -sL -o audio.wav "https://github.com/smallest-inc/cookbook/raw/main/speech-to-text/getting-started/samples/audio.wav"

curl --request POST \
  --url "https://api.smallest.ai/waves/v1/pulse/get_text?language=en&gender_detection=true" \
  --header "Authorization: Bearer $SMALLEST_API_KEY" \
  --header "Content-Type: audio/wav" \
  --data-binary "@audio.wav"
```Gender detection is currently supported only for Pre-Recorded API. Real-Time API support is coming soon.## Output format & field of interestResponses include a top-level `gender` (`male`, `female`) field that describes the dominant speaker in the processed segment. Store this field next to each transcript to power demographic analytics or routing logic.### Sample response```json
{
  "status": "success",
  "transcription": "Hello world.",
  "gender": "male"
}
```
