# my_tool

**Kind:** function
**Signature:** `class ToolRegistry:`
**Source:** https://raw.githubusercontent.com/smallest-inc/smallest-python-sdk/main/smallestai/atoms/agent/tools/registry.py#toolregistry

## Example

```python
class ToolRegistry:
    """
    Registry for managing and executing tools.

    Example:
        registry = ToolRegistry()

        @function_tool
        async def get_weather(location: str):
            return {"temp": 75}

        registry.register(get_weather)

        # Get schemas for LLM
        schemas = registry.get_schemas()

        # Execute tool calls from LLM
        results = await registry.execute(tool_calls)
    """

    def __init__(self):
        """Initialize empty registry."""
        self._tools: Dict[str, FunctionToolInfo] = {}

    def register(self, func_or_info: Union[Callable, FunctionToolInfo]):
        """
        Register a @function_tool decorated function.

        Args:
            func: Function decorated with @function_tool

        Raises:
            ValueError: If function is not decorated

        Example:
            @function_tool
            async def my_tool(param: str):
                return "result"

            registry.register(my_tool)
        """

        if isinstance(func_or_info, FunctionToolInfo):
            self._tools[func_or_info.name] = func_or_info
            return

        if not is_function_tool(func_or_info):
            raise ValueError(
                f"{func_or_info.__name__} is not decorated with @function_tool. "
                f"Use @function_tool decorator before registering."
            )

        info: FunctionToolInfo = func_or_info.__tool_info__  # type: ignore

        # If the function is a class method then it will be bound to a class instance
        # but when using the decorator it runs before the class instance is created
        # so we need to bind the function to the class instance
        if inspect.ismethod(func_or_info):
            info = FunctionToolInfo(
                name=info.name,
                description=info.description,
                schema=info.schema,
                function=func_or_info,
            )

        self._tools[info.name] = info
        logger.debug(f"Registered tool: {info.name}")

    def discover(self, obj: Any):
        """
        Auto-discover and register all @function_tool methods in object.

        Args:
            obj: Object to scan for decorated methods

        Example:
            class MyAgent:
                @function_tool
                async def tool1(self): pass

                @function_tool
                async def tool2(self): pass

            agent = MyAgent()
            registry.discover(agent)  # Registers both tools
        """
        tools = find_function_tools(obj)
        for tool in tools:
            self.register(tool)

    def get_schemas(self) -> List[Dict[str, Any]]:
        """
        Get OpenAI-compatible tool schemas.

        Returns:
            List of tool schemas for LLM

        Example:
            schemas = registry.get_schemas()
            response = await llm.chat(messages=[...], tools=schemas)
        """
        return [
            {"type": "function", "function": tool.schema.to_dict()}
            for tool in self._tools.values()
        ]

    async def execute(
        self,
        tool_calls: List[ToolCall],
        context: Optional[Any] = None,
        parallel: bool = True,
    ) -> List[ToolResult]:
        """
        Execute tool calls automatically.

        Args:
            tool_calls: List of tool calls from LLM
            context: Optional context to pass to tools
            parallel: Execute tools in parallel (True) or sequential (False)
```
