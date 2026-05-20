> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Search audience members

GET https://api.smallest.ai/atoms/v1/audience/{id}/members/search

Search for members within a specific audience using flexible search parameters. Users can only search members of audiences they created.

**Search Types:**
- **General Search** (`query`): Searches across all fields in the audience member data
- **Field-Specific Search**: Use any field name as a parameter (e.g., `firstName=john`, `phoneNumber=123456`, `email=test@example.com`)

**Examples:**
- `?query=john` - General search across all fields
- `?firstName=john` - Search specifically in firstName field
- `?phoneNumber=555-1234` - Search specifically in phoneNumber field
- `?firstName=john&lastName=doe` - Search for members matching both criteria

**Note:** When using phoneNumber field, do not use quotes around the phone number. You can use either a general search OR field-specific searches, but not both simultaneously.

Reference: https://docs.smallest.ai/atoms/api-reference/api-reference/audience/search-audience-members

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: atoms
  version: 1.0.0
paths:
  /audience/{id}/members/search:
    get:
      operationId: search-audience-members
      summary: Search audience members
      description: >
        Search for members within a specific audience using flexible search
        parameters. Users can only search members of audiences they created.

        **Search Types:**

        - **General Search** (`query`): Searches across all fields in the
        audience member data

        - **Field-Specific Search**: Use any field name as a parameter (e.g.,
        `firstName=john`, `phoneNumber=123456`, `email=test@example.com`)

        **Examples:**

        - `?query=john` - General search across all fields

        - `?firstName=john` - Search specifically in firstName field

        - `?phoneNumber=555-1234` - Search specifically in phoneNumber field

        - `?firstName=john&lastName=doe` - Search for members matching both
        criteria

        **Note:** When using phoneNumber field, do not use quotes around the
        phone number. You can use either a general search OR field-specific
        searches, but not both simultaneously.
      tags:
        - subpackage_audience
      parameters:
        - name: id
          in: path
          description: The unique identifier of the audience
          required: true
          schema:
            type: string
        - name: query
          in: query
          description: >-
            General search term that searches across all fields in audience
            member data
          required: false
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
          description: Search results returned successfully
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/Audience_searchAudienceMembers_Response_200
        '400':
          description: Bad request
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/SearchAudienceMembersRequestBadRequestError
        '500':
          description: Internal server error
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/SearchAudienceMembersRequestInternalServerError
servers:
  - url: https://api.smallest.ai/atoms/v1
components:
  schemas:
    AudienceIdMembersSearchGetResponsesContentApplicationJsonSchemaDataMembersItemsData:
      type: object
      properties: {}
      description: Dynamic data from CSV, structure depends on uploaded file
      title: >-
        AudienceIdMembersSearchGetResponsesContentApplicationJsonSchemaDataMembersItemsData
    AudienceIdMembersSearchGetResponsesContentApplicationJsonSchemaDataMembersItems:
      type: object
      properties:
        _id:
          type: string
          description: The unique identifier for the audience member
        data:
          $ref: >-
            #/components/schemas/AudienceIdMembersSearchGetResponsesContentApplicationJsonSchemaDataMembersItemsData
          description: Dynamic data from CSV, structure depends on uploaded file
      title: >-
        AudienceIdMembersSearchGetResponsesContentApplicationJsonSchemaDataMembersItems
    AudienceIdMembersSearchGetResponsesContentApplicationJsonSchemaDataSearchInfoSearchType:
      type: string
      enum:
        - general
        - field
      description: The type of search performed
      title: >-
        AudienceIdMembersSearchGetResponsesContentApplicationJsonSchemaDataSearchInfoSearchType
    AudienceIdMembersSearchGetResponsesContentApplicationJsonSchemaDataSearchInfo:
      type: object
      properties:
        searchType:
          $ref: >-
            #/components/schemas/AudienceIdMembersSearchGetResponsesContentApplicationJsonSchemaDataSearchInfoSearchType
          description: The type of search performed
        searchTerm:
          type: string
          description: The search term(s) used
        searchFields:
          type: array
          items:
            type: string
          description: The specific fields searched (for field-specific searches)
        totalResults:
          type: integer
          description: The number of results returned
      description: Information about the search performed
      title: >-
        AudienceIdMembersSearchGetResponsesContentApplicationJsonSchemaDataSearchInfo
    AudienceIdMembersSearchGetResponsesContentApplicationJsonSchemaData:
      type: object
      properties:
        members:
          type: array
          items:
            $ref: >-
              #/components/schemas/AudienceIdMembersSearchGetResponsesContentApplicationJsonSchemaDataMembersItems
        searchInfo:
          $ref: >-
            #/components/schemas/AudienceIdMembersSearchGetResponsesContentApplicationJsonSchemaDataSearchInfo
          description: Information about the search performed
      title: AudienceIdMembersSearchGetResponsesContentApplicationJsonSchemaData
    Audience_searchAudienceMembers_Response_200:
      type: object
      properties:
        status:
          type: boolean
        data:
          $ref: >-
            #/components/schemas/AudienceIdMembersSearchGetResponsesContentApplicationJsonSchemaData
      title: Audience_searchAudienceMembers_Response_200
    SearchAudienceMembersRequestBadRequestError:
      type: object
      properties:
        status:
          type: boolean
        errors:
          type: array
          items:
            type: string
      title: SearchAudienceMembersRequestBadRequestError
    SearchAudienceMembersRequestInternalServerError:
      type: object
      properties:
        status:
          type: boolean
        errors:
          type: array
          items:
            type: string
      title: SearchAudienceMembersRequestInternalServerError
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
    await client.atoms.audience.searchAudienceMembers("60d0fe4f5311236168a109ca", {});
}
main();

```

```python
from smallest_ai import SmallestAI

client = SmallestAI(
    token="YOUR_TOKEN_HERE",
)

client.atoms.audience.search_audience_members(
    id="60d0fe4f5311236168a109ca",
)

```

```go
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://api.smallest.ai/atoms/v1/audience/60d0fe4f5311236168a109ca/members/search"

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

url = URI("https://api.smallest.ai/atoms/v1/audience/60d0fe4f5311236168a109ca/members/search")

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

HttpResponse response = Unirest.get("https://api.smallest.ai/atoms/v1/audience/60d0fe4f5311236168a109ca/members/search")
  .header("Authorization", "Bearer ")
  .asString();
```

```php
request('GET', 'https://api.smallest.ai/atoms/v1/audience/60d0fe4f5311236168a109ca/members/search', [
  'headers' => [
    'Authorization' => 'Bearer ',
  ],
]);

echo $response->getBody();
```

```csharp
using RestSharp;

var client = new RestClient("https://api.smallest.ai/atoms/v1/audience/60d0fe4f5311236168a109ca/members/search");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Bearer ");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Bearer "]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/atoms/v1/audience/60d0fe4f5311236168a109ca/members/search")! as URL,
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
