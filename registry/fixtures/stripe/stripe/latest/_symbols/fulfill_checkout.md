# fulfill_checkout

**Kind:** function
**Signature:** `def fulfill_checkout(session_id)`
**Source:** https://docs.stripe.com/checkout/fulfillment.md

## Example

```ruby
def fulfill_checkout(session_id)
  # Don't put any keys in code. See https://docs.stripe.com/keys-best-practices.
  # Find your keys at https://dashboard.stripe.com/apikeys.
  client = Stripe::StripeClient.new('<<YOUR_SECRET_KEY>>')

  puts "Fullfilling Checkout Session #{session_id}"

  # TODO: Make this function safe to run multiple times,
  # even concurrently, with the same session ID

  # TODO: Make sure fulfillment hasn't already been
  # performed for this Checkout Session

  # Retrieve the Checkout Session from the API with line_items expanded
  checkout_session = client.v1.checkout.sessions.retrieve(
    session_id,
    {expand: ['line_items']},
  )

  # Check the Checkout Session's payment_status property
  # to determine if fulfillment should be performed
  if checkout_session.payment_status != 'unpaid'
    # TODO: Perform fulfillment of the line items

    # TODO: Record/save fulfillment status for this
    # Checkout Session
  end
end
```
