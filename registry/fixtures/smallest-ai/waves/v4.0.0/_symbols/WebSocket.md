# WebSocket

**Kind:** expected
**Signature:** `WebSocket`
**Source:** https://docs.smallest.ai/waves/llms-full.txt

## Example

```markdown
output_format: "wav",
    }),
  }
);

const buffer = Buffer.from(await response.arrayBuffer());
fs.writeFileSync("output.wav", buffer);
console.log(`Saved output.wav (${buffer.length} bytes)`);
```The `smallestai` Python SDK's synchronous `WavesClient.synthesize()` is being updated. Use the `requests` example above until the next SDK release.**Full runnable source files:** [Python](https://github.com/smallest-inc/cookbook/blob/main/text-to-speech/quickstart-python.py) | [JavaScript](https://github.com/smallest-inc/cookbook/blob/main/text-to-speech/quickstart-javascript.js) | [cURL](https://github.com/smallest-inc/cookbook/blob/main/text-to-speech/quickstart-curl.sh)## Step 4: Explore MoreBrowse 217 voices across 12 languages — English, Hindi, Spanish, and 9 Indian languages.Real-time audio streaming via WebSocket for voice assistants.Clone any voice from just 5-15 seconds of audio.Custom pronunciations for brand names and technical terms.## Key Parameters| Parameter       | Type   | Default    | Description                                      |
| --------------- | ------ | ---------- | ------------------------------------------------ |
| `text`          | string | *required* | Text to synthesize (max \~250 chars recommended) |
| `voice_id`      | string | *required* | Voice to use (e.g., `magnus`, `olivia`)          |
| `sample_rate`   | int    | `44100`    | `8000`, `16000`, `24000`, or `44100` Hz          |
| `speed`         | float  | `1.0`      | Speech rate: `0.5` to `2.0`                      |
| `language`      | string | `auto`     | `en`, `hi`, `es`, `ta`, or `auto`                |
| `output_format` | string | `pcm`      | `pcm`, `wav`, `mp3`, `ulaw`, or `alaw`           |## Need Help?Ask questions, share what you're building, and connect with other developers on Discord.If you need direct assistance, reach out at [support@smallest.ai](mailto:support@smallest.ai).
```
