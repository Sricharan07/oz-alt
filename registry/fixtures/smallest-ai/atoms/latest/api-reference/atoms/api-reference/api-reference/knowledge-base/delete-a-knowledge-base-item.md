> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Delete a knowledge base item

DELETE https://api.smallest.ai/atoms/v1/knowledgebase/{knowledgeBaseId}/items/{knowledgeBaseItemId}

Delete a knowledge base item

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/knowledge-base/delete-a-knowledge-base-item

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /knowledgebase/{knowledgeBaseId}/items/{knowledgeBaseItemId}:
    delete:
      operationId: delete-a-knowledge-base-item
      summary: Delete a knowledge base item
      description: Delete a knowledge base item
      tags:
        - subpackage_knowledgeBase
      parameters:
        - name: knowledgeBaseId
          in: path
          description: The ID of the knowledge base
          required: true
          schema:
            type: string
        - name: knowledgeBaseItemId
          in: path
          description: The ID of the knowledge base item
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
          description: Knowledge base item deleted successfully
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/Knowledge
                  Base_deleteAKnowledgeBaseItem_Response_200
        '400':
          description: Invalid input
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BadRequestErrorResponse'
        '401':
          description: Unauthorized access
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UnauthorizedErrorResponse'
        '500':
          description: Internal server error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/InternalServerErrorResponse'
servers:
  - url: https://api.smallest.ai/atoms/v1
components:
  schemas:
    Knowledge Base_deleteAKnowledgeBaseItem_Response_200:
      type: object
      properties:
        status:
          type: boolean
      title: Knowledge Base_deleteAKnowledgeBaseItem_Response_200
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
    UnauthorizedErrorResponse:
      type: object
      properties:
        status:
          type: boolean
        errors:
          type: array
          items:
            type: string
      title: UnauthorizedErrorResponse
    InternalServerErrorResponse:
      type: object
      properties:
        status:
          type: boolean
        errors:
          type: array
          items:
            type: string
      title: InternalServerErrorResponse
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      description: >-
        API key from the console ApiKey collection, sent as Bearer token. Also
        accepts session cookies for browser-based auth.

```

## SDK Code Examples

```typescript
import { SmallestAIClient } from "smallest-ai";

async function main() {
    const client = new SmallestAIClient({
        token: "YOUR_TOKEN_HERE",
    });
    await client.atoms.knowledgeBase.deleteAKnowledgeBaseItem("knowledgeBaseId", "knowledgeBaseItemId");
}
main();

```

```python
from smallest_ai import SmallestAI

client = SmallestAI(
    token="YOUR_TOKEN_HERE",
)

client.atoms.knowledge_base.delete_a_knowledge_base_item(
    knowledge_base_id="knowledgeBaseId",
    knowledge_base_item_id="knowledgeBaseItemId",
)

```

```go
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://api.smallest.ai/atoms/v1/knowledgebase/knowledgeBaseId/items/knowledgeBaseItemId"

	req, _ := http.NewRequest("DELETE", url, nil)

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

url = URI("https://api.smallest.ai/atoms/v1/knowledgebase/knowledgeBaseId/items/knowledgeBaseItemId")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Delete.new(url)
request["Authorization"] = 'Bearer '

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse response = Unirest.delete("https://api.smallest.ai/atoms/v1/knowledgebase/knowledgeBaseId/items/knowledgeBaseItemId")
  .header("Authorization", "Bearer ")
  .asString();
```

```php
request('DELETE', 'https://api.smallest.ai/atoms/v1/knowledgebase/knowledgeBaseId/items/knowledgeBaseItemId', [
  'headers' => [
    'Authorization' => 'Bearer ',
  ],
]);

echo $response->getBody();
```

```csharp
using RestSharp;

var client = new RestClient("https://api.smallest.ai/atoms/v1/knowledgebase/knowledgeBaseId/items/knowledgeBaseItemId");
var request = new RestRequest(Method.DELETE);
request.AddHeader("Authorization", "Bearer ");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Bearer "]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/knowledgebase/knowledgeBaseId/items/knowledgeBaseItemId")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "DELETE"
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
