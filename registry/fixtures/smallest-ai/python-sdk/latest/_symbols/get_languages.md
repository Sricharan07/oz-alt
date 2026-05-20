# get_languages

**Kind:** function
**Signature:** `def _ensure_session(self):`
**Source:** https://raw.githubusercontent.com/smallest-inc/smallest-python-sdk/main/smallestai/waves/async_waves_client.py#ensure_session

## Example

```python
def _ensure_session(self):
        """Ensure session exists for direct calls"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            return True
        return False

    def get_languages(self, model="lightning") -> List[str]:
        """Returns a list of available languages."""
        return get_smallest_languages(model)

    def get_cloned_voices(self) -> str:
        """Returns a list of your cloned voices."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        res = requests.request("GET", f"{API_BASE_URL}/lightning-large/get_cloned_voices", headers=headers)
        if res.status_code != 200:
            raise APIError(f"Failed to get cloned voices: {res.text}. For more information, visit https://waves.smallest.ai/")

        return json.dumps(res.json(), indent=4, ensure_ascii=False)

    def get_voices(
            self,
            model: Optional[str] = "lightning"
        ) -> str:
        """Returns a list of available voices."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        res = requests.request("GET", f"{API_BASE_URL}/{model}/get_voices", headers=headers)
        if res.status_code != 200:
            raise APIError(f"Failed to get voices: {res.text}. For more information, visit https://waves.smallest.ai/")

        return json.dumps(res.json(), indent=4, ensure_ascii=False)

    def get_models(self) -> List[str]:
        """Returns a list of available models."""
        return get_smallest_models()

    async def synthesize(
            self,
            text: str,
            **kwargs
        ) -> Union[bytes]:
        """
        Asynchronously synthesize speech from the provided text.

        Args:
        - text (str): The text to be converted to speech.
        - stream (Optional[bool]): If True, returns an iterator yielding audio chunks instead of a full byte array.
        - kwargs: Additional optional parameters to override `__init__` options for this call.

        Returns:
        - Union[bytes, None, Iterator[bytes]]:
            - If `stream=True`, returns an iterator yielding audio chunks.
            - If `save_as` is provided, saves the file and returns None.
            - Otherwise, returns the synthesized audio content as bytes.

        Raises:
        - InvalidError: If the provided file name does not have a .wav or .mp3 extension when `save_as` is specified.
        - APIError: If the API request fails or returns an error.
        - ValueError: If an unexpected parameter is passed in `kwargs`.
        """
        should_cleanup = False

        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
            should_cleanup = True  # Cleanup only if we created a new session

        try:
            opts = copy.deepcopy(self.opts)
            valid_keys = set(vars(opts).keys())

            invalid_keys = [key for key in kwargs if key not in valid_keys]
            if invalid_keys:
                raise ValueError(f"Invalid parameter(s) in kwargs: {', '.join(invalid_keys)}. Allowed parameters are: {', '.join(valid_keys)}")

            for key, value in kwargs.items():
                setattr(opts, key, value)

            validate_input(text, opts.model, opts.sample_rate, opts.speed, opts.consistency, opts.similarity, opts.enhancement)

            payload = {
                "text": text,
                "voice_id": opts.voice_id,
                "sample_rate": opts.sample_rate,
                "speed": opts.speed,
                "consistency": opts.consistency,
                "similarity": opts.similarity,
                "enhancement": opts.enhancement,
                "language": opts.language,
                "output_format": opts.output_format
            }

            if opts.model == "lightning-large" or opts.model == "lightning-v2":
                if opts.consistency is not None:
                    payload["consistency"] = opts.consistency
                if opts.similarity is not None:
                    payload["similarity"] = opts.similarity
                if opts.enhancement is not None:
                    payload["enhancement"] = opts.enhancement

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            async with self.session.post(f"{API_BASE_URL}/{opts.model}/get_speech", json=payload, headers=headers) as res:
                if res.status != 200:
                    raise APIError(f"Failed to synthesize speech: {await res.text()}. For more information, visit https://waves.smallest.ai/")

                audio_bytes = await res.content.read()
```
