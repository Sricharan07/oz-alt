# preprocess_audio

**Kind:** function
**Signature:** `import os`
**Source:** https://docs.smallest.ai/waves/documentation/speech-to-text-pulse/pre-recorded/code-examples

## Example

```python
import os
from pydub import AudioSegment
from smallestai.waves import WavesClient

client = WavesClient(api_key=os.getenv("SMALLEST_API_KEY"))

def preprocess_audio(input_path, output_path):
    """
    Preprocess audio file to optimal format for Pulse STT:
    - Convert to 16 kHz mono WAV
    - Normalize audio levels
    - Remove leading/trailing silence
    """
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_frame_rate(16000).set_channels(1)
    audio = audio.normalize()
    audio = audio.strip_silence(silence_len=100, silence_thresh=-40)
    audio.export(output_path, format="wav")
    print(f"Preprocessed audio saved to: {output_path}")
    return output_path

def transcribe_with_features(audio_path):
    """
    Transcribe audio with gender detection, emotion detection, and utterances.
    """
    response = client.transcribe(
        file_path=audio_path,
        model="pulse",
        language="en",
        word_timestamps=True,
        gender_detection=True,
        emotion_detection=True,
        diarize=True
    )

    return response

def process_results(response):
    """
    Extract and display transcription results.
    """
    print("=" * 60)
    print("TRANSCRIPTION RESULTS")
    print("=" * 60)

    print(f"\nTranscription: {response.get('transcription', 'N/A')}")

    if 'gender' in response:
        print(f"\nGender: {response['gender']}")

    if 'emotions' in response:
        print("\nEmotion Scores:")
        emotions = response['emotions']
        for emotion, score in emotions.items():
            print(f"  {emotion.capitalize()}: {score:.2f}")

    if 'utterances' in response:
        print("\nUtterances (Sentence-level timestamps):")
        for i, utterance in enumerate(response['utterances'], 1):
            speaker = utterance.get('speaker', 'unknown')
            start = utterance.get('start', 0)
            end = utterance.get('end', 0)
            text = utterance.get('text', '')
            print(f"\n  [{i}] Speaker: {speaker}")
            print(f"      Time: {start:.2f}s - {end:.2f}s")
            print(f"      Text: {text}")

    if 'words' in response:
        print(f"\nWord-level timestamps: {len(response['words'])} words")

if __name__ == "__main__":
    input_audio = "input_audio.mp3"
    preprocessed_audio = "preprocessed_audio.wav"

    try:
        print("Preprocessing audio...")
        preprocess_audio(input_audio, preprocessed_audio)

        print("\nTranscribing audio with gender, emotion, and utterance detection...")
        result = transcribe_with_features(preprocessed_audio)

        process_results(result)

        if os.path.exists(preprocessed_audio):
            os.remove(preprocessed_audio)
            print("\nCleaned up temporary preprocessed file.")

    except FileNotFoundError:
        print(f"Error: Audio file '{input_audio}' not found.")
    except Exception as e:
        print(f"Error: {str(e)}")
```
