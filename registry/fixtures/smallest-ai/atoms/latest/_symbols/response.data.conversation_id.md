# response.data.conversation_id

**Kind:** heading
**Signature:** `response.data.conversation_id`
**Source:** https://docs.smallest.ai/atoms/developer-guide/build/calling/outbound-calls

## Example

```markdown
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
```
