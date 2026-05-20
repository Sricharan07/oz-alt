> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Subscribe to live call events (SSE)

GET https://api.smallest.ai/atoms/v1/events

Real-time streaming of user speech (STT) and agent speech (TTS) events for an active call via Server-Sent Events.

The connection is real-time — events stream directly from the call runtime as they are produced. The SSE connection auto-closes when the call ends (`sse_close` event). Only active calls can be subscribed to; completed calls return a 400 error.

**Transcript event types:**

- `user_interim_transcription` — Partial, in-progress transcription as the user speaks. Use for live preview only; will be superseded by `user_transcription`.
- `user_transcription` — Final transcription for a completed user speech turn.
- `tts_completed` — Fired when the agent finishes speaking a TTS segment. Includes the spoken text and optionally TTS latency.

**Lifecycle events:**

- `sse_init` — Sent immediately when the SSE connection is established.
- `sse_close` — Sent when the call ends, right before the server closes the connection.

Other event types (e.g. `call_start`, `call_end`, `turn_latency`, metrics) are also sent on this stream.

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/live-transcripts/subscribe-to-live-call-events-sse

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /events:
    get:
      operationId: subscribe-to-live-call-events-sse
      summary: Subscribe to live call events (SSE)
      description: >
        Real-time streaming of user speech (STT) and agent speech (TTS) events
        for an active call via Server-Sent Events.

        The connection is real-time — events stream directly from the call
        runtime as they are produced. The SSE connection auto-closes when the
        call ends (`sse_close` event). Only active calls can be subscribed to;
        completed calls return a 400 error.

        **Transcript event types:**

        - `user_interim_transcription` — Partial, in-progress transcription as
        the user speaks. Use for live preview only; will be superseded by
        `user_transcription`.

        - `user_transcription` — Final transcription for a completed user speech
        turn.

        - `tts_completed` — Fired when the agent finishes speaking a TTS
        segment. Includes the spoken text and optionally TTS latency.

        **Lifecycle events:**

        - `sse_init` — Sent immediately when the SSE connection is established.

        - `sse_close` — Sent when the call ends, right before the server closes
        the connection.

        Other event types (e.g. `call_start`, `call_end`, `turn_latency`,
        metrics) are also sent on this stream.
      tags:
        - subpackage_liveTranscripts
      parameters:
        - name: callId
          in: query
          description: The call ID to subscribe events for
          required: true
          schema:
            type: string
        - name: Authorization
          in: header
          description: >-
            API key from the console ApiKey collection, sent as Bearer token.
            Also accepts session cookies for browser-based auth.
          required: true
          schema:
            type: string
      responses:
        '200':
          description: SSE event stream established successfully
          content:
            text/event-stream:
              schema:
                $ref: >-
                  #/components/schemas/Live
                  Transcripts_subscribeToLiveCallEventsSse_Response_200
        '400':
          description: Invalid input
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BadRequestErrorResponse'
        '404':
          description: Not authorized (org mismatch) or call/agent not found
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/SubscribeToLiveCallEventsSseRequestNotFoundError
servers:
  - url: https://api.smallest.ai/atoms/v1
components:
  schemas:
    EventsGetResponsesContentSseSchemaEventType:
      type: string
      enum:
        - sse_init
        - user_interim_transcription
        - user_transcription
        - tts_completed
        - sse_close
      description: The type of event
      title: EventsGetResponsesContentSseSchemaEventType
    Live Transcripts_subscribeToLiveCallEventsSse_Response_200:
      type: object
      properties:
        event_type:
          $ref: '#/components/schemas/EventsGetResponsesContentSseSchemaEventType'
          description: The type of event
        event_id:
          type: string
          description: Unique identifier for the event
        timestamp:
          type: string
          format: date-time
          description: ISO 8601 timestamp of the event
        call_id:
          type: string
          description: The call ID this event belongs to
        interim_transcription_text:
          type: string
          description: Partial transcription text (only for `user_interim_transcription`)
        user_transcription_text:
          type: string
          description: Final transcription text (only for `user_transcription`)
        tts_text:
          type: string
          description: Text spoken by the agent (only for `tts_completed`)
        tts_latency:
          type: integer
          description: TTS latency in milliseconds (only for `tts_completed`)
      description: >
        Events are sent as `data: \n\n`. Each event has an `event_type`
        field.
      title: Live Transcripts_subscribeToLiveCallEventsSse_Response_200
    BadRequestErrorResponse:
      type: object
      properties:
        status:
          type: boolean
        errors:
          type: array
          items:
            type: string
      title: BadRequestErrorResponse
    SubscribeToLiveCallEventsSseRequestNotFoundError:
      type: object
      properties:
        status:
          type: boolean
        errors:
          type: array
          items:
            type: string
      title: SubscribeToLiveCallEventsSseRequestNotFoundError
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      description: >-
        API key from the console ApiKey collection, sent as Bearer token. Also
        accepts session cookies for browser-based auth.

```

## SDK Code Examples

```python
import requests

url = "https://api.smallest.ai/atoms/v1/events"

querystring = {"callId":"CALL-1758124225863-80752e"}

headers = {"Authorization": "Bearer "}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())
```

```javascript
const url = 'https://api.smallest.ai/atoms/v1/events?callId=CALL-1758124225863-80752e';
const options = {method: 'GET', headers: {Authorization: 'Bearer '}};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

```go
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://api.smallest.ai/atoms/v1/events?callId=CALL-1758124225863-80752e"

	req, _ := http.NewRequest("GET", url, nil)

	req.Header.Add("Authorization", "Bearer ")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.smallest.ai/atoms/v1/events?callId=CALL-1758124225863-80752e")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["Authorization"] = 'Bearer '

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse response = Unirest.get("https://api.smallest.ai/atoms/v1/events?callId=CALL-1758124225863-80752e")
  .header("Authorization", "Bearer ")
  .asString();
```

```php
request('GET', 'https://api.smallest.ai/atoms/v1/events?callId=CALL-1758124225863-80752e', [
  'headers' => [
    'Authorization' => 'Bearer ',
  ],
]);

echo $response->getBody();
```

```csharp
using RestSharp;

var client = new RestClient("https://api.smallest.ai/atoms/v1/events?callId=CALL-1758124225863-80752e");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Bearer ");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Bearer "]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/events?callId=CALL-1758124225863-80752e")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"
request.allHTTPHeaderFields = headers

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```
