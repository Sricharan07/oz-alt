> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Models

> Find detailed description of each model along with their capabilities and supported languages.

## Text to Speech (TTS) ModelsLatest Release A 44 kHz model delivering natural, expressive, and realistic speech. Supports voice cloning with ultra-low latency. 12 languages plus `auto`-detect with mid-sentence code-switching.**Lightning v2 is deprecated.** New integrations should use Lightning v3.1. The v2 endpoints remain available for existing callers but are not recommended for new work.## Speech to Text (STT) ModelsLow-latency speech recognition for real-time and pre-recorded transcription.
Automatic language detection across 38 languages. Click on a model name to view its detailed model card. ## Geo-location Based RoutingWaves intelligently routes every request to the nearest server cluster to ensure the lowest possible latency for your applications. We currently operate server clusters in:- India (Mumbai)
- USA (Oregon)Our routing system automatically detects the client's geographical location and connects them to the optimal server based on network proximity and latency. This process is fully automated, no manual configuration is required on your side.## Model Overview (TTS)| Model ID                                                                       | Description                                                                         | Languages Supported                                                                                                                                                                                           |
| ------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [**lightning-v3.1**](/waves/model-cards/text-to-speech/lightning-v-3-1) Latest | 44 kHz model, natural expressive speech, ultra-low latency, supports voice cloning. | `English`
 `Hindi`
 `Marathi`
 `Kannada`
 `Tamil`
 `Bengali`
 `Gujarati`
 `Telugu`
 `Malayalam`
 `Punjabi`
 `Odia`
 `Spanish`
 `auto` |## Model Overview (STT)| Model ID  | Description                                                                                           | Languages Supported                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| --------- | ----------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **pulse** | Low-latency speech-to-text model supporting automatic language detection and real-time transcription. | `Italian`
 `Spanish`
 `English`
 `Portuguese`
 `Hindi`
 `German`
 `French`
 `Ukrainian`
 `Russian`
 `Kannada`
 `Malayalam`
 `Polish`
 `Marathi`
 `Gujarati`
 `Czech`
 `Slovak`
 `Telugu`
 `Oriya (Odia)`
 `Dutch`
 `Bengali`
 `Latvian`
 `Estonian`
 `Romanian`
 `Punjabi`
 `Finnish`
 `Swedish`
 `Bulgarian`
 `Tamil`
 `Hungarian`
 `Danish`
 `Lithuanian`
 `Maltese`
 `Japanese`
 `Korean`
 `Chinese`
 `Malay`
 `Indonesian`
 `Tagalog` |Note: The API uses [ISO 639-1 language codes - Set
1](https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes) (2-letter
codes) to specify supported languages.## PricingOur pricing model is designed to be flexible and scalable, catering to different usage needs. For detailed pricing information, please visit our [pricing page](https://smallest.ai/text-to-speech) or contact our sales team at [support@smallest.ai](mailto:support@smallest.ai).
