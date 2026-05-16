# constructEvent

**Kind:** expected
**Signature:** `constructEvent`
**Source:** https://docs.stripe.com/webhooks/signature

## Example

```markdown
Resolve webhook signature verification errors
Learn how to fix a common error when listening to webhook events.

Ask about this page
Copy for LLM
View as MarkdownInstall skills

When processing webhook events, we recommend securing your endpoint by verifying that the event is coming from Stripe. To do this, use the Stripe-Signature header and call the constructEvent() function with three parameters:
requestBody: The request body string sent by Stripe.
signature: The Stripe-Signature header in the request sent by Stripe.
endpointSecret: The secret associated with your endpoint.
This function might look like this:

Select a languageRuby
Python
PHP
```
