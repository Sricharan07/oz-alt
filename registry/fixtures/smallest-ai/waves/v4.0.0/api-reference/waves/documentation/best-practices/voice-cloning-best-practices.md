> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Voice Cloning Best Practices

> Guidelines for recording reference audio and achieving high-quality voice clones.

High-quality reference audio is the single most important factor in clone quality. These guidelines cover recording environment, speaking style, multi-lingual cloning, and expressive control.

Clone a voice directly in the console. 5-15 seconds of audio, no code required.

## Recording Reference Audio

### Environment

* Record in a quiet room with minimal background noise. Ambient noise, hiss, or rumble will be captured in the clone.
* Use a dedicated microphone when possible. MacBook and mobile device microphones are acceptable if positioned at an appropriate distance to avoid distortion.
* Avoid rooms with echo (large empty spaces, outdoor areas). Small treated rooms produce the best results.
* After recording, listen back to the audio before uploading. Verify it is free of interruptions, clipping, or background interference.

### Speaking Style

* Speak naturally in your normal conversational voice. The model captures timbre, accent, emotional tone, rhythm, and pacing automatically.
* Maintain a consistent pace throughout the recording. Avoid long pauses, as they can degrade clone quality.
* Do not exaggerate emotion unless a specific tone is the intended output (see [Expressive Cloning](#expressive-cloning) below).

### Audio Length

* Provide **5 to 15 seconds** of clean, continuous speech.

## Multi-Lingual Voice Cloning

### Language Matching

For best results, record reference audio in the same language as your intended output. The model supports cross-lingual cloning (e.g., English reference audio used for Spanish output), but a language-matched reference will always produce higher fidelity.

| Scenario                                      | Expected Quality                                                               |
| --------------------------------------------- | ------------------------------------------------------------------------------ |
| Reference and output in the same language     | Best results. Highest phonetic accuracy.                                       |
| Reference in a different language than output | Functional. Voice characteristics transfer, but the source accent is retained. |

### Accent Retention

When synthesizing in a different language than the reference audio, the original accent is preserved. A clone from a South Indian English speaker will retain that accent when generating Hindi or Tamil output. This is by design: the clone reproduces *your* voice, including accent characteristics.

If accent-neutral output is required for a specific language, provide reference audio recorded by a native speaker of that language.

### Language Group Constraints

Cloned voices follow the same language group routing rules as standard synthesis. See [Code-Switching](/waves/model-cards/text-to-speech/lightning-v-3-1#code-switching) for details on Indic and Global group restrictions.

## Expressive Cloning

The model captures emotional and prosodic characteristics from the reference audio. The tone, pace, and volume of the reference directly influence the synthesized output.

### Emotional Control

The emotion conveyed in the reference audio (e.g., calm, happy, angry) is reflected in the generated speech. To produce an angry-sounding clone, provide an angry reference. To produce a neutral clone, provide a neutral reference.

### Speed Control

The pace of the reference audio determines the output speed. A fast-paced reference produces faster delivery; a slower reference produces more measured output.

### Volume Control

The volume level in the reference audio carries over to the output. A soft-spoken reference produces quieter output; a louder, more energetic recording produces bolder output.

## Reference Audio Examples

Audio samples are embedded as video due to platform constraints.

### Good Reference Audio

Clear, consistent tone with no background noise.

### Bad Reference Audio

**Background noise present.**

**Inconsistent speaking style.**

**Overlapping voices.**

## Expressive Audio Examples

### Angry Tone

**Reference:**

**Output:**

### Whisper Tone

**Reference:**

**Output:**

### Fast-Paced Tone

**Reference:**

**Output:**
