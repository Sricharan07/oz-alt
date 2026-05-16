# webhook

**Kind:** function
**Signature:** `import { headers } from 'next/headers';`
**Source:** https://raw.githubusercontent.com/openai/openai-node/master/README.md

## Example

```ts
import { headers } from 'next/headers';
import OpenAI from 'openai';

const client = new OpenAI({
  webhookSecret: process.env.OPENAI_WEBHOOK_SECRET, // env var used by default; explicit here.
});

export async function webhook(request: Request) {
  const headersList = headers();
  const body = await request.text();

  try {
    const event = client.webhooks.unwrap(body, headersList);

    switch (event.type) {
      case 'response.completed':
        console.log('Response completed:', event.data);
        break;
      case 'response.failed':
        console.log('Response failed:', event.data);
        break;
      default:
        console.log('Unhandled event type:', event.type);
    }

    return Response.json({ message: 'ok' });
  } catch (error) {
    console.error('Invalid webhook signature:', error);
    return new Response('Invalid signature', { status: 400 });
  }
}
```
