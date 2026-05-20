> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Overview

> Pulse STT API — transcribe audio in real-time or from files with 38 language support, diarization, and emotion detection.

The Pulse STT API transcribes audio via `https://api.smallest.ai/waves/v1/pulse/get_text`. Pre-recorded and real-time (WebSocket) modes, 38 languages with auto-detection, speaker diarization, word timestamps, and emotion detection.

Get started in minutes. Learn how to get your API key and transcribe your first audio file.

## Transcription Modes

We offer two transcription modes to cover a wide range of use cases. Choose the one that best fits your needs:

Transcribe audio files using synchronous HTTPS POST requests. Perfect for batch processing, archived media, and offline transcription workflows.

Stream audio and receive transcription results as the audio is processed. Ideal for live conversations, voice assistants, and low-latency applications.

## Feature highlights

Our models specialize in processing audio to preserve information that is often lost during conventional speech to text conversion.

Support for 38 languages with automatic language detection or ISO 639-1 codes (`en`, `hi`, etc.). Use `language=multi` to enable automatic language detection across all supported languages.

Get precise timing information for each word in the transcription. Enables caption generation, subtitle tracks, and time-based search within audio content.

Receive sentence-level transcription segments with timing information. Perfect for displaying readable captions, synchronizing larger chunks of audio, or storing structured call summaries.

Identify and separate generated text into speaker turns. Automatically label different speakers in multi-speaker audio, enabling speaker-attributed transcription.

Detect the gender of each speaker alongside transcription. Provides demographic insights for analytics and content analysis.

Detect emotional tone in transcribed speech with strength indicators for 5 core emotion types. Analyze sentiment and emotional context in conversations.

Automatically redact personally identifiable information (names, addresses, phone numbers) and payment card information (credit cards, CVV, account numbers) to protect privacy and ensure compliance.

Streaming pipeline tuned for \~64 ms time to first transcript latency. Optimized for real-time transcription with minimal delay.

## Supported languages

        Language

        Code

        Pre-Recorded

        Real-Time

        Italian

        it

        Yes

        Yes

        Spanish

        es

        Yes

        Yes

        English

        en

        Yes

        Yes

        Portuguese

        pt

        Yes

        Yes

        Hindi

        hi

        Yes

        Yes

        German

        de

        Yes

        Yes

        French

        fr

        Yes

        Yes

        Ukrainian

        uk

        Yes

        Yes

        Russian

        ru

        Yes

        Yes

        Kannada

        kn

        Yes

        Yes

        Malayalam

        ml

        Yes

        Yes

        Polish

        pl

        Yes

        Yes

        Marathi

        mr

        Yes

        Yes

        Gujarati

        gu

        Yes

        Yes

        Czech

        cs

        Yes

        Yes

        Slovak

        sk

        Yes

        Yes

        Telugu

        te

        Yes

        Yes

        Oriya (Odia)

        or

        Yes

        Yes

        Dutch

        nl

        Yes

        Yes

        Bengali

        bn

        Yes

        Yes

        Latvian

        lv

        Yes

        Yes

        Estonian

        et

        Yes

        Yes

        Romanian

        ro

        Yes

        Yes

        Punjabi

        pa

        Yes

        Yes

        Finnish

        fi

        Yes

        Yes

        Swedish

        sv

        Yes

        Yes

        Bulgarian

        bg

        Yes

        Yes

        Tamil

        ta

        Yes

        Yes

        Hungarian

        hu

        Yes

        Yes

        Danish

        da

        Yes

        Yes

        Lithuanian

        lt

        Yes

        Yes

        Maltese

        mt

        Yes

        Yes

Use `language=multi` to auto-detect across the full list or specify one of the codes above to pin the model to a single language.

## Next steps

* Send your first POST request in the [Pulse STT Pre-Recorded quickstart](/waves/documentation/speech-to-text-pulse/pre-recorded/quickstart).
* Start your first WebSocket connection in the [Pulse STT WebSocket quickstart](/waves/documentation/speech-to-text-pulse/realtime-web-socket/quickstart).
* Review [best practices](/waves/documentation/speech-to-text-pulse/pre-recorded/best-practices) for audio preprocessing and request hygiene.
* Use the [troubleshooting guide](/waves/documentation/speech-to-text-pulse/pre-recorded/troubleshooting) when you need quick fixes.
