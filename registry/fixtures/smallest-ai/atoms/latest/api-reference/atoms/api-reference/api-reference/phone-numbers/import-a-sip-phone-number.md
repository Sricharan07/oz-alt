> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Import a SIP phone number

POST https://api.smallest.ai/atoms/v1/product/import-phone-number
Content-Type: application/json

Bring your own SIP trunk by importing an existing phone number with its SIP termination URL.
Atoms creates both inbound and outbound SIP trunks so your number works for making and receiving calls through the platform.

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/phone-numbers/import-a-sip-phone-number

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /product/import-phone-number:
    post:
      operationId: import-a-sip-phone-number
      summary: Import a SIP phone number
      description: >
        Bring your own SIP trunk by importing an existing phone number with its
        SIP termination URL.

        Atoms creates both inbound and outbound SIP trunks so your number works
        for making and receiving calls through the platform.
      tags:
        - subpackage_phoneNumbers
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
          description: Phone number imported successfully
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/Phone
                  Numbers_importASipPhoneNumber_Response_200
        '400':
          description: Bad request — missing required fields or phone number already exists
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/ImportASipPhoneNumberRequestBadRequestError
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
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                phoneNumber:
                  type: string
                  description: Your existing phone number in E.164 format
                sipTerminationUrl:
                  type: string
                  description: >-
                    The SIP URI where calls should be routed to your
                    infrastructure
                name:
                  type: string
                  description: A friendly display name for this number
                sipUsername:
                  type: string
                  description: Username for SIP authentication (if your trunk requires it)
                sipPassword:
                  type: string
                  description: Password for SIP authentication (if your trunk requires it)
              required:
                - phoneNumber
                - sipTerminationUrl
servers:
  - url: https://api.smallest.ai/atoms/v1
components:
  schemas:
    ProductImportPhoneNumberPostResponsesContentApplicationJsonSchemaDataAttributes:
      type: object
      properties:
        name:
          type: string
          description: Display name for the number
        phoneNumber:
          type: string
          description: The imported phone number
        outboundSipTrunkId:
          type: string
          description: Identifier for the outbound SIP trunk created
        inboundSipTrunkId:
          type: string
          description: Identifier for the inbound SIP trunk created
      title: >-
        ProductImportPhoneNumberPostResponsesContentApplicationJsonSchemaDataAttributes
    ProductImportPhoneNumberPostResponsesContentApplicationJsonSchemaData:
      type: object
      properties:
        _id:
          type: string
          description: Unique identifier of the created product
        productType:
          type: string
          description: The type of product created
        isActive:
          type: boolean
          description: Whether the number is active and ready to use
        attributes:
          $ref: >-
            #/components/schemas/ProductImportPhoneNumberPostResponsesContentApplicationJsonSchemaDataAttributes
        agentId:
          type:
            - string
            - 'null'
          description: ID of the agent assigned to this number (null if unassigned)
        createdAt:
          type: string
          format: date-time
          description: Timestamp when the product was created
        updatedAt:
          type: string
          format: date-time
          description: Timestamp when the product was last updated
      title: ProductImportPhoneNumberPostResponsesContentApplicationJsonSchemaData
    Phone Numbers_importASipPhoneNumber_Response_200:
      type: object
      properties:
        status:
          type: boolean
        data:
          $ref: >-
            #/components/schemas/ProductImportPhoneNumberPostResponsesContentApplicationJsonSchemaData
      title: Phone Numbers_importASipPhoneNumber_Response_200
    ImportASipPhoneNumberRequestBadRequestError:
      type: object
      properties:
        status:
          type: boolean
        errors:
          type: array
          items:
            type: string
          description: List of validation error messages
      title: ImportASipPhoneNumberRequestBadRequestError
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

url = "https://api.smallest.ai/atoms/v1/product/import-phone-number"

payload = {
    "phoneNumber": "+14155552678",
    "sipTerminationUrl": "sip:trunk.voipprovider.net",
    "name": "Customer Service Line",
    "sipUsername": "cs_user_01",
    "sipPassword": "securePass123!"
}
headers = {
    "Authorization": "Bearer ",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.smallest.ai/atoms/v1/product/import-phone-number';
const options = {
  method: 'POST',
  headers: {Authorization: 'Bearer ', 'Content-Type': 'application/json'},
  body: '{"phoneNumber":"+14155552678","sipTerminationUrl":"sip:trunk.voipprovider.net","name":"Customer Service Line","sipUsername":"cs_user_01","sipPassword":"securePass123!"}'
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

	url := "https://api.smallest.ai/atoms/v1/product/import-phone-number"

	payload := strings.NewReader("{\n  \"phoneNumber\": \"+14155552678\",\n  \"sipTerminationUrl\": \"sip:trunk.voipprovider.net\",\n  \"name\": \"Customer Service Line\",\n  \"sipUsername\": \"cs_user_01\",\n  \"sipPassword\": \"securePass123!\"\n}")

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

url = URI("https://api.smallest.ai/atoms/v1/product/import-phone-number")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Bearer '
request["Content-Type"] = 'application/json'
request.body = "{\n  \"phoneNumber\": \"+14155552678\",\n  \"sipTerminationUrl\": \"sip:trunk.voipprovider.net\",\n  \"name\": \"Customer Service Line\",\n  \"sipUsername\": \"cs_user_01\",\n  \"sipPassword\": \"securePass123!\"\n}"

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse response = Unirest.post("https://api.smallest.ai/atoms/v1/product/import-phone-number")
  .header("Authorization", "Bearer ")
  .header("Content-Type", "application/json")
  .body("{\n  \"phoneNumber\": \"+14155552678\",\n  \"sipTerminationUrl\": \"sip:trunk.voipprovider.net\",\n  \"name\": \"Customer Service Line\",\n  \"sipUsername\": \"cs_user_01\",\n  \"sipPassword\": \"securePass123!\"\n}")
  .asString();
```

```php
request('POST', 'https://api.smallest.ai/atoms/v1/product/import-phone-number', [
  'body' => '{
  "phoneNumber": "+14155552678",
  "sipTerminationUrl": "sip:trunk.voipprovider.net",
  "name": "Customer Service Line",
  "sipUsername": "cs_user_01",
  "sipPassword": "securePass123!"
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

var client = new RestClient("https://api.smallest.ai/atoms/v1/product/import-phone-number");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Bearer ");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"phoneNumber\": \"+14155552678\",\n  \"sipTerminationUrl\": \"sip:trunk.voipprovider.net\",\n  \"name\": \"Customer Service Line\",\n  \"sipUsername\": \"cs_user_01\",\n  \"sipPassword\": \"securePass123!\"\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Bearer ",
  "Content-Type": "application/json"
]
let parameters = [
  "phoneNumber": "+14155552678",
  "sipTerminationUrl": "sip:trunk.voipprovider.net",
  "name": "Customer Service Line",
  "sipUsername": "cs_user_01",
  "sipPassword": "securePass123!"
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/product/import-phone-number")! as URL,
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
