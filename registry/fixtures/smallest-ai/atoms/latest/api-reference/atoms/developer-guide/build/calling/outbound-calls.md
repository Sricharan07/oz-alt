> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Outbound Calls

> Make phone calls programmatically with your AI agent.

Use `start_outbound_call()` to dial any phone number and connect it to your agent.

## Basic Call

```python
from smallestai.atoms import AtomsClient

client = AtomsClient()

response = client.start_outbound_call(
    conversation_outbound_post_request={
        "agentId": "your-agent-id",
        "phoneNumber": "+14155551234"
    }
)

conversation_id = response.data.conversation_id
print(f"Call started: {conversation_id}")
```

## Parameters

| Parameter     | Type   | Required | Description                       |
| ------------- | ------ | -------- | --------------------------------- |
| `agentId`     | string | Yes      | ID of your agent (from dashboard) |
| `phoneNumber` | string | Yes      | E.164 format phone number         |

Phone numbers must be in E.164 format: `+[country code][number]`

Examples: `+14155551234` (US), `+919876543210` (India)

## Response

```python
# response.data.conversation_id = "CALL-1767900635803-8a3bee"
```

| Field             | Type   | Description                  |
| ----------------- | ------ | ---------------------------- |
| `conversation_id` | string | Unique ID to track this call |

Save this ID to retrieve transcripts and analytics later.

## Error Handling

```python
try:
    response = client.start_outbound_call(
        conversation_outbound_post_request={
            "agentId": "agent-123",
            "phoneNumber": "+14155551234"
        }
    )
    print(f"Call started: {response.data.conversation_id}")

except Exception as e:
    error = str(e)

    if "Invalid agent id" in error:
        print("Error: Agent not found. Check your agent ID.")
    elif "Invalid phone" in error:
        print("Error: Invalid phone number. Use E.164 format.")
    elif "401" in error:
        print("Error: Check your API key.")
    else:
        print(f"Error: {error}")
```

## Tips

Use a library like `phonenumbers` to validate before calling. Invalid numbers waste API calls.

Wait 5-10 seconds between calls to avoid rate limits.

Save them in your database to retrieve transcripts later.

Wrap calls in try/except and log failures for retry.
