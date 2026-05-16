# API v2 overview

**Source:** https://docs.stripe.com/api-v2-overview

API v2 overview | Stripe Documentation

          Skip to content

API v2

Create account or Sign in

Search

/Ask AI
Create accountSign in

Get started

Payments

Revenue

Platforms and marketplaces

Money management

Developer resources

APIs & SDKsHelp

OverviewVersioning
Changelog

Upgrade your API versionUpgrade your SDK version

Essentials
SDKs

APIOverview
API v2Include-dependent response values v2
Represent customers using Account objects

Rate limits
Authentication
API keys

Specify request context
Domains and IP addresses
Make requests
Expand responses

Pagination
Search objects
Localize content
Testing and data
Metadata

Test your application
Error handling
Handle errors

Error codes

Testing

Stripe CLI

Sample projects

Tools
Stripe Dashboard

Workbench

Developers Dashboard

Stripe for Visual Studio CodeTerraform

Stripe Discord serverFeatures
Workflows

Batch jobs

Event destinations

Stripe health alertsStripe SignalsFile uploadsAI solutions
Agent toolkit

Model Context ProtocolBuild agentic AI SaaS Billing workflowsSecurity and privacy
Security

Activity logsStripebot web crawlerPrivacy

Extend Stripe
OverviewBuild Stripe apps

Use apps from Stripe

Build extensions

Custom objectsPartners
Partner ecosystem

Partner certification

United States
English (United States)

API v2 overview
Understand the behavior of APIs in the v2 namespace.

Ask about this page
Copy for LLM
View as MarkdownInstall skills

The Stripe API provides two namespaces that contain different sets of endpoints:
API v1: The /v1 namespace includes most of the existing Stripe API today.
API v2: The /v2 namespace includes endpoints that use /v2 design patterns.
Key differences between the v1 and v2 namespace
API v1API v2Send data to the APIRequests use form encoding (application/x-www-form-urlencoded), and responses use JSON encoding (application/json).Request and responses use JSON encoding (application/json).Test your integration
Validate APIs in the /v1 namespace using Sandboxes, an isolated environment.
Validate APIs in the /v2 namespace using Sandboxes, an isolated environment.
Read more: Sandboxes
Send idempotent requests
When providing the Idempotency-Key header with a unique identifier, if the API already processed the request, it returns the previously stored request.
When providing the Idempotency-Key header with a unique identifier, the API retries any failed requests without producing side effects (any extraneous change or observable behavior that occurs as a result of an API call).
Read more: Idempotency
Receive events from Stripe
Most events emitted from APIs in the /v1 namespace include a snapshot of an API object in their payload. Some APIs in the /v1 namespace generate thin events, which include a minimal, unversioned push payload.
Events emitted from APIs in the /v2 namespace are thin events.
Read more: Event destinations
Paginating through a list
Specify an object’s ID as the starting element for list API requests. Use the starting_after, ending_before, and has_more properties from the API response to paginate through a list.
Specify the page token for list API requests. Use the previous_page_url and next_page_url properties in the API response to paginate through a list.
Read more: List pagination
Consistency guarantees for listsTop-level lists are immediately consistent (with higher latency to render). Some sublists are eventually consistent.Lists are eventually consistent by default and lower-latency.Fetch additional data with expansion
Use the expand parameter to replace IDs for related API objects with fully-expanded child objects.
Read more: Expanding responses
The expand parameter isn’t supported. Some APIs in this namespace might provide additional fields in their responses by using the include parameter.
Manage metadataRemove a key-value pair by setting the value to an empty string.Remove a key-value pair by setting the value to null.

SDKs that support API v2
All server-side SDKs support APIs in the /v2 namespace.
Using API v2 with the Stripe CLI
Use stripe trigger and stripe listen to test your integration’s event handling.
To access APIs in the /v2 namespace using the Stripe CLI, use the command stripe v2. For example, to list all v2 Accounts, you can use stripe v2 core accounts list.
SDK, CLI, and API versioning
SDKs and the Stripe CLI automatically include an API version for all requests. After you update your SDK or CLI version, Stripe simultaneously updates the API version of your requests and responses.
Include Stripe-Version without SDK or CLI
All API requests to the API /v2 namespace must include the Stripe-Version header to specify the underlying API version.
For example, a curl request using API version 2024-09-30.acacia looks like:

Command Line

curl -G https://api.stripe.com/v2/core/event_destinations \
  -H &quot;Authorization: Bearer {{YOUR_API_KEY}}&quot; \
  -H &quot;Stripe-Version: 2024-09-30.acacia&quot; \

Using APIs from the v1 and v2 namespaces in the same integration
You can use any combination of APIs in the /v1 or /v2 namespace in the same integration.

Select a languageJava
Node.js
Python
.NET
Ruby
PHP
Go
 No results

import com.stripe.StripeClient;

StripeClient stripe = new StripeClient(&quot;{{YOUR_API_KEY}}&quot;);

// Call a v2 API
EventDestination eventDestination = stripe.v2().core().eventDestinations().retrieve(&quot;ed_123&quot;);

// Call a v1 API
Customer customer = stripe.customers().retrieve(&quot;cus_123&quot;);

If you’re not using an official SDK or the CLI, always include the namespace in the URL path for your API calls. For example:

Command Line

# Call a v2 API
curl https://api.stripe.com/v2/core/event_destinations

# Call a v1 API
curl https://api.stripe.com/v1/charges -d amount=2000 -d currency=usd

List pagination
APIs within the /v2 namespace (for example, GET /v2/core/event_destinations) contain a different pagination interface compared to those in the /v1 namespace.
The previous_page_url property returns a URL to fetch the previous page of the list. If there are no previous pages, the value is null.
The next_page_url property returns a URL to fetch the next page of the list. If there are no more pages, the value is null.
You can use these URLs to make requests without using our SDKs. Conversely, when you use our SDKs, you don’t need to use these URLs because the SDKs handle auto-pagination automatically.
You can’t change list filters after the first request.

Select a languageJava
Node.js
Python
.NET
Ruby
PHP
Go
 No results

StripeClient stripe = new StripeClient(&quot;{{YOUR_API_KEY}}&quot;);

EventDestinationListParams params = EventDestinationListParams.builder().build();

for (EventDestination eventDestination : stripe.v2().core().eventDestinations().list(params).autoPagingIterable()) {
  // process event destination object
}

Using query parameters in API requests
Use filters on list endpoints to constrain results. Use include parameters on supported GET endpoints to return additional fields in the response. Filters and include parameters let you pass an array of values. When you make direct API requests (not using server-side SDKs or the CLI), you must always specify the index of the array value using bracket notation, even if you only pass a single value.
For example, to list all Accounts where the applied_configuration is merchant, pass the following:

Command Line

curl -G https://api.stripe.com/v2/core/accounts?applied_configurations[0]=merchant
  -H &quot;Authorization: Bearer {{YOUR_API_KEY}}&quot; \
  -H &quot;Stripe-Version: 2025-12-15.clover&quot; \

To list all Accounts where the configuration is merchant or customer, use the following syntax:

Command Line

curl -G https://api.stripe.com/v2/core/accounts?applied_configurations[0]=merchant&applied_configurations[1]=customer
  -H &quot;Authorization: Bearer {{YOUR_API_KEY}}&quot; \
  -H &quot;Stripe-Version: 2025-12-15.clover&quot; \

You can use the same pattern for include parameters. For example, to include multiple fields in a response, use the following syntax:

Command Line

curl -G https://api.stripe.com/v2/core/accounts/:id?include[0]=requirements&include[1]=defaults&include[2]=identity
  -H &quot;Authorization: Bearer {{YOUR_API_KEY}}&quot; \
  -H &quot;Stripe-Version: 2025-12-15.clover&quot; \

In some cases, an array is nested within a query parameter. For example, to retrieve a list of payout methods, you can provide an array of values to filter on the usage_status[payments] nested field:

Command Line

curl -G https://api.stripe.com/v2/money_management/payout_methods?usage_status[payments][0]=eligible&usage_status[payments][1]=invalid
  -H &quot;Authorization: Bearer {{YOUR_API_KEY}}&quot; \
  -H &quot;Stripe-Version: 2025-12-15.preview&quot; \

Idempotency
APIs in the /v2 namespace provide improved support for idempotency behavior, preventing unintended side effects when requests are performed multiple times using the same idempotency key. When the API receives two requests with the same idempotency key:
If the first request succeeded, the API skips making new changes and returns an updated response.
If the first request failed (or partially failed), the API re-executes the failed requests and returns the new response.
In the rare event that it’s no longer possible for an idempotent replay to succeed, the API returns an error explaining why.
A request is considered an idempotent replay of another request if the following are all true:
They use the same idempotency key for the same API
They occur in the scope of the same account or sandbox
They occur within 30 days of each other
To specify an idempotency key, use the Idempotency-Key header and provide a unique value to represent the operation (we recommend a UUID). If no key is provided, Stripe automatically generates a UUID for you.
All POST and DELETE API v2 requests accept idempotency keys and behave idempotently. GET requests are idempotent by definition, so sending an idempotency key has no effect.
Idempotency differences between API v1 and API v2
API v1 and API v2 idempotency have a few key differences:
API v1 only supports idempotent replay for POST requests. API v2 supports all POST and DELETE requests.
A request is considered an idempotent replay of another request for:API v1 if they use the same idempotency key and occur within 24 hours of each other.
API v2 if they use the same idempotency key, are made to the same API, occur within the scope of the same account or sandbox, and occur within 30 days of each other.

When you provide the same idempotency key for two requests:API v1 always returns the previously-saved response of the first API request, even if it was an error.
API v2 attempts to retry any failed requests without producing side effects (any extraneous change or observable behavior that occurs as a result of an API call) and provide an updated response.

Making idempotent requests
Using the SDK, provide an idempotency key with the idempotencyKey property in API requests.
For example, to make an API request with a specific idempotency key:

Select a languageJava
Node.js
Python
.NET
Ruby
PHP
Go
 No results

StripeClient stripe = new StripeClient(&quot;{{YOUR_API_KEY}}&quot;);

String idempotencyKey = &quot;unique-idempotency-key&quot;;
Example result = stripe.v2().examples().create(
        ExampleCreateParams.builder()
          .setName(&quot;My example&quot;)
          .build(),

        RequestOptions.builder()
          .setIdempotencyKey(idempotencyKey)
          .build());

If you’re not using a SDK or the CLI, requests can include the Idempotency-Key header:

Command Line

curl https://api.stripe.com/v2/examples \
  -H &quot;Authorization: Bearer {{YOUR_API_KEY}}&quot; \
  -H &quot;Stripe-Version: {{STRIPE_API_VERSION}}&quot; \
  -H &quot;Idempotency-Key: unique-idempotency-key&quot; \
  -d <JSON request body>

Limitations
Not all /v2 APIs support test mode sandboxes. You can always test /v2 endpoints in a sandbox.
Currently, Stripe only generates thin events using /v2 endpoints and resources.
You can only see request logs generated by API v2 in Workbench, not in the Developers Dashboard.

On this page
