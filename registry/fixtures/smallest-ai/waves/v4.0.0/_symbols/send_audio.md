# send_audio

**Kind:** function
**Signature:** `import asyncio, json, websockets, pyaudio`
**Source:** https://docs.smallest.ai/waves/api-reference/api-reference/speech-to-text/speech-to-text

## Example

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
