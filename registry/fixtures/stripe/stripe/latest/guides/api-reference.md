# API Reference

**Source:** https://docs.stripe.com/api

Stripe API Reference

Find anything
/

Ask AI

Introduction

Authentication

Errors

Expanding Responses

Idempotent requests

Include-dependent response values (API v2)

Metadata

Pagination

Request IDs

Connected Accounts

Versioning

Core ResourcesAccountsv2

Account Linksv2

Account Tokensv2

Balance

Balance Transactions

Charges

Customers

Customer Session

Disputes

Events

Eventsv2

Event Destinationsv2

Files

File Links

Mandates

Payment Intents

Personsv2

Person Tokensv2

Setup Intents

Setup Attempts

Payouts

Refunds

Confirmation Token

Tokens

Payment MethodsPayment Methods

Payment Method Configurations

Payment Method Domains

Bank Accounts

Cash Balance

Cash Balance Transaction

Cards

Sources

ProductsProducts

Prices

Coupons

Promotion Code

Discounts

Tax Code

Tax Rate

Shipping Rates

Commerce
Agentic CommerceShared Payment Issued Token

Shared Payment Granted Token

CheckoutCheckout Sessions

Payment LinksPayment Link

BillingAlerts

Credit Balance Summary

Credit Balance Transaction

Credit Grant

Credit Note

Customer Balance Transaction

Customer Portal Configuration

Customer Portal Session

Invoices

Invoice Items

Invoice Line Item

Invoice Payment

Invoice Rendering Templates

Meters

Meter Events

Meter Event Adjustment

Meter Event Adjustmentsv2

Meter Event Streamsv2

Meter Event Summary

Meter Eventsv2

Plans

Quote

Subscriptions

Subscription Items

Subscription Schedule

Tax IDs

Test Clocks

CapitalFinancing Offer

Financing Summary

ConnectAccounts

Login Links

Account Links

Account Session

Application Fees

Application Fee Refunds

Capabilities

Country Specs

Balance Settings

External Bank Accounts

External Account Cards

Person

Top-ups

Transfers

Transfer Reversals

Secrets

Reserves
Fraud
Issuing
Terminal
Treasury
Payment Records
Account Evaluation
Entitlements
Sigma
Reporting
Financial Connections
Tax
Identity
Crypto
Climate
Forwarding
Privacy
Webhooks

API Reference
Ask about this section
Copy for LLM
View as Markdown

The Stripe API is organized around REST. Our API has predictable resource-oriented URLs, accepts form-encoded request bodies, returns JSON-encoded responses, and uses standard HTTP response codes, authentication, and verbs.
You can use the Stripe API in sandboxes without affecting your live data or interacting with banking networks. The API key that you use to authenticate the request determines whether the request runs in live mode or in a sandbox. Sandboxes support all v2 APIs. Test mode sandboxes support some v2 APIs.
The Stripe API doesn’t support bulk updates. You can work on only one object per request.
The Stripe API differs for every account as we release new versions and tailor functionality. Log in to see docs with your test key and data.
Was this section helpful?YesNo

Just getting started?
Check out our development quickstart guide.

Not a developer?
Use Stripe’s no-code options or apps from our partners to get started with Stripe and to do more with your Stripe account—no code required.

Base URL

https://api.stripe.com

Client Libraries
Ruby
Python
PHP
Java
Node.js
Go
.NET

By default, the Stripe API Docs demonstrate using curl to interact with the API over HTTP. Select one of our official client libraries to see examples in code.

Authentication
Ask about this section
Copy for LLM
View as Markdown

The Stripe API uses API keys to authenticate requests. You can view and manage your API keys in the Stripe Dashboard.
Test secret keys have the prefix sk_test_ and live mode secret keys have the prefix sk_live_. Alternatively, you can use restricted API keys for granular permissions.
Your API keys carry many privileges. Follow best practices to keep your keys safe. Don’t embed secret (or restricted) API keys in source code or client-side applications. Instead, use your server platform’s secrets vault to provide keys to your server-side applications. If your platform doesn’t offer a secrets vault, set your keys in environment variables.
Make all API requests over HTTPS. Calls made over plain HTTP fail. API requests without authentication also fail.
Was this section helpful?YesNo

Authenticated Request

curl https://api.stripe.com/v1/charges \
  -u sk_test_BQokikJ...2HlWgH4olfQ2sk_test_BQokikJOvBiI2HlWgH4olfQ2:
# The colon prevents curl from asking for a password.

Your API Key
A sample test API key is included in all the examples here, so you can test any example right away. Do not submit any personally identifiable information in requests made with this key.
To test requests using your account, replace the sample API key with your actual API key or sign in.

Errors
Ask about this section
Copy for LLM
View as Markdown

Stripe uses conventional HTTP response codes to indicate the success or failure of an API request. In general: Codes in the 2xx range indicate success. Codes in the 4xx range indicate an error that failed given the information provided (e.g., a required parameter was omitted, a charge failed, etc.). Codes in the 5xx range indicate an error with Stripe’s servers (these are rare).
Some 4xx errors that could be handled programmatically (e.g., a card is declined) include an error code that briefly explains the error reported.
Was this section helpful?YesNo

Attributes
codenullable string

For some errors that could be handled programmatically, a short string indicating the error code reported.

decline_codenullable string

For card errors resulting from a card issuer decline, a short string indicating the card issuer’s reason for the decline if they provide one.

messagenullable string

A human-readable message providing more details about the error. For card errors, these messages can be shown to your users.

paramnullable string

If the error is parameter-specific, the parameter related to the error. For example, you can use this to display a message near the correct form field.

payment_intentnullable object

The PaymentIntent object for errors returned on a request involving a PaymentIntent.

typeenum

The type of error returned. One of api_error, card_error, idempotency_error, or invalid_request_error
Possible enum values
api_error
card_error
idempotency_error
invalid_request_error

MoreExpand all

advice_codenullable string

chargenullable string

doc_urlnullable string

network_advice_codenullable string

network_decline_codenullable string

payment_methodnullable object

payment_method_typenullable string

request_log_urlnullable string

setup_intentnullable object

sourcenullable object

HTTP Status Code Summary
200OKEverything worked as expected.400Bad RequestThe request was unacceptable, often due to missing a required parameter.401UnauthorizedNo valid API key provided.402Request FailedThe parameters were valid but the request failed.403ForbiddenThe API key doesn’t have permissions to perform the request.404Not FoundThe requested resource doesn’t exist.409ConflictThe request conflicts with another request (perhaps due to using the same idempotent key).424External Dependency FailedThe request couldn’t be completed due to a failure in a dependency external to Stripe.429Too Many RequestsToo many requests hit the API too quickly. We recommend an exponential backoff of your requests.500, 502, 503, 504Server ErrorsSomething went wrong on Stripe’s end. (These are rare.)

Error Types
api_errorAPI errors cover any other type of problem (e.g., a temporary problem with Stripe’s servers), and are extremely uncommon.card_errorCard errors are the most common type of error you should expect to handle. They result when the user enters a card that can’t be charged for some reason.idempotency_errorIdempotency errors occur when an Idempotency-Key is re-used on a request that does not match the first request’s API endpoint and parameters.invalid_request_errorInvalid request errors arise when your request has invalid parameters.

Handling errors
Ask about this section
Copy for LLM
View as Markdown

Our Client libraries raise exceptions for many reasons, such as a failed charge, invalid parameters, authentication errors, and network unavailability. We recommend writing code that gracefully handles all possible API exceptions.
Related guide: Error Handling

# Select a client library to see examples of
# handling different kinds of errors.

Expanding Responses
Ask about this section
Copy for LLM
View as Markdown

Many objects allow you to request additional information as an expanded response by using the expand request parameter. This parameter is available on all API requests, and applies to the response of that request only. You can expand responses in two ways.
In many cases, an object contains the ID of a related object in its response properties. For example, a Charge might have an associated Customer ID. You can expand these objects in line with the expand request parameter. The expandable label in this documentation indicates ID fields that you can expand into objects.
Some available fields aren’t included in the responses by default, such as the number and cvc fields for the Issuing Card object. You can request these fields as an expanded response by using the expand request parameter.
You can expand recursively by specifying nested fields after a dot (.). For example, requesting payment_intent.customer on a charge expands the payment_intent property into a full PaymentIntent object, then expands the customer property on that payment intent into a full Customer object.
You can use the expand parameter on any endpoint that returns expandable fields, including list, create, and update endpoints.
Expansions on list requests start with the data property. For example, you can expand data.customers on a request to list charges and associated customers. Performing deep expansions on numerous list requests might result in slower processing times.
Expansions have a maximum depth of four levels (for example, the deepest expansion allowed when listing charges is data.payment_intent.customer.default_source).
You can expand multiple objects at the same time by identifying multiple items in the expand array.
Related guide: Expanding responses
Related video: Expand
Was this section helpful?YesNo

curl https://api.stripe.com/v1/charges/ch_3LmzzQ2eZvKYlo2C0XjzUzJV \
  -u sk_test_BQokikJ...2HlWgH4olfQ2sk_test_BQokikJOvBiI2HlWgH4olfQ2: \
  -d &quot;expand[]&quot;=customer \
  -d &quot;expand[]&quot;=&quot;payment_intent.customer&quot; \
  -G

Response

{
  &quot;id&quot;: &quot;ch_3LmzzQ2eZvKYlo2C0XjzUzJV&quot;,
  &quot;object&quot;: &quot;charge&quot;,
  &quot;customer&quot;: {
    &quot;id&quot;: &quot;cu_14HOpH2eZvKYlo2CxXIM7Pb2&quot;,
    &quot;object&quot;: &quot;customer&quot;,
    // ...
  },
  &quot;payment_intent&quot;: {
    &quot;id&quot;: &quot;pi_3MtwBwLkdIwHu7ix28a3tqPa&quot;,
    &quot;object&quot;: &quot;payment_intent&quot;,
    &quot;customer&quot;: {
      &quot;id&quot;: &quot;cus_NffrFeUfNV2Hib&quot;,
      &quot;object&quot;: &quot;customer&quot;,
      // ...
    },
    // ...
  },
  // ...
}
