# Authentication

**Source:** https://docs.stripe.com/api/authentication.md

# Authentication

**Source:** https://docs.stripe.com/api/authentication.md

# Authentication

The Stripe API uses [API keys](https://docs.stripe.com/keys.md) to authenticate requests. You can view and manage your API keys in [the Stripe Dashboard](https://dashboard.stripe.com/login?redirect=/apikeys).

Test secret keys have the prefix `sk_test_` and live mode secret keys have the prefix `sk_live_`. Alternatively, you can use [restricted API keys](https://docs.stripe.com/keys.md#limit-access) for granular permissions.

Your API keys carry many privileges. Follow [best practices](https://docs.stripe.com/keys-best-practices.md) to keep your keys safe. Don’t embed secret (or restricted) API keys in source code or client-side applications. Instead, use your server platform’s secrets vault to provide keys to your server-side applications. If your platform doesn’t offer a secrets vault, set your keys in environment variables.

The Stripe API authenticates requests using [HTTP Basic Auth](http://en.wikipedia.org/wiki/Basic_access_authentication). Provide your API key as the basic auth username value. You don’t need to provide a password.

If you need to authenticate using bearer auth (for example, for a cross-origin request), use `-H "Authorization: Bearer ,[object Object],"` instead of `-u ,[object Object]`.

Connect the CLI to your Stripe account by logging in to persist your secret key locally. See also [Log in to the CLI](https://docs.stripe.com/stripe-cli.md#login-account).

Use your API key by assigning it when creating [StripeClient](https://docs.stripe.com/sdks/server-side.md#stripeclient). The Ruby library will then automatically send this key in each request.

You can also set a per-request key with an option. This is often useful for Connect applications that use multiple API keys during the lifetime of a process. Methods on the returned object reuse the same API key.

Use your API key by assigning it when creating [StripeClient](https://docs.stripe.com/sdks/server-side.md#stripeclient). The Python library will then automatically send this key in each request.

You can also set a per-request key with an option. This is often useful for Connect applications that use multiple API keys during the lifetime of a process. Methods on the returned object reuse the same API key.

Use your API key by setting it when creating [StripeClient](https://docs.stripe.com/sdks/server-side.md#stripeclient). The PHP library will then automatically send this key in each request.

You can also set a per-request key with an option. This is often useful for Connect applications that use multiple API keys during the lifetime of a process. Methods on the returned object reuse the same API key.

Use your API key by passing it when creating [StripeClient](https://docs.stripe.com/sdks/server-side.md#stripeclient). The client then automatically sends this key in each request.

You can also set a per-request key with an option. This is often useful for Connect applications that use multiple API keys during the lifetime of a process.

Use your API key by setting it in the initial configuration of `stripe`. The Node.js library will then automatically send this key in each request.

You can also set a per-request key with an option. This is often useful for Connect applications that use multiple API keys during the lifetime of a process. Methods on the returned object reuse the same API key.

Use your API key by passing it when creating [StripeClient](https://docs.stripe.com/sdks/server-side.md#stripeclient). The Go library then automatically sends this key in each request.

You can also set a per-request key with an option. This is often useful for Connect applications that use multiple API keys during the lifetime of a process.

Use your API key by passing it when creating [StripeClient](https://docs.stripe.com/sdks/server-side.md#stripeclient). The client then automatically sends this key in each request.

You can also set a per-request key with an option. This is often useful for Connect applications that use multiple API keys during the lifetime of a process.

Make all API requests over [HTTPS](http://en.wikipedia.org/wiki/HTTP_Secure). Calls made over plain HTTP fail. API requests without authentication also fail.

```sh
curl https://api.stripe.com/v1/charges \
  -u sk_test_REDACTED:
# The colon prevents curl from asking for a password.
```

### Initialize StripeClient

```javascript
import Stripe from 'stripe';
// Test mode key; don't put live keys in code. See https://docs.stripe.com/keys-best-practices.
const stripeClient = new Stripe('sk_test_REDACTED');
```

### Per-Request API Key

```javascript
var charge = await stripeClient.charges.retrieve(
  'ch_3LiiC52eZvKYlo2C1da66ZSQ',
  {
    apiKey: 'sk_test_REDACTED'
  }
);
```

```plaintext
stripe login
```

### Initialize StripeClient

```ruby
require 'stripe'
# Test mode key; don't put live keys in code. See https://docs.stripe.com/keys-best-practices.
client = Stripe::StripeClient.new("sk_test_REDACTED")
```

### Per-Request API Key

```ruby
charge = client.v1.charges.retrieve(
  'ch_3P5pVZArEmbiH6tU1sgOWO6t',
  {},
  {
    api_key: 'sk_test_REDACTED'
  }
)
charge.capture() # Uses the same request specific API Key.
```

### Initialize StripeClient

```python
from stripe import StripeClient
# Test mode key; don't put live keys in code. See https://docs.stripe.com/keys-best-practices.
client = StripeClient("sk_test_REDACTED")
```

### Per-Request API Key

```python
charge = client.v1.charges.retrieve(
  "ch_3Ln3e92eZvKYlo2C0eUfv7bi",
  options={
    "api_key": "sk_test_REDACTED"
  }
)
charge.capture() # Uses the same request specific API Key.
```

### Initialize StripeClient

```php
// Test mode key; don't put live keys in code. See https://docs.stripe.com/keys-best-practices.
$stripe = new \Stripe\StripeClient("sk_test_REDACTED");
```

### Per-Request API Key

```php
$ch = $stripe->charges->retrieve(
  'ch_3Ln3fO2eZvKYlo2C1kqP3AMr',
  [],
  ['api_key' => 'sk_test_REDACTED']
);
$ch->capture(); // Uses the same API Key.
```

### Initialize StripeClient

```java
// Test mode key; don't put live keys in code. See https://docs.stripe.com/keys-best-practices.
StripeClient client = new StripeClient("sk_test_REDACTED");
```

### Per-Request API Key

```java
RequestOptions requestOptions = RequestOptions.builder()
  .setApiKey("sk_test_REDACTED")
  .build();

Charge charge = client.v1().charges().retrieve(
  "ch_3Ln3ga2eZvKYlo2C11iwHdxy",
  requestOptions,
);

```

### Initialize StripeClient

```go
// Test mode key; don't put live keys in code. See https://docs.stripe.com/keys-best-practices.
sc := stripe.NewClient("sk_test_REDACTED")
```

### Per-Request API Key

```go
sc := stripe.NewClient("sk_test_REDACTED")
params := &stripe.ChargeRetrieveParams{}
ch, err := sc.V1Charges.Retrieve(context.TODO(), "ch_3Ln3j02eZvKYlo2C0d5IZWuG", params)
```

### Initialize StripeClient

```dotnet
// Test mode key; don't put live keys in code. See https://docs.stripe.com/keys-best-practices.
var client = new StripeClient("sk_test_REDACTED");
```

### Per-Request API Key

```dotnet
var options = new RequestOptions
{
  ApiKey = "sk_test_REDACTED"
};
Charge charge = client.V1.Charges.Get(
  "ch_3Ln3kB2eZvKYlo2C1YRBr0Ll",
  null,
  options
);
```

## Your API Key

A sample test API key is included in all the examples here, so you can test any example right away. Do not submit any personally identifiable information in requests made with this key.

To test requests using your account, replace the sample API key with your actual API key or sign in.
