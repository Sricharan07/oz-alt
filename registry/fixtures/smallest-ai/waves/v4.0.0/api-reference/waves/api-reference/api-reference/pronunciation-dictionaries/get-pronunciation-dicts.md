> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Get Pronunciation Dictionaries

GET https://api.smallest.ai/waves/v1/pronunciation-dicts

Retrieve all pronunciation dictionaries for the authenticated user

Reference: https://docs.smallest.ai/waves/api-reference/api-reference/pronunciation-dictionaries/get-pronunciation-dicts

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: waves-v4
  version: 1.0.0
paths:
  /waves/v1/pronunciation-dicts:
    get:
      operationId: get-pronunciation-dicts
      summary: List
      description: Retrieve all pronunciation dictionaries for the authenticated user
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
          description: List of pronunciation dictionaries
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/PronunciationDict'
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

```python Pronunciation Dictionaries_getPronunciationDicts_example
import requests

url = "https://api.smallest.ai/waves/v1/pronunciation-dicts"

headers = {"Authorization": "Bearer "}

response = requests.get(url, headers=headers)

print(response.json())
```

```javascript Pronunciation Dictionaries_getPronunciationDicts_example
const url = 'https://api.smallest.ai/waves/v1/pronunciation-dicts';
const options = {method: 'GET', headers: {Authorization: 'Bearer '}};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

```go Pronunciation Dictionaries_getPronunciationDicts_example
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://api.smallest.ai/waves/v1/pronunciation-dicts"

	req, _ := http.NewRequest("GET", url, nil)

	req.Header.Add("Authorization", "Bearer ")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby Pronunciation Dictionaries_getPronunciationDicts_example
require 'uri'
require 'net/http'

url = URI("https://api.smallest.ai/waves/v1/pronunciation-dicts")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["Authorization"] = 'Bearer '

response = http.request(request)
puts response.read_body
```

```java Pronunciation Dictionaries_getPronunciationDicts_example
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse response = Unirest.get("https://api.smallest.ai/waves/v1/pronunciation-dicts")
  .header("Authorization", "Bearer ")
  .asString();
```

```php Pronunciation Dictionaries_getPronunciationDicts_example
request('GET', 'https://api.smallest.ai/waves/v1/pronunciation-dicts', [
  'headers' => [
    'Authorization' => 'Bearer ',
  ],
]);

echo $response->getBody();
```

```csharp Pronunciation Dictionaries_getPronunciationDicts_example
using RestSharp;

var client = new RestClient("https://api.smallest.ai/waves/v1/pronunciation-dicts");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Bearer ");
IRestResponse response = client.Execute(request);
```

```swift Pronunciation Dictionaries_getPronunciationDicts_example
import Foundation

let headers = ["Authorization": "Bearer "]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/waves/v1/pronunciation-dicts")! as URL,
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
