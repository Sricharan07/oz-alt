# TranscriptionOptions

**Kind:** type
**Signature:** `import axios, { AxiosInstance } from 'axios';`
**Source:** https://docs.smallest.ai/waves/self-host/api-reference/examples

## Example

```typescript
import axios, { AxiosInstance } from 'axios';

interface TranscriptionOptions {
  url?: string;
  file?: File;
  language?: string;
  punctuate?: boolean;
  diarize?: boolean;
  timestamps?: boolean;
  callback_url?: string;
}

interface TranscriptionResult {
  request_id: string;
  text: string;
  confidence: number;
  duration: number;
  language: string;
  words?: Array;
}

class SmallestClient {
  private client: AxiosInstance;

  constructor(apiUrl: string, licenseKey: string) {
    this.client = axios.create({
      baseURL: apiUrl,
      headers: {
        'Authorization': `Token ${licenseKey}`,
        'Content-Type': 'application/json'
      },
      timeout: 300000
    });
  }

  async transcribe(options: TranscriptionOptions): Promise {
    const response = await this.client.post('/v1/listen', options);
    return response.data;
  }

  async health(): Promise {
    const response = await this.client.get('/health');
    return response.data;
  }
}

const client = new SmallestClient(
  process.env.API_URL || 'http://localhost:7100',
  process.env.LICENSE_KEY!
);

async function main() {
  const result = await client.transcribe({
    url: 'https://example.com/audio.wav',
    punctuate: true,
    timestamps: true
  });

  console.log(result.text);
}

main();
```
