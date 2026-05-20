> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Create agent from template

POST https://api.smallest.ai/atoms/v1/agent/from-template
Content-Type: application/json

We have created templates for some common use cases. You can use these templates to create an agent. For getting list of templates, you can use the /agent/template endpoint. It will give you the list of templates with their description and id. You can pass the id of the template in the request body to create an agent from the template.

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/agent-templates/create-agent-from-template

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /agent/from-template:
    post:
      operationId: create-agent-from-template
      summary: Create agent from template
      description: >-
        We have created templates for some common use cases. You can use these
        templates to create an agent. For getting list of templates, you can use
        the /agent/template endpoint. It will give you the list of templates
        with their description and id. You can pass the id of the template in
        the request body to create an agent from the template.
      tags:
        - subpackage_agentTemplates
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
                  #/components/schemas/Agent
                  Templates_createAgentFromTemplate_Response_200
        '400':
          description: Invalid input
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BadRequestErrorResponse'
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
              $ref: '#/components/schemas/CreateAgentFromTemplateRequest'
servers:
  - url: https://api.smallest.ai/atoms/v1
components:
  schemas:
    CreateAgentFromTemplateRequest:
      type: object
      properties:
        agentName:
          type: string
          description: Name of the agent
        agentDescription:
          type: string
          description: Description of the agent
        templateId:
          type: string
          description: >-
            ID of the template to use. You can get the list of templates with
            their description and id from the /agent/template endpoint.
      required:
        - agentName
        - templateId
      title: CreateAgentFromTemplateRequest
    Agent Templates_createAgentFromTemplate_Response_200:
      type: object
      properties:
        status:
          type: boolean
        data:
          type: string
          description: The ID of the created agent
      title: Agent Templates_createAgentFromTemplate_Response_200
    BadRequestErrorResponse:
      type: object
      properties:
        status:
          type: boolean
        errors:
          type: array
          items:
            type: string
      title: BadRequestErrorResponse
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
    await client.atoms.agentTemplates.createAgentFromTemplate({
        agentName: "string",
        templateId: "string",
    });
}
main();

```

```python
from smallest_ai import SmallestAI

client = SmallestAI(
    token="YOUR_TOKEN_HERE",
)

client.atoms.agent_templates.create_agent_from_template(
    agent_name="string",
    template_id="string",
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

	url := "https://api.smallest.ai/atoms/v1/agent/from-template"

	payload := strings.NewReader("{\n  \"agentName\": \"string\",\n  \"templateId\": \"string\"\n}")

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

url = URI("https://api.smallest.ai/atoms/v1/agent/from-template")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Bearer '
request["Content-Type"] = 'application/json'
request.body = "{\n  \"agentName\": \"string\",\n  \"templateId\": \"string\"\n}"

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse response = Unirest.post("https://api.smallest.ai/atoms/v1/agent/from-template")
  .header("Authorization", "Bearer ")
  .header("Content-Type", "application/json")
  .body("{\n  \"agentName\": \"string\",\n  \"templateId\": \"string\"\n}")
  .asString();
```

```php
request('POST', 'https://api.smallest.ai/atoms/v1/agent/from-template', [
  'body' => '{
  "agentName": "string",
  "templateId": "string"
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

var client = new RestClient("https://api.smallest.ai/atoms/v1/agent/from-template");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Bearer ");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"agentName\": \"string\",\n  \"templateId\": \"string\"\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Bearer ",
  "Content-Type": "application/json"
]
let parameters = [
  "agentName": "string",
  "templateId": "string"
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/agent/from-template")! as URL,
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
