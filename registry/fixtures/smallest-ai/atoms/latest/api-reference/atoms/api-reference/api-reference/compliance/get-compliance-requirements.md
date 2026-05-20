> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Get compliance requirements

GET https://api.smallest.ai/atoms/v1/compliance/requirements

Discover what documents are required for a given country, number type, and user type.
Results are cached for 1 hour. Returns an empty `documentTypes` array if no compliance
is needed for the given combination.

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/compliance/get-compliance-requirements

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /compliance/requirements:
    get:
      operationId: get-compliance-requirements
      summary: Get compliance requirements
      description: >
        Discover what documents are required for a given country, number type,
        and user type.

        Results are cached for 1 hour. Returns an empty `documentTypes` array if
        no compliance

        is needed for the given combination.
      tags:
        - subpackage_compliance
      parameters:
        - name: countryIso
          in: query
          description: ISO 3166-1 alpha-2 country code
          required: true
          schema:
            type: string
        - name: numberType
          in: query
          description: The type of phone number
          required: true
          schema:
            $ref: '#/components/schemas/ComplianceRequirementsGetParametersNumberType'
        - name: userType
          in: query
          description: The type of end user
          required: true
          schema:
            $ref: '#/components/schemas/ComplianceRequirementsGetParametersUserType'
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
          description: Requirements retrieved successfully
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/Compliance_getComplianceRequirements_Response_200
        '400':
          description: Invalid query parameters
          content:
            application/json:
              schema:
                description: Any type
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
    ComplianceRequirementsGetParametersNumberType:
      type: string
      enum:
        - local
        - mobile
        - tollfree
      title: ComplianceRequirementsGetParametersNumberType
    ComplianceRequirementsGetParametersUserType:
      type: string
      enum:
        - individual
        - business
      title: ComplianceRequirementsGetParametersUserType
    RequiredDocumentTypeRequiredFieldsItems:
      type: object
      properties:
        fieldName:
          type: string
        friendlyName:
          type: string
        helpText:
          type: string
        fieldType:
          type: string
        required:
          type: boolean
      title: RequiredDocumentTypeRequiredFieldsItems
    RequiredDocumentType:
      type: object
      properties:
        documentTypeId:
          type: string
          description: Identifier to use when submitting this document type
        name:
          type: string
          description: Human-readable name
        description:
          type: string
          description: Description of what this document should contain
        proofRequired:
          type: boolean
          description: Whether a file upload is required for this document type
        requiredFields:
          type: array
          items:
            $ref: '#/components/schemas/RequiredDocumentTypeRequiredFieldsItems'
          description: Data fields that must be provided alongside the document
      description: A document type required for compliance
      title: RequiredDocumentType
    ComplianceRequirement:
      type: object
      properties:
        requirementId:
          type: string
          description: Plivo's requirement identifier
        countryIso:
          type: string
        numberType:
          type: string
        userType:
          type: string
        documentTypes:
          type: array
          items:
            $ref: '#/components/schemas/RequiredDocumentType'
          description: Required document types. Empty array means no compliance is needed.
      description: Compliance requirements for a country/numberType/userType combination
      title: ComplianceRequirement
    Compliance_getComplianceRequirements_Response_200:
      type: object
      properties:
        status:
          type: boolean
        data:
          $ref: '#/components/schemas/ComplianceRequirement'
      title: Compliance_getComplianceRequirements_Response_200
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

url = "https://api.smallest.ai/atoms/v1/compliance/requirements"

querystring = {"countryIso":"US","numberType":"mobile","userType":"individual"}

payload = {}
headers = {
    "Authorization": "Bearer ",
    "Content-Type": "application/json"
}

response = requests.get(url, json=payload, headers=headers, params=querystring)

print(response.json())
```

```javascript
const url = 'https://api.smallest.ai/atoms/v1/compliance/requirements?countryIso=US&numberType=mobile&userType=individual';
const options = {
  method: 'GET',
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

	url := "https://api.smallest.ai/atoms/v1/compliance/requirements?countryIso=US&numberType=mobile&userType=individual"

	payload := strings.NewReader("{}")

	req, _ := http.NewRequest("GET", url, payload)

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

url = URI("https://api.smallest.ai/atoms/v1/compliance/requirements?countryIso=US&numberType=mobile&userType=individual")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["Authorization"] = 'Bearer '
request["Content-Type"] = 'application/json'
request.body = "{}"

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse response = Unirest.get("https://api.smallest.ai/atoms/v1/compliance/requirements?countryIso=US&numberType=mobile&userType=individual")
  .header("Authorization", "Bearer ")
  .header("Content-Type", "application/json")
  .body("{}")
  .asString();
```

```php
request('GET', 'https://api.smallest.ai/atoms/v1/compliance/requirements?countryIso=US&numberType=mobile&userType=individual', [
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

var client = new RestClient("https://api.smallest.ai/atoms/v1/compliance/requirements?countryIso=US&numberType=mobile&userType=individual");
var request = new RestRequest(Method.GET);
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

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/compliance/requirements?countryIso=US&numberType=mobile&userType=individual")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"
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
