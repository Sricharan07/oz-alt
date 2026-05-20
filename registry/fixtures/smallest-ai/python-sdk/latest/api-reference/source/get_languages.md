# get_languages

```python
def get_languages(self, model:str="lightning") -> List[str]:
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

    def synthesize(
            self,
            text: str,
            **kwargs
        ) -> Union[bytes]:
        """
        Synthesize speech from the provided text.

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
        """
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

        res = requests.post(f"{API_BASE_URL}/{opts.model}/get_speech", json=payload, headers=headers)
        if res.status_code != 200:
            raise APIError(f"Failed to synthesize speech: {res.text}. Please check if you have set the correct API key. For more information, visit https://waves.smallest.ai/")

        return res.content

    def add_voice(self, display_name: str, file_path: str) -> str:
        """
        Instantly clone your voice synchronously.

        Args:
        - display_name (str): The display name for the new voice.
        - file_path (str): The path to the reference audio file to be cloned.

        Returns:
        - str: The response from the API as a formatted JSON string.

        Raises:
        - InvalidError: If the file does not exist or is not a valid audio file.
        - APIError: If the API request fails or returns an error.
        """
        if not os.path.isfile(file_path):
```
