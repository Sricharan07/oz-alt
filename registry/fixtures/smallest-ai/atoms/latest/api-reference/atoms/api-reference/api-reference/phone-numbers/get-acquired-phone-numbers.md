> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Get acquired phone numbers

GET https://api.smallest.ai/atoms/v1/product/phone-numbers

Retrieve all acquired phone numbers for the organization

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/phone-numbers/get-acquired-phone-numbers

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /product/phone-numbers:
    get:
      operationId: get-acquired-phone-numbers
      summary: Get acquired phone numbers
      description: Retrieve all acquired phone numbers for the organization
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
          description: Successful response
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/Phone
                  Numbers_getAcquiredPhoneNumbers_Response_200
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
    ProductPhoneNumbersGetResponsesContentApplicationJsonSchemaDataItemsAttributes:
      type: object
      properties:
        provider:
          type: string
          description: The telephony provider
        phoneNumber:
          type: string
          description: The actual phone number
      description: Additional attributes of the phone number
      title: >-
        ProductPhoneNumbersGetResponsesContentApplicationJsonSchemaDataItemsAttributes
    ProductPhoneNumbersGetResponsesContentApplicationJsonSchemaDataItems:
      type: object
      properties:
        _id:
          type: string
          description: The unique identifier for the phone number
        isActive:
          type: boolean
          description: Whether the phone number is active
        attributes:
          $ref: >-
            #/components/schemas/ProductPhoneNumbersGetResponsesContentApplicationJsonSchemaDataItemsAttributes
          description: Additional attributes of the phone number
        createdAt:
          type: string
          format: date-time
          description: The date and time when the phone number was created
        updatedAt:
          type: string
          format: date-time
          description: The date and time when the phone number was last updated
      title: ProductPhoneNumbersGetResponsesContentApplicationJsonSchemaDataItems
    Phone Numbers_getAcquiredPhoneNumbers_Response_200:
      type: object
      properties:
        status:
          type: boolean
        data:
          type: array
          items:
            $ref: >-
              #/components/schemas/ProductPhoneNumbersGetResponsesContentApplicationJsonSchemaDataItems
      title: Phone Numbers_getAcquiredPhoneNumbers_Response_200
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
    await client.atoms.phoneNumbers.getAcquiredPhoneNumbers();
}
main();

```

```python
from smallest_ai import SmallestAI

client = SmallestAI(
    token="YOUR_TOKEN_HERE",
)

client.atoms.phone_numbers.get_acquired_phone_numbers()

```

```go
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://api.smallest.ai/atoms/v1/product/phone-numbers"

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

url = URI("https://api.smallest.ai/atoms/v1/product/phone-numbers")

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

HttpResponse response = Unirest.get("https://api.smallest.ai/atoms/v1/product/phone-numbers")
  .header("Authorization", "Bearer ")
  .asString();
```

```php
request('GET', 'https://api.smallest.ai/atoms/v1/product/phone-numbers', [
  'headers' => [
    'Authorization' => 'Bearer ',
  ],
]);

echo $response->getBody();
```

```csharp
using RestSharp;

var client = new RestClient("https://api.smallest.ai/atoms/v1/product/phone-numbers");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Bearer ");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Bearer "]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/product/phone-numbers")! as URL,
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
