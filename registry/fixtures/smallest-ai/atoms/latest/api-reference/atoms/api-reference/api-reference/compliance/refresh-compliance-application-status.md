> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Refresh compliance application status

POST https://api.smallest.ai/atoms/v1/compliance/applications/{id}/refresh

Manually poll Plivo for the latest status of a compliance application.
Use this as a fallback when webhooks are delayed. The frontend enforces a
60-second cooldown between refreshes.

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/compliance/refresh-compliance-application-status

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /compliance/applications/{id}/refresh:
    post:
      operationId: refresh-compliance-application-status
      summary: Refresh compliance application status
      description: >
        Manually poll Plivo for the latest status of a compliance application.

        Use this as a fallback when webhooks are delayed. The frontend enforces
        a

        60-second cooldown between refreshes.
      tags:
        - subpackage_compliance
      parameters:
        - name: id
          in: path
          description: The compliance application ID
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
          description: Application status refreshed
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/Compliance_refreshComplianceApplicationStatus_Response_200
        '401':
          description: Unauthorized access
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UnauthorizedErrorResponse'
        '404':
          description: Application not found or does not belong to this organization
          content:
            application/json:
              schema:
                description: Any type
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
    ComplianceApplicationStatus:
      type: string
      enum:
        - draft
        - submitted
        - accepted
        - rejected
        - suspended
        - expired
      description: Current status of the compliance application
      title: ComplianceApplicationStatus
    ComplianceApplicationNumberType:
      type: string
      enum:
        - local
        - mobile
        - tollfree
      title: ComplianceApplicationNumberType
    ComplianceApplicationUserType:
      type: string
      enum:
        - individual
        - business
      title: ComplianceApplicationUserType
    ComplianceApplication:
      type: object
      properties:
        _id:
          type: string
          description: Unique identifier
        organizationId:
          type: string
          description: The organization this application belongs to
        plivoComplianceId:
          type: string
          description: Plivo's compliance application identifier
        alias:
          type: string
          description: Auto-generated alias (orgId-countryIso-env)
        status:
          $ref: '#/components/schemas/ComplianceApplicationStatus'
          description: Current status of the compliance application
        countryIso:
          type: string
          description: ISO 3166-1 alpha-2 country code
        numberType:
          $ref: '#/components/schemas/ComplianceApplicationNumberType'
        userType:
          $ref: '#/components/schemas/ComplianceApplicationUserType'
        endUserName:
          type: string
          description: Legal business or individual name
        endUserLastName:
          type:
            - string
            - 'null'
        endUserEmail:
          type:
            - string
            - 'null'
        endUserCountry:
          type:
            - string
            - 'null'
        documentFileNames:
          type: array
          items:
            type: string
          description: Names of uploaded document files
        rejectionReason:
          type:
            - string
            - 'null'
          description: Reason for rejection, if applicable
        createdBy:
          type: string
          description: User ID of the person who created this application
        createdAt:
          type: string
          format: date-time
        updatedAt:
          type: string
          format: date-time
      description: >-
        A compliance application for a specific country, number type, and user
        type
      title: ComplianceApplication
    Compliance_refreshComplianceApplicationStatus_Response_200:
      type: object
      properties:
        status:
          type: boolean
        data:
          $ref: '#/components/schemas/ComplianceApplication'
      title: Compliance_refreshComplianceApplicationStatus_Response_200
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

```python
import requests

url = "https://api.smallest.ai/atoms/v1/compliance/applications/id/refresh"

payload = {}
headers = {
    "Authorization": "Bearer ",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.smallest.ai/atoms/v1/compliance/applications/id/refresh';
const options = {
  method: 'POST',
  headers: {Authorization: 'Bearer ', 'Content-Type': 'application/json'},
  body: '{}'
};

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
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.smallest.ai/atoms/v1/compliance/applications/id/refresh"

	payload := strings.NewReader("{}")

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

url = URI("https://api.smallest.ai/atoms/v1/compliance/applications/id/refresh")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Bearer '
request["Content-Type"] = 'application/json'
request.body = "{}"

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse response = Unirest.post("https://api.smallest.ai/atoms/v1/compliance/applications/id/refresh")
  .header("Authorization", "Bearer ")
  .header("Content-Type", "application/json")
  .body("{}")
  .asString();
```

```php
request('POST', 'https://api.smallest.ai/atoms/v1/compliance/applications/id/refresh', [
  'body' => '{}',
  'headers' => [
    'Authorization' => 'Bearer ',
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

```csharp
using RestSharp;

var client = new RestClient("https://api.smallest.ai/atoms/v1/compliance/applications/id/refresh");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Bearer ");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Bearer ",
  "Content-Type": "application/json"
]
let parameters = [] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/compliance/applications/id/refresh")! as URL,
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
