# get_cache_key

**Kind:** function
**Signature:** `import hashlib`
**Source:** https://docs.smallest.ai/waves/self-host/api-reference/endpoints/transcription

## Example

```python
import hashlib

def get_cache_key(audio_url):
    return hashlib.md5(audio_url.encode()).hexdigest()

cache_key = get_cache_key(audio_url)
if cache_key in cache:
    return cache[cache_key]

result = transcribe(audio_url)
cache[cache_key] = result
return result
```
