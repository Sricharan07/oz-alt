> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Get all knowledge base items

GET https://api.smallest.ai/atoms/v1/knowledgebase/{id}/items

Get all knowledge base items

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/knowledge-base/get-all-knowledge-base-items

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /knowledgebase/{id}/items:
    get:
      operationId: get-all-knowledge-base-items
      summary: Get all knowledge base items
      description: Get all knowledge base items
      tags:
        - subpackage_knowledgeBase
      parameters:
        - name: id
          in: path
          description: The ID of the knowledge base
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
          description: A list of knowledge base items
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/Knowledge
                  Base_getAllKnowledgeBaseItems_Response_200
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
    KnowledgeBaseItemItemType:
      type: string
      enum:
        - file
        - text
      description: The type of the knowledge base item
      title: KnowledgeBaseItemItemType
    KnowledgeBaseItemMetadata:
      type: object
      properties: {}
      description: Additional metadata for the item
      title: KnowledgeBaseItemMetadata
    KnowledgeBaseItemProcessingStatus:
      type: string
      enum:
        - pending
        - processing
        - completed
        - failed
      description: The processing status of the item
      title: KnowledgeBaseItemProcessingStatus
    KnowledgeBaseItem:
      type: object
      properties:
        _id:
          type: string
          description: The unique identifier for the knowledge base item
        itemType:
          $ref: '#/components/schemas/KnowledgeBaseItemItemType'
          description: The type of the knowledge base item
        metadata:
          $ref: '#/components/schemas/KnowledgeBaseItemMetadata'
          description: Additional metadata for the item
        knowledgeBaseId:
          type: string
          description: The ID of the knowledge base this item belongs to
        processingStatus:
          $ref: '#/components/schemas/KnowledgeBaseItemProcessingStatus'
          description: The processing status of the item
        fileName:
          type: string
          description: The name of the file (for file type items)
        contentType:
          type: string
          description: The MIME type of the content
        size:
          type: number
          format: double
          description: The size of the file in bytes
        key:
          type: string
          description: The storage key for the file
        title:
          type: string
          description: The title of the item
        content:
          type: string
          description: The content of the item (for text type items)
        createdAt:
          type: string
          format: date-time
          description: The date and time when the item was created
        updatedAt:
          type: string
          format: date-time
          description: The date and time when the item was last updated
      required:
        - _id
        - itemType
        - knowledgeBaseId
        - processingStatus
        - createdAt
        - updatedAt
      title: KnowledgeBaseItem
    Knowledge Base_getAllKnowledgeBaseItems_Response_200:
      type: object
      properties:
        status:
          type: boolean
        data:
          type: array
          items:
            $ref: '#/components/schemas/KnowledgeBaseItem'
      title: Knowledge Base_getAllKnowledgeBaseItems_Response_200
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
    await client.atoms.knowledgeBase.getAllKnowledgeBaseItems("id");
}
main();

```

```python
from smallest_ai import SmallestAI

client = SmallestAI(
    token="YOUR_TOKEN_HERE",
)

client.atoms.knowledge_base.get_all_knowledge_base_items(
    id="id",
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

	url := "https://api.smallest.ai/atoms/v1/knowledgebase/id/items"

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

url = URI("https://api.smallest.ai/atoms/v1/knowledgebase/id/items")

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

HttpResponse response = Unirest.get("https://api.smallest.ai/atoms/v1/knowledgebase/id/items")
  .header("Authorization", "Bearer ")
  .asString();
```

```php
request('GET', 'https://api.smallest.ai/atoms/v1/knowledgebase/id/items', [
  'headers' => [
    'Authorization' => 'Bearer ',
  ],
]);

echo $response->getBody();
```

```csharp
using RestSharp;

var client = new RestClient("https://api.smallest.ai/atoms/v1/knowledgebase/id/items");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Bearer ");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Bearer "]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/knowledgebase/id/items")! as URL,
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
