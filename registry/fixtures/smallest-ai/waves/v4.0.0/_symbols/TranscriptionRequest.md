# TranscriptionRequest

**Kind:** type
**Signature:** `package main`
**Source:** https://docs.smallest.ai/waves/self-host/api-reference/examples

## Example

```go
package main

import (
    "bytes"
    "encoding/json"
    "fmt"
    "io/ioutil"
    "net/http"
    "os"
    "time"
)

type TranscriptionRequest struct {
    URL       string `json:"url"`
    Punctuate bool   `json:"punctuate,omitempty"`
    Language  string `json:"language,omitempty"`
}

type TranscriptionResult struct {
    RequestID  string  `json:"request_id"`
    Text       string  `json:"text"`
    Confidence float64 `json:"confidence"`
    Duration   float64 `json:"duration"`
}

type SmallestClient struct {
    APIUrl     string
    LicenseKey string
    HTTPClient *http.Client
}

func NewClient(apiURL, licenseKey string) *SmallestClient {
    return &SmallestClient{
        APIUrl:     apiURL,
        LicenseKey: licenseKey,
        HTTPClient: &http.Client{Timeout: 5 * time.Minute},
    }
}

func (c *SmallestClient) Transcribe(req TranscriptionRequest) (*TranscriptionResult, error) {
    jsonData, err := json.Marshal(req)
    if err != nil {
        return nil, err
    }

    httpReq, err := http.NewRequest("POST", c.APIUrl+"/v1/listen", bytes.NewBuffer(jsonData))
    if err != nil {
        return nil, err
    }

    httpReq.Header.Set("Authorization", "Token "+c.LicenseKey)
    httpReq.Header.Set("Content-Type", "application/json")

    resp, err := c.HTTPClient.Do(httpReq)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    if resp.StatusCode != http.StatusOK {
        body, _ := ioutil.ReadAll(resp.Body)
        return nil, fmt.Errorf("API error: %s", string(body))
    }

    var result TranscriptionResult
    if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
        return nil, err
    }

    return &result, nil
}

func main() {
    client := NewClient(
        "http://localhost:7100",
        os.Getenv("LICENSE_KEY"),
    )

    result, err := client.Transcribe(TranscriptionRequest{
        URL:       "https://example.com/audio.wav",
        Punctuate: true,
        Language:  "en",
    })

    if err != nil {
        fmt.Printf("Error: %v\n", err)
        return
    }

    fmt.Printf("Transcription: %s\n", result.Text)
    fmt.Printf("Confidence: %.2f\n", result.Confidence)
}
```
