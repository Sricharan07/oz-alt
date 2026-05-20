> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Submit a compliance application

POST https://api.smallest.ai/atoms/v1/compliance/applications
Content-Type: multipart/form-data

Submit a new compliance application with end-user details and supporting documents.
One application is allowed per organization per country per number type per user type.

The request uses `multipart/form-data` because documents are uploaded inline.
The `endUser` and `documents` fields are JSON strings embedded in the form data.

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/compliance/submit-a-compliance-application

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /compliance/applications:
    post:
      operationId: submit-a-compliance-application
      summary: Submit a compliance application
      description: >
        Submit a new compliance application with end-user details and supporting
        documents.

        One application is allowed per organization per country per number type
        per user type.

        The request uses `multipart/form-data` because documents are uploaded
        inline.

        The `endUser` and `documents` fields are JSON strings embedded in the
        form data.
      tags:
        - subpackage_compliance
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
        '201':
          description: Application submitted successfully
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/Compliance_submitAComplianceApplication_Response_201
        '400':
          description: >-
            Validation error (invalid JSON, file count mismatch, unsupported
            file type)
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
        '409':
          description: >-
            A compliance application already exists for this
            country/numberType/userType
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
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                countryIso:
                  type: string
                  description: ISO 3166-1 alpha-2 country code
                numberType:
                  $ref: >-
                    #/components/schemas/ComplianceApplicationsPostRequestBodyContentMultipartFormDataSchemaNumberType
                  description: The type of phone number
                userType:
                  $ref: >-
                    #/components/schemas/ComplianceApplicationsPostRequestBodyContentMultipartFormDataSchemaUserType
                  description: The type of end user
                endUser:
                  type: string
                  description: |
                    JSON string containing end-user details. Example:
                    ```json
                    {
                      "name": "Acme Corp",
                      "country": "IN"
                    }
                    ```
                documents:
                  type: string
                  description: >
                    JSON string containing an array of document metadata. Each
                    entry must have a

                    `documentTypeId` (from the requirements endpoint) and
                    optional `dataFields`.

                    Example:

                    ```json

                    [{"documentTypeId": "dt_123", "dataFields":
                    {"business_name": "Acme Corp"}}]

                    ```
                files:
                  type: array
                  items:
                    type: string
                    format: binary
                  description: >
                    Document files in the same order as the `documents` metadata
                    array.

                    Accepted formats: PDF, JPEG, PNG. Maximum 5 MB per file, up
                    to 10 files.
              required:
                - countryIso
                - numberType
                - userType
                - endUser
                - documents
                - files
servers:
  - url: https://api.smallest.ai/atoms/v1
components:
  schemas:
    ComplianceApplicationsPostRequestBodyContentMultipartFormDataSchemaNumberType:
      type: string
      enum:
        - local
        - mobile
        - tollfree
      description: The type of phone number
      title: >-
        ComplianceApplicationsPostRequestBodyContentMultipartFormDataSchemaNumberType
    ComplianceApplicationsPostRequestBodyContentMultipartFormDataSchemaUserType:
      type: string
      enum:
        - individual
        - business
      description: The type of end user
      title: >-
        ComplianceApplicationsPostRequestBodyContentMultipartFormDataSchemaUserType
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
    Compliance_submitAComplianceApplication_Response_201:
      type: object
      properties:
        status:
          type: boolean
        data:
          $ref: '#/components/schemas/ComplianceApplication'
      title: Compliance_submitAComplianceApplication_Response_201
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

url = "https://api.smallest.ai/atoms/v1/compliance/applications"

files = { "files": "open('passport_scan.pdf', 'rb')" }
payload = {
    "countryIso": "US",
    "numberType": "mobile",
    "userType": "individual",
    "endUser": "{\"name\": \"John Doe\", \"country\": \"US\"}",
    "documents": "[{\"documentTypeId\": \"dt_456\", \"dataFields\": {\"first_name\": \"John\", \"last_name\": \"Doe\"}}]"
}
headers = {"Authorization": "Bearer "}

response = requests.post(url, data=payload, files=files, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.smallest.ai/atoms/v1/compliance/applications';
const form = new FormData();
form.append('countryIso', 'US');
form.append('numberType', 'mobile');
form.append('userType', 'individual');
form.append('endUser', '{"name": "John Doe", "country": "US"}');
form.append('documents', '[{"documentTypeId": "dt_456", "dataFields": {"first_name": "John", "last_name": "Doe"}}]');
form.append('files', 'passport_scan.pdf');

const options = {method: 'POST', headers: {Authorization: 'Bearer '}};

options.body = form;

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

	url := "https://api.smallest.ai/atoms/v1/compliance/applications"

	payload := strings.NewReader("-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"countryIso\"\r\n\r\nUS\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"numberType\"\r\n\r\nmobile\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"userType\"\r\n\r\nindividual\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"endUser\"\r\n\r\n{\"name\": \"John Doe\", \"country\": \"US\"}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"documents\"\r\n\r\n[{\"documentTypeId\": \"dt_456\", \"dataFields\": {\"first_name\": \"John\", \"last_name\": \"Doe\"}}]\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"files\"; filename=\"passport_scan.pdf\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001--\r\n")

	req, _ := http.NewRequest("POST", url, payload)

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

url = URI("https://api.smallest.ai/atoms/v1/compliance/applications")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Bearer '
request.body = "-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"countryIso\"\r\n\r\nUS\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"numberType\"\r\n\r\nmobile\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"userType\"\r\n\r\nindividual\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"endUser\"\r\n\r\n{\"name\": \"John Doe\", \"country\": \"US\"}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"documents\"\r\n\r\n[{\"documentTypeId\": \"dt_456\", \"dataFields\": {\"first_name\": \"John\", \"last_name\": \"Doe\"}}]\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"files\"; filename=\"passport_scan.pdf\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001--\r\n"

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse response = Unirest.post("https://api.smallest.ai/atoms/v1/compliance/applications")
  .header("Authorization", "Bearer ")
  .body("-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"countryIso\"\r\n\r\nUS\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"numberType\"\r\n\r\nmobile\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"userType\"\r\n\r\nindividual\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"endUser\"\r\n\r\n{\"name\": \"John Doe\", \"country\": \"US\"}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"documents\"\r\n\r\n[{\"documentTypeId\": \"dt_456\", \"dataFields\": {\"first_name\": \"John\", \"last_name\": \"Doe\"}}]\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"files\"; filename=\"passport_scan.pdf\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001--\r\n")
  .asString();
```

```php
request('POST', 'https://api.smallest.ai/atoms/v1/compliance/applications', [
  'multipart' => [
    [
        'name' => 'countryIso',
        'contents' => 'US'
    ],
    [
        'name' => 'numberType',
        'contents' => 'mobile'
    ],
    [
        'name' => 'userType',
        'contents' => 'individual'
    ],
    [
        'name' => 'endUser',
        'contents' => '{"name": "John Doe", "country": "US"}'
    ],
    [
        'name' => 'documents',
        'contents' => '[{"documentTypeId": "dt_456", "dataFields": {"first_name": "John", "last_name": "Doe"}}]'
    ],
    [
        'name' => 'files',
        'filename' => 'passport_scan.pdf',
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

var client = new RestClient("https://api.smallest.ai/atoms/v1/compliance/applications");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Bearer ");
request.AddParameter("undefined", "-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"countryIso\"\r\n\r\nUS\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"numberType\"\r\n\r\nmobile\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"userType\"\r\n\r\nindividual\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"endUser\"\r\n\r\n{\"name\": \"John Doe\", \"country\": \"US\"}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"documents\"\r\n\r\n[{\"documentTypeId\": \"dt_456\", \"dataFields\": {\"first_name\": \"John\", \"last_name\": \"Doe\"}}]\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"files\"; filename=\"passport_scan.pdf\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001--\r\n", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Bearer "]
let parameters = [
  [
    "name": "countryIso",
    "value": "US"
  ],
  [
    "name": "numberType",
    "value": "mobile"
  ],
  [
    "name": "userType",
    "value": "individual"
  ],
  [
    "name": "endUser",
    "value": "{\"name\": \"John Doe\", \"country\": \"US\"}"
  ],
  [
    "name": "documents",
    "value": "[{\"documentTypeId\": \"dt_456\", \"dataFields\": {\"first_name\": \"John\", \"last_name\": \"Doe\"}}]"
  ],
  [
    "name": "files",
    "fileName": "passport_scan.pdf"
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

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/compliance/applications")! as URL,
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
