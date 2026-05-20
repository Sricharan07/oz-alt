# get_weather

**Kind:** function
**Signature:** `class AssistantAgent(OutputAgentNode):`
**Source:** https://raw.githubusercontent.com/smallest-inc/smallest-python-sdk/main/examples/tool_calling-1/assistant_agent.py#assistantagent

## Example

```python
class AssistantAgent(OutputAgentNode):
    """Assistant that can call tools to answer questions."""

    def __init__(self):
        super().__init__(name="assistant-agent")
        self.llm = OpenAIClient(
            model="gpt-4o", temperature=0.7, api_key=os.getenv("OPENAI_API_KEY")
        )

        # Initialize tool registry
        self.tool_registry = ToolRegistry()
        self.tool_registry.discover(self)
        self.tool_schemas = self.tool_registry.get_schemas()

        self.context.add_message(
            {
                "role": "system",
                "content": "You are a helpful assistant that can call tools to answer questions.",
            }
        )

    async def generate_response(self):
        """Generate response with tool calling support."""

        response = await self.llm.chat(
            messages=self.context.messages, stream=True, tools=self.tool_schemas
        )

        tool_calls: List[ToolCall] = []

        async for chunk in response:
            if chunk.content:
                yield chunk.content
            if chunk.tool_calls:
                tool_calls.extend(chunk.tool_calls)

        if tool_calls:
            results: List[ToolResult] = await self.tool_registry.execute(
                tool_calls=tool_calls, parallel=True
            )

            self.context.add_messages(
                [
                    {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.name,
                                    "arguments": str(tc.arguments),
                                },
                            }
                            for tc in tool_calls
                        ],
                    },
                    *[
                        {"role": "tool", "tool_call_id": tc.id, "content": str(result)}
                        for tc, result in zip(tool_calls, results)
                    ],
                ]
            )

            final_response = await self.llm.chat(
                messages=self.context.messages, stream=True
            )

            async for chunk in final_response:
                if chunk.content:
                    yield chunk.content

    @function_tool()
    def get_weather(self, location: str, unit: str = "celsius"):
        """Get current weather for a location.

        Args:
            location: City and state, e.g., "San Francisco, CA"
            unit: Temperature unit (celsius or fahrenheit)
        """
        # Simulate weather API call
        weather_data = {
            "San Francisco, CA": {"temp": 18, "conditions": "Foggy"},
            "New York, NY": {"temp": 22, "conditions": "Sunny"},
            "London, UK": {"temp": 15, "conditions": "Rainy"},
        }

        result = weather_data.get(location, {"temp": 20, "conditions": "Clear"})

        return {
            "location": location,
            "temperature": result["temp"],
            "unit": unit,
            "conditions": result["conditions"],
        }

    @function_tool()
    def calculate(self, operation: str, a: float, b: float):
        """Perform mathematical calculation.

        Args:
            operation: Operation to perform (add, subtract, multiply, divide)
            a: First number
            b: Second number
        """
        operations = {
            "add": lambda x, y: x + y,
            "subtract": lambda x, y: x - y,
            "multiply": lambda x, y: x * y,
            "divide": lambda x, y: x / y if y != 0 else "Error: Division by zero",
        }

        if operation not in operations:
            return {"error": f"Unknown operation: {operation}"}

        result = operations[operation](a, b)

        return {"operation": operation, "a": a, "b": b, "result": result}
```
