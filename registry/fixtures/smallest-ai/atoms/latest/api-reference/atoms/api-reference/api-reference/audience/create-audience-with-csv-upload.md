> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Create audience with CSV upload

POST https://api.smallest.ai/atoms/v1/audience
Content-Type: multipart/form-data

Create a new audience by uploading a CSV file containing phone numbers

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/audience/create-audience-with-csv-upload

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /audience:
    post:
      operationId: create-audience-with-csv-upload
      summary: Create audience with CSV upload
      description: Create a new audience by uploading a CSV file containing phone numbers
      tags:
        - subpackage_audience
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
          description: Audience created successfully
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/Audience_createAudienceWithCsvUpload_Response_200
        '400':
          description: Bad request
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/CreateAudienceWithCsvUploadRequestBadRequestError
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
          multipart/form-data:
            schema:
              type: object
              properties:
                name:
                  type: string
                  description: The name of the audience
                description:
                  type: string
                  description: Optional description of the audience
                phoneNumberColumnName:
                  type: string
                  description: >-
                    The name of the column in the CSV that contains phone
                    numbers
                identifierColumnName:
                  type: string
                  description: >-
                    The name of the column in the CSV that contains identifiers
                    (e.g., names)
                file:
                  type: string
                  format: binary
                  description: CSV file containing phone numbers and identifiers (max 5MB)
              required:
                - name
                - phoneNumberColumnName
                - identifierColumnName
                - file
servers:
  - url: https://api.smallest.ai/atoms/v1
components:
  schemas:
    AudiencePostResponsesContentApplicationJsonSchemaData:
      type: object
      properties:
        _id:
          type: string
          description: The unique identifier for the audience
        name:
          type: string
          description: The name of the audience
        description:
          type: string
          description: The description of the audience
        phoneNumberColumnName:
          type: string
          description: The name of the column in the CSV that contains phone numbers
        identifierColumnName:
          type: string
          description: The name of the column in the CSV that contains identifiers
        organization:
          type: string
          description: The organization ID
        createdBy:
          type: string
          description: The user ID who created the audience
        createdAt:
          type: string
          format: date-time
          description: The date and time when the audience was created
        updatedAt:
          type: string
          format: date-time
          description: The date and time when the audience was last updated
      title: AudiencePostResponsesContentApplicationJsonSchemaData
    Audience_createAudienceWithCsvUpload_Response_200:
      type: object
      properties:
        status:
          type: boolean
        data:
          $ref: >-
            #/components/schemas/AudiencePostResponsesContentApplicationJsonSchemaData
      title: Audience_createAudienceWithCsvUpload_Response_200
    CreateAudienceWithCsvUploadRequestBadRequestError:
      type: object
      properties:
        status:
          type: boolean
        errors:
          type: array
          items:
            type: string
      title: CreateAudienceWithCsvUploadRequestBadRequestError
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
    await client.atoms.audience.createAudienceWithCsvUpload(, {});
}
main();

```

```python
from smallest_ai import SmallestAI

client = SmallestAI(
    token="YOUR_TOKEN_HERE",
)

client.atoms.audience.create_audience_with_csv_upload(
    file="example_file",
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

	url := "https://api.smallest.ai/atoms/v1/audience"

	payload := strings.NewReader("-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"name\"\r\n\r\ntest_audience\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"description\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"phoneNumberColumnName\"\r\n\r\nphoneNumber\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"identifierColumnName\"\r\n\r\nName\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"file\"; filename=\"audience_template.csv\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001--\r\n")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("Authorization", "Bearer ")
	req.Header.Add("Content-Type", "multipart/form-data; boundary=---011000010111000001101001")

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

url = URI("https://api.smallest.ai/atoms/v1/audience")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Bearer '
request["Content-Type"] = 'multipart/form-data; boundary=---011000010111000001101001'
request.body = "-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"name\"\r\n\r\ntest_audience\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"description\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"phoneNumberColumnName\"\r\n\r\nphoneNumber\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"identifierColumnName\"\r\n\r\nName\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"file\"; filename=\"audience_template.csv\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001--\r\n"

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse response = Unirest.post("https://api.smallest.ai/atoms/v1/audience")
  .header("Authorization", "Bearer ")
  .header("Content-Type", "multipart/form-data; boundary=---011000010111000001101001")
  .body("-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"name\"\r\n\r\ntest_audience\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"description\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"phoneNumberColumnName\"\r\n\r\nphoneNumber\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"identifierColumnName\"\r\n\r\nName\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"file\"; filename=\"audience_template.csv\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001--\r\n")
  .asString();
```

```php
request('POST', 'https://api.smallest.ai/atoms/v1/audience', [
  'multipart' => [
    [
        'name' => 'name',
        'contents' => 'test_audience'
    ],
    [
        'name' => 'phoneNumberColumnName',
        'contents' => 'phoneNumber'
    ],
    [
        'name' => 'identifierColumnName',
        'contents' => 'Name'
    ],
    [
        'name' => 'file',
        'filename' => 'audience_template.csv',
        'contents' => null
    ]
  ]
  'headers' => [
    'Authorization' => 'Bearer ',
  ],
]);

echo $response->getBody();
```

```csharp
using RestSharp;

var client = new RestClient("https://api.smallest.ai/atoms/v1/audience");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Bearer ");
request.AddParameter("multipart/form-data; boundary=---011000010111000001101001", "-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"name\"\r\n\r\ntest_audience\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"description\"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"phoneNumberColumnName\"\r\n\r\nphoneNumber\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"identifierColumnName\"\r\n\r\nName\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"file\"; filename=\"audience_template.csv\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001--\r\n", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Bearer ",
  "Content-Type": "multipart/form-data; boundary=---011000010111000001101001"
]
let parameters = [
  [
    "name": "name",
    "value": "test_audience"
  ],
  [
    "name": "description",
    "value":
  ],
  [
    "name": "phoneNumberColumnName",
    "value": "phoneNumber"
  ],
  [
    "name": "identifierColumnName",
    "value": "Name"
  ],
  [
    "name": "file",
    "fileName": "audience_template.csv"
  ]
]

let boundary = "---011000010111000001101001"

var body = ""
var error: NSError? = nil
for param in parameters {
  let paramName = param["name"]!
  body += "--\(boundary)\r\n"
  body += "Content-Disposition:form-data; name=\"\(paramName)\""
  if let filename = param["fileName"] {
    let contentType = param["content-type"]!
    let fileContent = String(contentsOfFile: filename, encoding: String.Encoding.utf8)
    if (error != nil) {
      print(error as Any)
    }
    body += "; filename=\"\(filename)\"\r\n"
    body += "Content-Type: \(contentType)\r\n\r\n"
    body += fileContent
  } else if let paramValue = param["value"] {
    body += "\r\n\r\n\(paramValue)"
  }
}

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/audience")! as URL,
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
