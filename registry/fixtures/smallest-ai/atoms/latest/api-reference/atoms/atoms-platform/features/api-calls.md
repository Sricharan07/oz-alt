> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# API Calls

> Connect agents to external systems.

API Calls let your agent interact with external systems during conversations — fetch customer data, book appointments, update CRMs, process payments.***## API Call Types| Type          | When It Runs               | Use Case                   |
| ------------- | -------------------------- | -------------------------- |
| **Pre-Call**  | Before conversation starts | Load customer context      |
| **Mid-Call**  | During conversation        | Check status, take action  |
| **Post-Call** | After conversation ends    | Log to CRM, create tickets |***## Configuration| Field                | Description                 |
| -------------------- | --------------------------- |
| **URL**              | API endpoint                |
| **Method**           | GET, POST, PUT, DELETE      |
| **Headers**          | Authorization, Content-Type |
| **Body**             | Request payload (JSON)      |
| **Response Mapping** | Extract data to variables   |***## Example**Request:**```
GET https://api.example.com/customers/{{caller_phone}}
```**Response:**```json
{
  "name": "Jane Smith",
  "tier": "premium"
}
```**Use in prompt:**```
Hello {{customer_name}}! I see you're a {{tier}} member.
```***## ImplementationAPI calls are configured differently in each agent type.API Calls in Configuration PanelDeprecatedAPI Call Nodes in Workflow
