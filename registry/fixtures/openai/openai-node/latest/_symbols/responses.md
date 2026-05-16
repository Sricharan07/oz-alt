# responses

**Kind:** expected
**Signature:** `responses`
**Source:** https://raw.githubusercontent.com/openai/openai-node/master/README.md

## Example

```markdown
```ts
import OpenAI from 'jsr:@openai/openai';
```

## Usage

The full API of this library can be found in [api.md file](api.md) along with many [code examples](https://github.com/openai/openai-node/tree/master/examples).

The primary API for interacting with OpenAI models is the [Responses API](https://platform.openai.com/docs/api-reference/responses). You can generate text from the model with the code below.

```ts
import OpenAI from 'openai';

const client = new OpenAI({
  apiKey: process.env['OPENAI_API_KEY'], // This is the default and can be omitted
});
```
