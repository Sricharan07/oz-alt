> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Get organization details

GET https://api.smallest.ai/atoms/v1/organization

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/organization/get-organization-details

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /organization:
    get:
      operationId: get-organization-details
      summary: Get organization details
      tags:
        - subpackage_organization
      parameters:
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
          description: Successful response
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/Organization_getOrganizationDetails_Response_200
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
    OrganizationGetResponsesContentApplicationJsonSchemaDataMembersItems:
      type: object
      properties:
        _id:
          type: string
          description: The member ID
        userEmail:
          type: string
          description: The member email
      title: OrganizationGetResponsesContentApplicationJsonSchemaDataMembersItems
    OrganizationGetResponsesContentApplicationJsonSchemaDataSubscription:
      type: object
      properties:
        planId:
          type: string
          description: The subscription plan ID
      title: OrganizationGetResponsesContentApplicationJsonSchemaDataSubscription
    OrganizationGetResponsesContentApplicationJsonSchemaData:
      type: object
      properties:
        _id:
          type: string
          description: The organization ID
        name:
          type: string
          description: The organization name
        members:
          type: array
          items:
            $ref: >-
              #/components/schemas/OrganizationGetResponsesContentApplicationJsonSchemaDataMembersItems
        subscription:
          $ref: >-
            #/components/schemas/OrganizationGetResponsesContentApplicationJsonSchemaDataSubscription
      title: OrganizationGetResponsesContentApplicationJsonSchemaData
    Organization_getOrganizationDetails_Response_200:
      type: object
      properties:
        status:
          type: boolean
        data:
          $ref: >-
            #/components/schemas/OrganizationGetResponsesContentApplicationJsonSchemaData
      title: Organization_getOrganizationDetails_Response_200
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
    await client.atoms.organization.getOrganizationDetails();
}
main();

```

```python
from smallest_ai import SmallestAI

client = SmallestAI(
    token="YOUR_TOKEN_HERE",
)

client.atoms.organization.get_organization_details()

```

```go
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://api.smallest.ai/atoms/v1/organization"

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

url = URI("https://api.smallest.ai/atoms/v1/organization")

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

HttpResponse response = Unirest.get("https://api.smallest.ai/atoms/v1/organization")
  .header("Authorization", "Bearer ")
  .asString();
```

```php
request('GET', 'https://api.smallest.ai/atoms/v1/organization', [
  'headers' => [
    'Authorization' => 'Bearer ',
  ],
]);

echo $response->getBody();
```

```csharp
using RestSharp;

var client = new RestClient("https://api.smallest.ai/atoms/v1/organization");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Bearer ");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Bearer "]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/organization")! as URL,
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
