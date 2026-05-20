> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Add audience members

POST https://api.smallest.ai/atoms/v1/audience/{id}/members
Content-Type: application/json

Add new members to an existing audience. Users can only add members to audiences they created.

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/audience/add-audience-members

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /audience/{id}/members:
    post:
      operationId: add-audience-members
      summary: Add audience members
      description: >-
        Add new members to an existing audience. Users can only add members to
        audiences they created.
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
          description: Members added successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Audience_addAudienceMembers_Response_200'
        '400':
          description: Bad request
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AddAudienceMembersRequestBadRequestError'
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
                $ref: '#/components/schemas/AddAudienceMembersRequestForbiddenError'
        '404':
          description: Audience not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AddAudienceMembersRequestNotFoundError'
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
                members:
                  type: array
                  items:
                    $ref: >-
                      #/components/schemas/AudienceIdMembersPostRequestBodyContentApplicationJsonSchemaMembersItems
                  description: >-
                    Array of member objects with dynamic structure based on
                    audience configuration
              required:
                - members
servers:
  - url: https://api.smallest.ai/atoms/v1
components:
  schemas:
    AudienceIdMembersPostRequestBodyContentApplicationJsonSchemaMembersItems:
      type: object
      properties: {}
      description: >-
        Member data with keys matching the audience's CSV structure. Must
        include the phone number column.
      title: AudienceIdMembersPostRequestBodyContentApplicationJsonSchemaMembersItems
    AudienceIdMembersPostResponsesContentApplicationJsonSchemaDataItemsData:
      type: object
      properties:
        added:
          type: integer
          description: Number of members successfully added
        skipped:
          type: integer
          description: Number of members skipped (e.g., duplicates)
      title: AudienceIdMembersPostResponsesContentApplicationJsonSchemaDataItemsData
    AudienceIdMembersPostResponsesContentApplicationJsonSchemaDataItems:
      type: object
      properties:
        message:
          type: string
        data:
          $ref: >-
            #/components/schemas/AudienceIdMembersPostResponsesContentApplicationJsonSchemaDataItemsData
      title: AudienceIdMembersPostResponsesContentApplicationJsonSchemaDataItems
    Audience_addAudienceMembers_Response_200:
      type: object
      properties:
        status:
          type: boolean
        data:
          type: array
          items:
            $ref: >-
              #/components/schemas/AudienceIdMembersPostResponsesContentApplicationJsonSchemaDataItems
      title: Audience_addAudienceMembers_Response_200
    AddAudienceMembersRequestBadRequestError:
      type: object
      properties:
        status:
          type: boolean
        errors:
          type: array
          items:
            type: string
      title: AddAudienceMembersRequestBadRequestError
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
    AddAudienceMembersRequestForbiddenError:
      type: object
      properties:
        status:
          type: boolean
        errors:
          type: array
          items:
            type: string
      title: AddAudienceMembersRequestForbiddenError
    AddAudienceMembersRequestNotFoundError:
      type: object
      properties:
        status:
          type: boolean
        errors:
          type: array
          items:
            type: string
      title: AddAudienceMembersRequestNotFoundError
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
    await client.atoms.audience.addAudienceMembers("60d0fe4f5311236168a109ca", {
        members: [
            {},
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

client.atoms.audience.add_audience_members(
    id="60d0fe4f5311236168a109ca",
    members=[
        {}
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

	payload := strings.NewReader("{\n  \"members\": [\n    {}\n  ]\n}")

	req, _ := http.NewRequest("POST", url, payload)

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

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Bearer '
request["Content-Type"] = 'application/json'
request.body = "{\n  \"members\": [\n    {}\n  ]\n}"

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse response = Unirest.post("https://api.smallest.ai/atoms/v1/audience/60d0fe4f5311236168a109ca/members")
  .header("Authorization", "Bearer ")
  .header("Content-Type", "application/json")
  .body("{\n  \"members\": [\n    {}\n  ]\n}")
  .asString();
```

```php
request('POST', 'https://api.smallest.ai/atoms/v1/audience/60d0fe4f5311236168a109ca/members', [
  'body' => '{
  "members": [
    {}
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
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Bearer ");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"members\": [\n    {}\n  ]\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Bearer ",
  "Content-Type": "application/json"
]
let parameters = ["members": [[]]] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/audience/60d0fe4f5311236168a109ca/members")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
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
