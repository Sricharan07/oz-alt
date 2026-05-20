> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Get audience members

GET https://api.smallest.ai/atoms/v1/audience/{id}/members

Retrieve members of a specific audience with pagination support. Users can only access members of audiences they created.

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/audience/get-audience-members

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /audience/{id}/members:
    get:
      operationId: get-audience-members
      summary: Get audience members
      description: >-
        Retrieve members of a specific audience with pagination support. Users
        can only access members of audiences they created.
      tags:
        - subpackage_audience
      parameters:
        - name: id
          in: path
          description: The unique identifier of the audience
          required: true
          schema:
            type: string
        - name: page
          in: query
          description: Page number for pagination (default is 1)
          required: false
          schema:
            type: integer
            default: 1
        - name: limit
          in: query
          description: Number of items per page (default is 5)
          required: false
          schema:
            type: integer
            default: 5
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
          description: Successfully retrieved audience members
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Audience_getAudienceMembers_Response_200'
        '400':
          description: Bad request
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GetAudienceMembersRequestBadRequestError'
        '500':
          description: Internal server error
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/GetAudienceMembersRequestInternalServerError
servers:
  - url: https://api.smallest.ai/atoms/v1
components:
  schemas:
    AudienceIdMembersGetResponsesContentApplicationJsonSchemaDataMembersItemsData:
      type: object
      properties: {}
      description: Dynamic data from CSV, structure depends on uploaded file
      title: >-
        AudienceIdMembersGetResponsesContentApplicationJsonSchemaDataMembersItemsData
    AudienceIdMembersGetResponsesContentApplicationJsonSchemaDataMembersItems:
      type: object
      properties:
        _id:
          type: string
          description: The unique identifier for the audience member
        data:
          $ref: >-
            #/components/schemas/AudienceIdMembersGetResponsesContentApplicationJsonSchemaDataMembersItemsData
          description: Dynamic data from CSV, structure depends on uploaded file
      title: >-
        AudienceIdMembersGetResponsesContentApplicationJsonSchemaDataMembersItems
    AudienceIdMembersGetResponsesContentApplicationJsonSchemaData:
      type: object
      properties:
        members:
          type: array
          items:
            $ref: >-
              #/components/schemas/AudienceIdMembersGetResponsesContentApplicationJsonSchemaDataMembersItems
        totalCount:
          type: integer
          description: Total number of members in the audience
        totalPages:
          type: integer
          description: Total number of pages available
        hasMore:
          type: boolean
          description: Whether there are more pages available
      title: AudienceIdMembersGetResponsesContentApplicationJsonSchemaData
    Audience_getAudienceMembers_Response_200:
      type: object
      properties:
        status:
          type: boolean
        data:
          $ref: >-
            #/components/schemas/AudienceIdMembersGetResponsesContentApplicationJsonSchemaData
      title: Audience_getAudienceMembers_Response_200
    GetAudienceMembersRequestBadRequestError:
      type: object
      properties:
        status:
          type: string
        errors:
          type: array
          items:
            type: string
      title: GetAudienceMembersRequestBadRequestError
    GetAudienceMembersRequestInternalServerError:
      type: object
      properties:
        status:
          type: boolean
        errors:
          type: array
          items:
            type: string
      title: GetAudienceMembersRequestInternalServerError
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
    await client.atoms.audience.getAudienceMembers("60d0fe4f5311236168a109ca", {});
}
main();

```

```python
from smallest_ai import SmallestAI

client = SmallestAI(
    token="YOUR_TOKEN_HERE",
)

client.atoms.audience.get_audience_members(
    id="60d0fe4f5311236168a109ca",
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

	url := "https://api.smallest.ai/atoms/v1/audience/60d0fe4f5311236168a109ca/members"

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

url = URI("https://api.smallest.ai/atoms/v1/audience/60d0fe4f5311236168a109ca/members")

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

HttpResponse response = Unirest.get("https://api.smallest.ai/atoms/v1/audience/60d0fe4f5311236168a109ca/members")
  .header("Authorization", "Bearer ")
  .asString();
```

```php
request('GET', 'https://api.smallest.ai/atoms/v1/audience/60d0fe4f5311236168a109ca/members', [
  'headers' => [
    'Authorization' => 'Bearer ',
  ],
]);

echo $response->getBody();
```

```csharp
using RestSharp;

var client = new RestClient("https://api.smallest.ai/atoms/v1/audience/60d0fe4f5311236168a109ca/members");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Bearer ");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Bearer "]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/audience/60d0fe4f5311236168a109ca/members")! as URL,
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
