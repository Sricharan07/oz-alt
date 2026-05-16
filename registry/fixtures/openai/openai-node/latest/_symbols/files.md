# files

**Kind:** expected
**Signature:** `files`
**Source:** https://raw.githubusercontent.com/openai/openai-node/master/README.md

## Example

```markdown
```ts
import fs from 'fs';
import OpenAI, { toFile } from 'openai';

const client = new OpenAI();

// If you have access to Node `fs` we recommend using `fs.createReadStream()`:
await client.files.create({ file: fs.createReadStream('input.jsonl'), purpose: 'fine-tune' });

// Or if you have the web `File` API you can pass a `File` instance:
await client.files.create({ file: new File(['my bytes'], 'input.jsonl'), purpose: 'fine-tune' });

// You can also pass a `fetch` `Response`:
await client.files.create({
  file: await fetch('https://somesite/input.jsonl'),
  purpose: 'fine-tune',
```
