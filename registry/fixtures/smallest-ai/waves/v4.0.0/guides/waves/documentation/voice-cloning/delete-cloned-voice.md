> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Delete a Voice Clone

> Remove a cloned voice using the Python SDK.

Delete a previously created voice clone via the Python SDK.

You can access the source code for the Python SDK on our [GitHub repository](https://github.com/smallest-inc/smallest-python-sdk).

The `smallestai` Python SDK is being updated. If the SDK example below doesn't work, call the underlying delete-voice REST endpoint directly (see the API reference under Waves → API Reference). Streaming synthesis via `WavesStreamingTTS` is unaffected.

## Requirements

Before you begin, ensure you have the following:

* Python (3.9 or higher) installed on your machine.
* An API key from the Smallest AI [platform](https://app.smallest.ai/dashboard/api-keys?utm_source=documentation\&utm_medium=voice-cloning).

## Setup

### Install our SDK

```bash
pip install smallestai
```

Set your API key as an environment variable.

```bash
export SMALLEST_API_KEY=YOUR_API_KEY
```

## Delete your Voice

The Smallest AI SDK allows you to delete your cloned voice. This feature is available both synchronously and asynchronously, making it flexible for different use cases. Below are examples of how to use this functionality.

### Synchronously

```python python
from smallestai.waves import WavesClient

def main():
    client = WavesClient(api_key="SMALLEST_API_KEY")
    res = client.delete_voice(voice_id="voice_id")
    print(res)

if __name__ == "__main__":
    main()
```

### Asynchronously

```python python
import asyncio
from smallestai.waves import AsyncWavesClient

async def main():
    client = AsyncWavesClient(api_key="SMALLEST_API_KEY")
    res = await client.delete_voice(voice_id="voice_id")
    print(res)

if __name__ == "__main__":
    asyncio.run(main())
```

## Parameters

* `api_key`: Your API key (can be set via SMALLEST\_API\_KEY environment variable).
* `voice_id`: Unique Voice ID of the voice to be deleted.

If you have any questions or run into any issues, our community is here to help!

* Join our [Discord server](https://discord.gg/9WtSXv26WE) to connect with other developers and get real-time support.
* Reach out to our team via email: [support@smallest.ai](mailto:support@smallest.ai).
