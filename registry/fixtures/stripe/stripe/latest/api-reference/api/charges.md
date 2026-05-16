# Charges

**Source:** https://docs.stripe.com/api/charges.md

# Charges

**Source:** https://docs.stripe.com/api/charges.md

# Charges

The `Charge` object represents a single attempt to move money into your Stripe account. PaymentIntent confirmation is the most common way to create Charges, but [Account Debits](https://docs.stripe.com/docs/connect/account-debits.md) may also create Charges. Some legacy payment flows create Charges directly, which is not recommended for new integrations.

## Endpoints

### Create a charge

- [POST /v1/charges](https://docs.stripe.com/api/charges/create.md)

### Update a charge

- [POST /v1/charges/:id](https://docs.stripe.com/api/charges/update.md)

### Retrieve a charge

- [GET /v1/charges/:id](https://docs.stripe.com/api/charges/retrieve.md)

### List all charges

- [GET /v1/charges](https://docs.stripe.com/api/charges/list.md)

### Capture a charge

- [POST /v1/charges/:id/capture](https://docs.stripe.com/api/charges/capture.md)

### Search charges

- [GET /v1/charges/search](https://docs.stripe.com/api/charges/search.md)

## Events

- `charge.captured`
Occurs whenever a previously uncaptured charge is captured.

- `charge.expired`
Occurs whenever an uncaptured charge expires.

- `charge.failed`
Occurs whenever a failed charge attempt occurs.

- `charge.pending`
Occurs whenever a pending charge is created.

- `charge.refunded`
Occurs whenever a charge is refunded, including partial refunds. Listen to `refund.created` for information about the refund.

- `charge.succeeded`
Occurs whenever a charge is successful.

- `charge.updated`
Occurs whenever a charge description or metadata is updated, or upon an asynchronous capture.
