> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Instant Voice Clone (Python SDK)

> Clone a voice from a short audio sample using the Python SDK.

Create an instant voice clone by uploading a short audio sample (5-15 seconds) via the Python SDK.

You can access the source code for the Python SDK on our [GitHub repository](https://github.com/smallest-inc/smallest-python-sdk).

The `smallestai` Python SDK is being updated. If the SDK example below doesn't work, use the [Instant Voice Clone (REST API)](/waves/documentation/voice-cloning/instant-clone-api) page — same operation, no SDK required. Streaming synthesis via `WavesStreamingTTS` is unaffected.

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

## Add your Voice

The Smallest AI SDK allows you to clone your voice by uploading an audio file. This feature is available both synchronously and asynchronously, making it flexible for different use cases. Below are examples of how to use this functionality.

### Synchronously

```python python
from smallestai.waves import WavesClient

def main():
    client = WavesClient(api_key="YOUR_API_KEY")
    res = client.add_voice(display_name="My Voice", file_path="my_voice.wav")
    print(res)

if __name__ == "__main__":
    main()
```

### Asynchronously

```python python
import asyncio
from smallestai.waves import AsyncWavesClient

async def main():
    client = AsyncWavesClient(api_key="YOUR_API_KEY")
    res = await client.add_voice(display_name="My Voice", file_path="my_voice.wav")
    print(res)

if __name__ == "__main__":
    asyncio.run(main())
```

## Parameters

* `api_key`: Your API key (can be set via SMALLEST\_API\_KEY environment variable).
* `display_name`: Name of the voice to be created.
* `file_path`: Path to the audio file to be cloned.

These parameters are part of the add\_voice function. They can be set when calling the function as shown above.

## Get All Cloned Voices

Once you have cloned your voices, you can retrieve a list of all cloned voices associated with your account using the following code:

```python python
from smallestai.waves import WavesClient

client = WavesClient(api_key="YOUR_API_KEY")
print(f"Available Voices: {client.get_cloned_voices()}")
```

If you have any questions or run into any issues, our community is here to help!

* Join our [Discord server](https://discord.gg/9WtSXv26WE) to connect with other developers and get real-time support.
* Reach out to our team via email: [support@smallest.ai](mailto:support@smallest.ai).
