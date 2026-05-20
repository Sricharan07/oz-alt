# text_chunks

**Kind:** function
**Signature:** `from smallestai.waves import WavesStreamingTTS, TTSConfig`
**Source:** https://docs.smallest.ai/waves/api-reference/api-reference/text-to-speech/text-to-speech-v-3-1

## Example

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
