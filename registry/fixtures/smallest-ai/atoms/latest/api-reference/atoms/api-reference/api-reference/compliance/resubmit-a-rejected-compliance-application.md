> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Resubmit a rejected compliance application

PATCH https://api.smallest.ai/atoms/v1/compliance/applications/{id}
Content-Type: multipart/form-data

Resubmit a previously rejected compliance application with corrected documents.
Only applications in `rejected` status can be resubmitted. All documents must be
re-uploaded — partial updates are not supported.

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/compliance/resubmit-a-rejected-compliance-application

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /compliance/applications/{id}:
    patch:
      operationId: resubmit-a-rejected-compliance-application
      summary: Resubmit a rejected compliance application
      description: >
        Resubmit a previously rejected compliance application with corrected
        documents.

        Only applications in `rejected` status can be resubmitted. All documents
        must be

        re-uploaded — partial updates are not supported.
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
          description: Application resubmitted successfully
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/Compliance_resubmitARejectedComplianceApplication_Response_200
        '400':
          description: Only rejected applications can be resubmitted, or validation error
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
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                documents:
                  type: string
                  description: >
                    JSON string containing an array of document metadata. Same
                    format as

                    the create endpoint.
                files:
                  type: array
                  items:
                    type: string
                    format: binary
                  description: >
                    Replacement document files. Must match the length of the
                    `documents` array.

                    Accepted formats: PDF, JPEG, PNG. Maximum 5 MB per file.
              required:
                - documents
                - files
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
    Compliance_resubmitARejectedComplianceApplication_Response_200:
      type: object
      properties:
        status:
          type: boolean
        data:
          $ref: '#/components/schemas/ComplianceApplication'
      title: Compliance_resubmitARejectedComplianceApplication_Response_200
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

url = "https://api.smallest.ai/atoms/v1/compliance/applications/id"

files = { "files": "open('acme_corporation_tax_id.pdf', 'rb')" }
payload = { "documents": "[{\"documentTypeId\": \"dt_456\", \"dataFields\": {\"business_name\": \"Acme Corporation\"}}, {\"documentTypeId\": \"dt_789\", \"dataFields\": {\"tax_id\": \"123-45-6789\"}}]" }
headers = {"Authorization": "Bearer "}

response = requests.patch(url, data=payload, files=files, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.smallest.ai/atoms/v1/compliance/applications/id';
const form = new FormData();
form.append('documents', '[{"documentTypeId": "dt_456", "dataFields": {"business_name": "Acme Corporation"}}, {"documentTypeId": "dt_789", "dataFields": {"tax_id": "123-45-6789"}}]');
form.append('files', 'acme_corporation_certificate.pdf');
form.append('files', 'acme_corporation_tax_id.pdf');

const options = {method: 'PATCH', headers: {Authorization: 'Bearer '}};

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

	url := "https://api.smallest.ai/atoms/v1/compliance/applications/id"

	payload := strings.NewReader("-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"documents\"\r\n\r\n[{\"documentTypeId\": \"dt_456\", \"dataFields\": {\"business_name\": \"Acme Corporation\"}}, {\"documentTypeId\": \"dt_789\", \"dataFields\": {\"tax_id\": \"123-45-6789\"}}]\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"files\"; filename=\"acme_corporation_certificate.pdf\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"files\"; filename=\"acme_corporation_tax_id.pdf\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001--\r\n")

	req, _ := http.NewRequest("PATCH", url, payload)

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

url = URI("https://api.smallest.ai/atoms/v1/compliance/applications/id")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Patch.new(url)
request["Authorization"] = 'Bearer '
request.body = "-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"documents\"\r\n\r\n[{\"documentTypeId\": \"dt_456\", \"dataFields\": {\"business_name\": \"Acme Corporation\"}}, {\"documentTypeId\": \"dt_789\", \"dataFields\": {\"tax_id\": \"123-45-6789\"}}]\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"files\"; filename=\"acme_corporation_certificate.pdf\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"files\"; filename=\"acme_corporation_tax_id.pdf\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001--\r\n"

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse response = Unirest.patch("https://api.smallest.ai/atoms/v1/compliance/applications/id")
  .header("Authorization", "Bearer ")
  .body("-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"documents\"\r\n\r\n[{\"documentTypeId\": \"dt_456\", \"dataFields\": {\"business_name\": \"Acme Corporation\"}}, {\"documentTypeId\": \"dt_789\", \"dataFields\": {\"tax_id\": \"123-45-6789\"}}]\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"files\"; filename=\"acme_corporation_certificate.pdf\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"files\"; filename=\"acme_corporation_tax_id.pdf\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001--\r\n")
  .asString();
```

```php
request('PATCH', 'https://api.smallest.ai/atoms/v1/compliance/applications/id', [
  'multipart' => [
    [
        'name' => 'documents',
        'contents' => '[{"documentTypeId": "dt_456", "dataFields": {"business_name": "Acme Corporation"}}, {"documentTypeId": "dt_789", "dataFields": {"tax_id": "123-45-6789"}}]'
    ],
    [
        'name' => 'files',
        'filename' => 'acme_corporation_certificate.pdf',
        'contents' => null
    ],
    [
        'name' => 'files',
        'filename' => 'acme_corporation_tax_id.pdf',
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

var client = new RestClient("https://api.smallest.ai/atoms/v1/compliance/applications/id");
var request = new RestRequest(Method.PATCH);
request.AddHeader("Authorization", "Bearer ");
request.AddParameter("undefined", "-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"documents\"\r\n\r\n[{\"documentTypeId\": \"dt_456\", \"dataFields\": {\"business_name\": \"Acme Corporation\"}}, {\"documentTypeId\": \"dt_789\", \"dataFields\": {\"tax_id\": \"123-45-6789\"}}]\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"files\"; filename=\"acme_corporation_certificate.pdf\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"files\"; filename=\"acme_corporation_tax_id.pdf\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001--\r\n", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Bearer "]
let parameters = [
  [
    "name": "documents",
    "value": "[{\"documentTypeId\": \"dt_456\", \"dataFields\": {\"business_name\": \"Acme Corporation\"}}, {\"documentTypeId\": \"dt_789\", \"dataFields\": {\"tax_id\": \"123-45-6789\"}}]"
  ],
  [
    "name": "files",
    "fileName": "acme_corporation_certificate.pdf"
  ],
  [
    "name": "files",
    "fileName": "acme_corporation_tax_id.pdf"
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

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/compliance/applications/id")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "PATCH"
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
