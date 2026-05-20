# _build_params

**Kind:** function
**Signature:** `class OpenAIClient(BaseLLMClient):`
**Source:** https://raw.githubusercontent.com/smallest-inc/smallest-python-sdk/main/smallestai/atoms/agent/clients/openai.py#openaiclient

## Example

```python
class OpenAIClient(BaseLLMClient):
    """
    Standalone OpenAI client for use in any node.

    Example:
        client = OpenAIClient(model="gpt-4o-mini")
        response = await client.chat(messages=[...])

        # Streaming
        async for chunk in client.chat(messages=[...], stream=True):
            print(chunk.content)

        # With tools
        response = await client.chat(
            messages=[...],
            tools=[{
                "type": "function",
                "function": {...}
            }]
        )
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: NotGivenOr[float] = NOT_GIVEN,
        max_tokens: NotGivenOr[int] = NOT_GIVEN,
        **kwargs: Any,
    ):
        """
        Initialize OpenAI client.

        Args:
            model: Model name (e.g., "gpt-4o-mini", "gpt-4")
            api_key: API key (or None to use OPENAI_API_KEY env var)
            base_url: Custom base URL for OpenAI-compatible APIs
            temperature: Default sampling temperature
            max_tokens: Default max completion tokens
            **kwargs: Additional default parameters
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._extra_kwargs = kwargs
        self._client = self._create_client(api_key, base_url)

    def _create_client(
        self, api_key: Optional[str], base_url: Optional[str]
    ) -> AsyncOpenAI:
        """Create the OpenAI async client."""
        # Get API key from parameter or environment
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning(
                "No OpenAI API key provided. "
                "Set OPENAI_API_KEY environment variable or pass api_key parameter."
            )

        # Create httpx client with connection pooling
        http_client = httpx.AsyncClient(
            limits=httpx.Limits(
                max_keepalive_connections=100,
                max_connections=1000,
            )
        )

        # Create OpenAI client
        client_kwargs: Dict[str, Any] = {
            "api_key": api_key,
            "http_client": http_client,
        }

        if base_url:
            client_kwargs["base_url"] = base_url

        return AsyncOpenAI(**client_kwargs)

    def _build_params(
        self,
        messages: List[Dict[str, Any]],
        stream: bool,
        tools: Optional[List[Dict[str, Any]]],
        overrides: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build parameters for OpenAI API call."""
        params: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
        }

        if stream:
            params["stream_options"] = {"include_usage": True}

        temperature = overrides.get("temperature")
        if temperature is not None:
            params["temperature"] = temperature
        elif is_given(self.temperature):
            params["temperature"] = self.temperature

        # Add max_tokens if set
        max_tokens = overrides.get("max_tokens")
        if max_tokens is not None:
            params["max_tokens"] = max_tokens
        elif is_given(self.max_tokens):
            params["max_tokens"] = self.max_tokens

        # Add tools if provided
        if tools:
            params["tools"] = tools

        # Merge extra_kwargs
        for key, value in self._extra_kwargs.items():
            if key not in params:
                params[key] = value

        for key, value in overrides.items():
            if key not in ["temperature", "max_tokens", "tools"] and value is not None:
```
