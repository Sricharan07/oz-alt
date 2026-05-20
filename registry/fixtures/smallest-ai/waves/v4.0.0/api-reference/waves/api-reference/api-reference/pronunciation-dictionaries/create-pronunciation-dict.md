> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Create Pronunciation Dictionary

POST https://api.smallest.ai/waves/v1/pronunciation-dicts
Content-Type: application/json

Create a new pronunciation dictionary for the authenticated user

Reference: https://docs.smallest.ai/waves/api-reference/api-reference/pronunciation-dictionaries/create-pronunciation-dict

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: waves-v4
  version: 1.0.0
paths:
  /waves/v1/pronunciation-dicts:
    post:
      operationId: create-pronunciation-dict
      summary: Create
      description: Create a new pronunciation dictionary for the authenticated user
      tags:
        - subpackage_pronunciationDictionaries
      parameters:
        - name: Authorization
          in: header
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Successfully created pronunciation dictionary
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PronunciationDict'
        '400':
          description: Bad request - Invalid request body
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '401':
          description: Unauthorized - Invalid or missing authentication
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '500':
          description: Internal server error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreatePronunciationDictRequest'
servers:
  - url: https://api.smallest.ai
components:
  schemas:
    PronunciationItem:
      type: object
      properties:
        word:
          type: string
          description: The word to be pronounced
        pronunciation:
          type: string
          description: The phonetic pronunciation of the word
      required:
        - word
        - pronunciation
      title: PronunciationItem
    CreatePronunciationDictRequest:
      type: object
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/PronunciationItem'
          description: List of word-pronunciation pairs to create
      required:
        - items
      title: CreatePronunciationDictRequest
    PronunciationDict:
      type: object
      properties:
        id:
          type: string
          description: Unique identifier for the pronunciation dictionary
        items:
          type: array
          items:
            $ref: '#/components/schemas/PronunciationItem'
          description: List of word-pronunciation pairs
        createdAt:
          type: string
          format: date-time
          description: Timestamp when the dictionary was created
      required:
        - id
        - items
        - createdAt
      title: PronunciationDict
    ErrorResponseStatus:
      type: string
      enum:
        - error
      title: ErrorResponseStatus
    ErrorResponseError:
      type: object
      properties:
        message:
          type: string
        code:
          type: string
      title: ErrorResponseError
    ErrorResponse:
      type: object
      properties:
        status:
          $ref: '#/components/schemas/ErrorResponseStatus'
        error:
          $ref: '#/components/schemas/ErrorResponseError'
      title: ErrorResponse
  securitySchemes:
    BearerAuth:
      type: apiKey
      in: header
      name: Authorization

```

## SDK Code Examples

```python Pronunciation Dictionaries_createPronunciationDict_example
import requests

url = "https://api.smallest.ai/waves/v1/pronunciation-dicts"

payload = { "items": [
        {
            "word": "mysql",
            "pronunciation": "my-sequel"
        }
    ] }
headers = {
    "Authorization": "Bearer ",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

```javascript Pronunciation Dictionaries_createPronunciationDict_example
const url = 'https://api.smallest.ai/waves/v1/pronunciation-dicts';
const options = {
  method: 'POST',
  headers: {Authorization: 'Bearer ', 'Content-Type': 'application/json'},
  body: '{"items":[{"word":"mysql","pronunciation":"my-sequel"}]}'
};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

```go Pronunciation Dictionaries_createPronunciationDict_example
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.smallest.ai/waves/v1/pronunciation-dicts"

	payload := strings.NewReader("{\n  \"items\": [\n    {\n      \"word\": \"mysql\",\n      \"pronunciation\": \"my-sequel\"\n    }\n  ]\n}")

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

```ruby Pronunciation Dictionaries_createPronunciationDict_example
require 'uri'
require 'net/http'

url = URI("https://api.smallest.ai/waves/v1/pronunciation-dicts")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Bearer '
request["Content-Type"] = 'application/json'
request.body = "{\n  \"items\": [\n    {\n      \"word\": \"mysql\",\n      \"pronunciation\": \"my-sequel\"\n    }\n  ]\n}"

response = http.request(request)
puts response.read_body
```

```java Pronunciation Dictionaries_createPronunciationDict_example
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse response = Unirest.post("https://api.smallest.ai/waves/v1/pronunciation-dicts")
  .header("Authorization", "Bearer ")
  .header("Content-Type", "application/json")
  .body("{\n  \"items\": [\n    {\n      \"word\": \"mysql\",\n      \"pronunciation\": \"my-sequel\"\n    }\n  ]\n}")
  .asString();
```

```php Pronunciation Dictionaries_createPronunciationDict_example
request('POST', 'https://api.smallest.ai/waves/v1/pronunciation-dicts', [
  'body' => '{
  "items": [
    {
      "word": "mysql",
      "pronunciation": "my-sequel"
    }
  ]
}',
  'headers' => [
    'Authorization' => 'Bearer ',
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

```csharp Pronunciation Dictionaries_createPronunciationDict_example
using RestSharp;

var client = new RestClient("https://api.smallest.ai/waves/v1/pronunciation-dicts");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Bearer ");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"items\": [\n    {\n      \"word\": \"mysql\",\n      \"pronunciation\": \"my-sequel\"\n    }\n  ]\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift Pronunciation Dictionaries_createPronunciationDict_example
import Foundation

let headers = [
  "Authorization": "Bearer ",
  "Content-Type": "application/json"
]
let parameters = ["items": [
    [
      "word": "mysql",
      "pronunciation": "my-sequel"
    ]
  ]] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/waves/v1/pronunciation-dicts")! as URL,
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
