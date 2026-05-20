> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Tools & Functions

> Giving your agent the ability to take action.

**Tools** let your agent do things—look up orders, check weather, book appointments, or end a call. When a user asks something that requires real data or an action, the LLM decides to call a tool instead of making something up.

## What are Tools?

Tools are Python functions that your agent can invoke during a conversation. The LLM analyzes the user's request, decides which tool to call (if any), and your code executes it. The result is fed back to the LLM so it can respond naturally.

This is also known as **function calling** or **tool use**.

## How It Works

1. User says "What's the weather in NYC?"
2. LLM decides to call `get_weather("New York, NY")`
3. Your function runs and returns `{"temp": 72}`
4. LLM responds "It's 72°F in New York City!"

The LLM never runs your code directly—it just tells you what to run and with what arguments.

## Key Concepts

| Concept                | Description                                                  |
| ---------------------- | ------------------------------------------------------------ |
| **@function\_tool()**  | Decorator that marks a method as callable by the LLM         |
| **ToolRegistry**       | Discovers and manages all tools on your agent                |
| **Tool Schemas**       | Auto-generated from your function's docstring and type hints |
| **Parallel Execution** | Run multiple tool calls at once                              |

## What's Next

The `@function_tool` decorator, docstrings, and type hints.

ToolRegistry, handling calls, and feeding results back.

SDK-provided actions: ending calls, transferring to humans.
