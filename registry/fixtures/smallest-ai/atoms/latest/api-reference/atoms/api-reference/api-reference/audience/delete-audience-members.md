> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Delete audience members

DELETE https://api.smallest.ai/atoms/v1/audience/{id}/members
Content-Type: application/json

Remove specific members from an audience by their member IDs. Users can only delete members from audiences they created.

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/audience/delete-audience-members

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /audience/{id}/members:
    delete:
      operationId: delete-audience-members
      summary: Delete audience members
      description: >-
        Remove specific members from an audience by their member IDs. Users can
        only delete members from audiences they created.
      tags:
        - subpackage_audience
      parameters:
        - name: id
          in: path
          description: The unique identifier of the audience
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
          description: Members deleted successfully
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/Audience_deleteAudienceMembers_Response_200
        '400':
          description: Bad request
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/DeleteAudienceMembersRequestBadRequestError
        '401':
          description: Unauthorized access
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UnauthorizedErrorResponse'
        '403':
          description: Forbidden - User can only modify audiences they created
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/DeleteAudienceMembersRequestForbiddenError
        '404':
          description: Audience not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DeleteAudienceMembersRequestNotFoundError'
        '500':
          description: Internal server error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/InternalServerErrorResponse'
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                memberIds:
                  type: array
                  items:
                    type: string
                  description: Array of member IDs to delete
              required:
                - memberIds
servers:
  - url: https://api.smallest.ai/atoms/v1
components:
  schemas:
    AudienceIdMembersDeleteResponsesContentApplicationJsonSchemaData:
      type: object
      properties:
        deletedCount:
          type: integer
          description: Number of members successfully deleted
      title: AudienceIdMembersDeleteResponsesContentApplicationJsonSchemaData
    Audience_deleteAudienceMembers_Response_200:
      type: object
      properties:
        status:
          type: boolean
        data:
          $ref: >-
            #/components/schemas/AudienceIdMembersDeleteResponsesContentApplicationJsonSchemaData
      title: Audience_deleteAudienceMembers_Response_200
    DeleteAudienceMembersRequestBadRequestError:
      type: object
      properties:
        status:
          type: boolean
        errors:
          type: array
          items:
            type: string
      title: DeleteAudienceMembersRequestBadRequestError
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
    DeleteAudienceMembersRequestForbiddenError:
      type: object
      properties:
        status:
          type: boolean
        errors:
          type: array
          items:
            type: string
      title: DeleteAudienceMembersRequestForbiddenError
    DeleteAudienceMembersRequestNotFoundError:
      type: object
      properties:
        status:
          type: boolean
        errors:
          type: array
          items:
            type: string
      title: DeleteAudienceMembersRequestNotFoundError
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
    await client.atoms.audience.deleteAudienceMembers("60d0fe4f5311236168a109ca", {
        memberIds: [
            "60d0fe4f5311236168a109cd",
        ],
    });
}
main();

```

```python
from smallest_ai import SmallestAI

client = SmallestAI(
    token="YOUR_TOKEN_HERE",
)

client.atoms.audience.delete_audience_members(
    id="60d0fe4f5311236168a109ca",
    member_ids=[
        "60d0fe4f5311236168a109cd"
    ],
)

```

```go
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.smallest.ai/atoms/v1/audience/60d0fe4f5311236168a109ca/members"

	payload := strings.NewReader("{\n  \"memberIds\": [\n    \"60d0fe4f5311236168a109cd\"\n  ]\n}")

	req, _ := http.NewRequest("DELETE", url, payload)

	req.Header.Add("Authorization", "Bearer ")
	req.Header.Add("Content-Type", "application/json")

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

url = URI("https://api.smallest.ai/atoms/v1/audience/60d0fe4f5311236168a109ca/members")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Delete.new(url)
request["Authorization"] = 'Bearer '
request["Content-Type"] = 'application/json'
request.body = "{\n  \"memberIds\": [\n    \"60d0fe4f5311236168a109cd\"\n  ]\n}"

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse response = Unirest.delete("https://api.smallest.ai/atoms/v1/audience/60d0fe4f5311236168a109ca/members")
  .header("Authorization", "Bearer ")
  .header("Content-Type", "application/json")
  .body("{\n  \"memberIds\": [\n    \"60d0fe4f5311236168a109cd\"\n  ]\n}")
  .asString();
```

```php
request('DELETE', 'https://api.smallest.ai/atoms/v1/audience/60d0fe4f5311236168a109ca/members', [
  'body' => '{
  "memberIds": [
    "60d0fe4f5311236168a109cd"
  ]
}',
  'headers' => [
    'Authorization' => 'Bearer ',
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

```csharp
using RestSharp;

var client = new RestClient("https://api.smallest.ai/atoms/v1/audience/60d0fe4f5311236168a109ca/members");
var request = new RestRequest(Method.DELETE);
request.AddHeader("Authorization", "Bearer ");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"memberIds\": [\n    \"60d0fe4f5311236168a109cd\"\n  ]\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Bearer ",
  "Content-Type": "application/json"
]
let parameters = ["memberIds": ["60d0fe4f5311236168a109cd"]] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/audience/60d0fe4f5311236168a109ca/members")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "DELETE"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

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
