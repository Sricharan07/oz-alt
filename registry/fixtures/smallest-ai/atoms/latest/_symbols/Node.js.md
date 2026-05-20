# Node.js

**Kind:** heading
**Signature:** `Node.js`
**Source:** https://docs.smallest.ai/atoms/developer-guide/operate/analytics/sse-for-live-transcripts

## Example

```markdown
};

evtSource.onerror = (err) => {
  console.error("SSE connection error:", err);
  evtSource.close();
};
```

### Node.js

```javascript
import EventSource from "eventsource";

const BASE_URL = "https://api.smallest.ai/atoms/v1";
const callId = "CALL-1758124225863-80752e";

const es = new EventSource(
```
