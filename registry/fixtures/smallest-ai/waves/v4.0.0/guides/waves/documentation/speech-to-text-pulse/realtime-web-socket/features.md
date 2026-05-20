> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Features

> Available features for Real-Time Pulse STT WebSocket API

The Real-Time Pulse STT WebSocket API supports the following features:

## Available Features

Get precise timing information for each word in the transcription with confidence scores

Automatically detect the language of the audio

Get sentence-level transcription segments with timing information

Automatically redact personally identifiable information and payment card information

Control how numbers are formatted in transcriptions (digits, words, or auto-detect)

Identify and label different speakers in the audio with speaker confidence scores

Boost recognition accuracy for specific words, brand names, and domain terms

Control punctuation and capitalization formatting in transcripts

Control how long Pulse waits after speech ends before finalizing the transcript

Convert spoken-form numbers, dates, and currencies into written form

Take manual control of when transcripts are finalized using `finalize_on_words` and `max_words`
