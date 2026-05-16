# Receive Stripe events in your webhook endpoint

**Source:** https://docs.stripe.com/webhooks

Receive Stripe events in your webhook endpoint | Stripe Documentation

          Skip to content

Webhook endpoint

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

API

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

Event destinationsIntegrate with events
Amazon EventBridge
Azure Event Grid
Webhook endpointWebhook builder
Handle payment events
Webhook versioning
Migrate to thin events
Resolve webhook signature verification errors
Process undelivered events
Handle irrecoverable webhook events
Manage webhooks with event notification handlers

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

Receive Stripe events in your webhook endpoint
Listen for events from Stripe on your webhook endpoint so your integration can automatically trigger reactions.

Ask about this page
Copy for LLM
View as MarkdownInstall skills

Send events to your AWS account or Azure subscription
You can send events directly to Amazon EventBridge or Azure Event Grid as event destinations.

Create an event destination to receive events at an HTTPS webhook endpoint. After you register a webhook endpoint, Stripe can push real-time event data to your application’s webhook endpoint when events happen in your Stripe account. Stripe uses HTTPS to send webhook events to your app as a JSON payload that includes an Event object.
Receiving webhook events helps you respond to asynchronous events, such as when a customer’s bank confirms a payment, a customer disputes a charge, or a recurring payment succeeds.
Get started
To start receiving webhook events in your app:
Create a webhook endpoint handler to receive event data POST requests.
Test your webhook endpoint handler locally using the Stripe CLI.
Create a new event destination for your webhook endpoint.
Secure your webhook endpoint.
You can register and create one endpoint to handle several different event types at the same time, or set up individual endpoints for specific events.
Unsupported event type behaviors for organization event destinations
Stripe sends most event types asynchronously, but waits for a response for some event types. In these cases, Stripe behaves differently based on whether or not the event destination responds.
If your event destination receives Organization events, those requiring a response have the following limitations:
You can’t subscribe to issuing_authorization.request for organization destinations. Instead, set up a webhook endpoint in a Stripe account within the organization to subscribe to this event type. Use issuing_authorization.request to authorize purchase requests in real-time.
Organization destinations receiving checkout_sessions.completed can’t handle redirect behavior when you embed Checkout directly in your website or redirect customers to a Stripe-hosted payment page. To influence Checkout redirect behavior, process this event type with a webhook endpoint configured in a Stripe account within the organization.
Organization destinations responding unsuccessfully to an invoice.created event can’t influence automatic invoice finalization when using automatic collection. You must process this event type with a webhook endpoint configured in a Stripe account within the organization to trigger automatic invoice finalization.
Create a handler

Set up an HTTP or HTTPS endpoint function that can accept webhook requests with a POST method. If you’re still developing your endpoint function on your local machine, it can use HTTP. After it’s publicly accessible, your webhook endpoint function must use HTTPS.
Set up your endpoint function so that it:
Handles POST requests with a JSON payload consisting of an event object.
For organization event handlers, it inspects the context value to determine which account in an organization generated the event, then sets the Stripe-Context header corresponding to the context value.
Quickly returns a successful status code (2xx) prior to any complex logic that might cause a timeout. For example, you must return a 200 response before updating a customer’s invoice as paid in your accounting system.
Note
Use our interactive webhook endpoint builder to build a webhook endpoint function in your programming language.
Use the Stripe API reference to identify the thin event objects or snapshot event objects your webhook handler needs to process.

Example endpoint
This code snippet is a webhook function configured to check for received events from a Stripe account, handle the events, and return a 200 responses. Reference the snapshot event handler when you use API v1 resources, and reference the thin event handler when you use API v2 resources.
Snapshot event handler

Thin event handler (Clover+)

Thin event handler (Acacia or Basil)

When you create a snapshot event handler, use the API object definition at the time of the event for your logic by accessing the event’s data.object fields. You can also retrieve the API resource from the Stripe API to access the latest and up-to-date object definition.

Select a languageRuby
Python
PHP
Java
Node.js
Go
.NET
 No results

require &#x27;json&#x27;
require &#x27;stripe&#x27;

client = Stripe::StripeClient.new(ENV.fetch(&#x27;STRIPE_API_KEY&#x27;))

# Replace this endpoint secret with your unique endpoint secret key
# If you&#x27;re testing with the CLI, run &#x27;stripe listen&#x27; to find the secret key
# If you defined your endpoint using the API or the Dashboard, check your webhook settings for your endpoint secret: https://dashboard.stripe.com/webhooks
endpoint_secret = &#x27;whsec_...&#x27;;

# Using Sinatra
post &#x27;/webhook&#x27; do
  payload = request.body.read
  event = nil

  begin
    event = Stripe::Event.construct_from(
      JSON.parse(payload, symbolize_names: true)
    )
  rescue JSON::ParserError => e
    # Invalid payload
    status 400
    return
  end

  # Check that you have configured webhook signing
  if endpoint_secret
    # Retrieve the event by verifying the signature using the raw body and the endpoint secret
    signature = request.env[&#x27;HTTP_STRIPE_SIGNATURE&#x27;];
    begin
      event = Stripe::Webhook.construct_event(
        payload, signature, endpoint_secret
      )
    rescue Stripe::SignatureVerificationError => e
      puts &quot;⚠️  Webhook signature verification failed. #{e.message}&quot;
      status 400
    end
  end

  # Handle the event
  case event.type
  when &#x27;payment_intent.succeeded&#x27;
    payment_intent = event.data.object # contains a Stripe::PaymentIntent
    # Then define and call a method to handle the successful payment intent.
    # handle_payment_intent_succeeded(payment_intent)
  when &#x27;payment_method.attached&#x27;
    payment_method = event.data.object # contains a Stripe::PaymentMethod
    # Then define and call a method to handle the successful attachment of a PaymentMethod.
    # handle_payment_method_attached(payment_method)
  # ... handle other event types
  else
    puts &quot;Unhandled event type: #{event.type}&quot;
  end

  status 200
end

Using context
Snapshot events

Thin event handler (Clover+)

Thin event handler (Acacia or Basil)

This code snippet is a webhook function configured to check for received events, detect the originating account if applicable, handle the event, and return a 200 response.

Select a languageRuby
Python
Java
Node.js
.NET
 No results

require &#x27;json&#x27;

client = Stripe::StripeClient.new(&#x27;sk_...&#x27;)

# Using Sinatra
post &#x27;/webhook&#x27; do
  payload = request.body.read
  event = nil

  begin
    event = Stripe::Event.construct_from(
      JSON.parse(payload, symbolize_names: true)
    )
  rescue JSON::ParserError => e
    # Invalid payload
    status 400
    return
  end

  # Extract the context
  context = event.context

  # Define your API key variables (ideally loaded securely)
  ACCOUNT_123_API_KEY = &quot;sk_test_REDACTED&quot;
  ACCOUNT_456_API_KEY = &quot;sk_test_REDACTED&quot;

  account_api_keys = {
    &quot;account_123&quot; => ACCOUNT_123_API_KEY,
    &quot;account_456&quot; => ACCOUNT_456_API_KEY
  }

  api_key = account_api_keys[context]

  if api_key.nil?
    puts &quot;No API key found for context: #{context}&quot;
    status 400
    return
  end

  # Handle the event
  case event.type
  when &#x27;customer.created&#x27;
    customer = event.data.object

    begin

      latest_customer = client.v1.customers.retrieve(customer.id, {api_key: api_key})
      handle_customer_created(latest_customer, context)
    rescue => e
      puts &quot;Error retrieving customer: #{e.message}&quot;
      status 500
      return
    end

  when &#x27;payment_method.attached&#x27;
    payment_method = event.data.object

    begin
      latest_payment_method = client.v1.payment_methods.retrieve(payment_method.id, {api_key: api_key})
      handle_payment_method_attached(latest_payment_method, context)
    rescue => e
      puts &quot;Error retrieving payment method: #{e.message}&quot;
      status 500
      return
    end

  else
    puts &quot;Unhandled event type: #{event.type}&quot;
  end

  status 200
end

Test your handler

Before you go-live with your webhook endpoint function, we recommend that you test your application integration. You can do so by configuring a local listener to send events to your local machine, and sending test events. You need to use the CLI to test.
Forward events to a local endpoint
To forward events to your local endpoint, run the following command with the CLI to set up a local listener. The --forward-to flag sends all Stripe events in a sandbox to your local webhook endpoint. Use the appropriate CLI commands below depending on whether you use thin or snapshot events.
Forward snapshot events

Forward thin events

Use the following command to forward snapshot events to your local listener.

Command Line

stripe listen --forward-to localhost:4242/webhook

Note
You can also run stripe listen to see events in Stripe Shell, although you won’t be able to forward events from the shell to your local endpoint.

Useful configurations to help you test with your local listener include the following:
To disable HTTPS certificate verification, use the --skip-verify optional flag.
To forward only specific events, use the --events optional flag and pass in a comma separated list of events.
Forward target snapshot events

Forward target thin events

Use the following command to forward target snapshot events to your local listener.

Command Line

stripe listen --events payment_intent.created,customer.created,payment_intent.succeeded,checkout.session.completed,payment_intent.payment_failed \
  --forward-to localhost:4242/webhook

To forward events to your local webhook endpoint from the public webhook endpoint that you already registered on Stripe, use the --load-from-webhooks-api optional flag. It loads your registered endpoint, parses the path and its registered events, then appends the path to your local webhook endpoint in the --forward-to path.
Forward snapshot events from a public webhook endpoint

Forward thin events from a public webhook endpoint

Use the following command to forward snapshot events from a public webhook endpoint to your local listener.

Command Line

stripe listen --load-from-webhooks-api --forward-to localhost:4242/webhook

To check webhook signatures, use the {{WEBHOOK_SIGNING_SECRET}} from the initial output of the listen command.

Ready! Your webhook signing secret is &#x27;{{WEBHOOK_SIGNING_SECRET}}&#x27; (^C to quit)

Triggering test events
To send test events, trigger an event type that your event destination is subscribed to by manually creating an object in the Stripe Dashboard. Learn how to trigger events with Stripe for VS Code.
Trigger a snapshot event

Trigger a thin event

You can use the following command in either Stripe Shell or Stripe CLI. This example triggers a payment_intent.succeeded event:

Command Line

stripe trigger payment_intent.succeeded
Running fixture for: payment_intent
Trigger succeeded! Check dashboard for event details.

Register your endpoint

After testing your webhook endpoint function, use the API or the Webhooks tab in Workbench to register your webhook endpoint’s accessible URL so Stripe knows where to deliver events. You can register up to 16 webhook endpoints with Stripe. Registered webhook endpoints must be publicly accessible HTTPS URLs.
Webhook URL format
The URL format to register a webhook endpoint is:

https://<your-website>/<your-webhook-endpoint>

For example, if your domain is https://mycompanysite.com and the route to your webhook endpoint is @app.route(&#x27;/stripe_webhooks&#x27;, methods=[&#x27;POST&#x27;]), specify https://mycompanysite.com/stripe_webhooks as the Endpoint URL.
Create an event destination for your webhook endpoint
Create an event destination using Workbench in the Dashboard or programmatically with the API. You can register up to 16 event destinations on each Stripe account.
When you create an event destination, you choose which scope it listens to:
Your account: events from resources in your account. If you use the Accounts v2 API, this includes thin events for accounts created in your account, such as connected accounts, but not their snapshot events.
Connected accounts: events from resources belonging to Accounts that you create in your account, such as connected accounts. If you use the Accounts v2 API, this scope includes snapshot events for Account objects created in your account, but not their thin events. However, it includes both snapshot and thin events for Account objects belonging to those Accounts.
Most developers start with destinations that listen to the Your account scope. If you use Connect or the Accounts v2 API, you might need destinations that listen to both scopes. See Connect webhooks
Dashboard

API

To create a new webhook endpoint in the Dashboard:
Open the Webhooks tab in Workbench.
Click Create an event destination.
Select where you want to receive events from. Stripe supports two types of configurations: Your account and Connected accounts. Select Account to listen to events from your own account. If you created a Connect application and want to listen to events from your connected accounts, select Connected accounts.
Listen to events from an organization webhook endpoint
If you create a webhook endpoint in an organization account, select Accounts to listen to events from accounts in your organization. If you have Connect platforms as members of your organizations and want to listen to events from the all the platforms’ connected accounts, select Connected accounts.

Select the API version for the events object you want to consume.
Select the event types that you want to send to a webhook endpoint.
Select Continue, then select Webhook endpoint as the destination type.
Click Continue, then provide the Endpoint URL and an optional description for the webhook.

Note
Workbench replaces the existing Developers Dashboard. If you’re still using the Developers Dashboard, see how to create a new webhook endpoint.

Secure your endpoint

After confirming that your endpoint works as expected, secure it by implementing webhook best practices.
Secure your integration by making sure your handler verifies that all webhook requests are generated by Stripe. You can verify webhook signatures using our official libraries or verify them manually.
Verify with official libraries (recommended)

Verify manually

Verify webhook signatures with official libraries
We recommend using our official libraries to verify signatures. You perform the verification by providing the event payload, the Stripe-Signature header, and the endpoint’s secret. If verification fails, you get an error.
If you get a signature verification error, read our guide about troubleshooting it.
Warning
Stripe requires the raw body of the request to perform signature verification. If you’re using a framework, make sure it doesn’t manipulate the raw body. Any manipulation to the raw body of the request causes the verification to fail.

Select a languageRuby
Python
PHP
Java
Node.js
Go
.NET
 No results

# Don&#x27;t put any keys in code. See https://docs.stripe.com/keys-best-practices.
# Find your keys at https://dashboard.stripe.com/apikeys.
client = Stripe::StripeClient.new(&#x27;sk_test_REDACTED&#x27;

)

require &#x27;stripe&#x27;
require &#x27;sinatra&#x27;

# If you are testing your webhook locally with the Stripe CLI you
# can find the endpoint&#x27;s secret by running `stripe listen`
# Otherwise, find your endpoint&#x27;s secret in your webhook settings in
# the Developer Dashboard
endpoint_secret = &#x27;whsec_...&#x27;

# Using the Sinatra framework
set :port, 4242

post &#x27;/my/webhook/url&#x27; do
  payload = request.body.read
  sig_header = request.env[&#x27;HTTP_STRIPE_SIGNATURE&#x27;]
  event = nil

  begin
    event = Stripe::Webhook.construct_event(
      payload, sig_header, endpoint_secret
    )
  rescue JSON::ParserError => e
    # Invalid payload
    puts &quot;Error parsing payload: #{e.message}&quot;
    status 400
    return
  rescue Stripe::SignatureVerificationError => e
    # Invalid signature
    puts &quot;Error verifying webhook signature: #{e.message}&quot;
    status 400
    return
  end

  # Handle the event
  case event.type
  when &#x27;payment_intent.succeeded&#x27;
    payment_intent = event.data.object # contains a Stripe::PaymentIntent
    puts &#x27;PaymentIntent was successful!&#x27;
  when &#x27;payment_method.attached&#x27;
    payment_method = event.data.object # contains a Stripe::PaymentMethod
    puts &#x27;PaymentMethod was attached to a Customer!&#x27;
  # ... handle other event types
  else
    puts &quot;Unhandled event type: #{event.type}&quot;
  end

  status 200
end

Debug webhook integrations
Multiple types of issues can occur when delivering events to your webhook endpoint:
Stripe might not be able to deliver an event to your webhook endpoint.
Your webhook endpoint might have an SSL issue.
Your network connectivity is intermittent.
Your webhook endpoint isn’t receiving events that you expect to receive.
View event deliveries
To view event deliveries, open Workbench, select the webhook endpoint under Webhooks, then select the Event deliveries tab. The Event deliveries tab provides a list of events and whether they’re Delivered, Pending, or Failed. Click an event to view metadata, including the HTTP status code of the delivery attempt and the time of pending future deliveries.
You can also use the Stripe CLI to listen for events directly in your terminal.
Fix HTTP status codes
When an event displays a status code of 200, it indicates successful delivery to the webhook endpoint. You might also receive a status code other than 200. View the table below for a list of common HTTP status codes and recommended solutions.
Pending webhook statusDescriptionFix(Unable to connect) ERRWe’re unable to establish a connection to the destination server.Make sure that your host domain is publicly accessible to the internet.(302) ERR (or other 3xx status)The destination server attempted to redirect the request to another location. We consider redirect responses to webhook requests as failures.Set the webhook endpoint destination to the URL resolved by the redirect.(400) ERR (or other 4xx status)The destination server can’t or won’t process the request. This might occur when the server detects an error (400), when the destination URL has access restrictions, (401, 403, 405), or when the destination URL doesn’t exist (404).Make sure that your endpoint is publicly accessible to the internet and accepts a POST HTTP method.(500) ERR (or other 5xx status)The destination server encountered an error while processing the request.Review your application’s logs to understand why it’s returning a 500 error.(TLS error) ERRWe couldn’t establish a secure connection to the destination server. Issues with the SSL/TLS certificate or an intermediate certificate in the destination server’s certificate chain usually cause these errors. Stripe requires TLS version v1.2 or higher.Perform an SSL server test to find issues that might cause this error.(Timed out) ERRThe destination server took too long to respond to the webhook request.Make sure you defer complex logic and return a successful response immediately in your webhook handling code.

Event delivery behaviors
This section helps you understand different behaviors to expect regarding how Stripe sends events to your webhook endpoint.
Automatic retries
Stripe attempts to deliver events to your destination for up to three days with an exponential back off in live mode. View when the next retry will occur, if applicable, in your event destination’s Event deliveries tab. We retry event deliveries created in a sandbox three times over the course of a few hours. If your destination has been disabled or deleted when we attempt a retry, we prevent future retries of that event. However, if you disable and then re-enable the event destination before we’re able to retry, you still see future retry attempts.
Manual retries
There are two ways to manually retry events:
In the Stripe Dashboard, click Resend when looking at a specific event. This works for up to 15 days after the event creation.
With the Stripe CLI, run the stripe events resend <event_id> --webhook-endpoint=<endpoint_id> command. This works for up to 30 days after the event creation.
Manually resending an event that had previous delivery failures to a webhook endpoint doesn’t dismiss Stripe’s automatic retry behavior, even if it results in a 2xx status code. Learn how to process undelivered webhook events to stop future retries.
Event ordering
Stripe doesn’t guarantee the delivery of events in the order that they’re generated. For example, creating a subscription might generate the following events:
customer.subscription.created
invoice.created
invoice.paid
charge.created (if there’s a charge)
Make sure that your event destination isn’t dependent on receiving events in a specific order. Be prepared to manage their delivery appropriately. You can also use the API to retrieve any missing objects. For example, you can retrieve the invoice, charge, and subscription objects with the information from invoice.paid if you receive this event first.
API versioning
The API version in your account settings when the event occurs dictates the API version, and therefore the structure of an Event sent to your destination. For example, if your account is set to an older API version, such as 2015-02-16, and you change the API version for a specific request with versioning, the Event object generated and sent to your destination is still based on the 2015-02-16 API version. You can’t change Event objects after creation. For example, if you update a charge, the original charge event remains unchanged. As a result, subsequent updates to your account’s API version don’t retroactively alter existing Event objects. Retrieving an older Event by calling /v1/events using a newer API version also has no impact on the structure of the received event. You can set test event destinations to either your default API version or the latest API version. The Event sent to the destination is structured for the event destination’s specified version.
Best practices for using webhooks
Review these best practices to make sure your webhook endpoints remain secure and function well with your integration.
Handle duplicate events
Webhook endpoints might occasionally receive the same event more than once. You can guard against duplicated event receipts by logging the event IDs you’ve processed, and then not processing already-logged events.
In some cases, two separate Event objects are generated and sent. To identify these duplicates, use the ID of the object in data.object along with the event.type.
Only listen to event types your integration requires
Configure your webhook endpoints to receive only the types of events required by your integration. Listening for extra events (or all events) puts undue strain on your server and we don’t recommend it.
You can change the events that a webhook endpoint receives in the Dashboard or with the API.
Handle events asynchronously
Configure your handler to process incoming events with an asynchronous queue. You might encounter scalability issues if you choose to process events synchronously. Any large spike in webhook deliveries (for example, during the beginning of the month when all subscriptions renew) might overwhelm your endpoint hosts.
Asynchronous queues allow you to process the concurrent events at a rate your system can support.
Exempt webhook route from CSRF protection
If you’re using Rails, Django, or another web framework, your site might automatically check that every POST request contains a CSRF token. This is an important security feature that helps protect you and your users from cross-site request forgery attempts. However, this security measure might also prevent your site from processing legitimate events. If so, you might need to exempt the webhooks route from CSRF protection.

Select a languageRails
Django
 No results

class StripeController < ApplicationController
  # If your controller accepts requests other than Stripe webhooks,
  # you&#x27;ll probably want to use `protect_from_forgery` to add CSRF
  # protection for your application. But don&#x27;t forget to exempt
  # your webhook route!
  protect_from_forgery except: :webhook

  def webhook
    # Process webhook data in `params`
  end
end

Receive events with an HTTPS server
If you use an HTTPS URL for your webhook endpoint (required in live mode), Stripe validates that the connection to your server is secure before sending your webhook data. For this to work, your server must be correctly configured to support HTTPS with a valid server certificate. Stripe webhooks support only TLS versions v1.2 and v1.3.
Roll endpoint signing secrets periodically
The secret used for verifying that events come from Stripe is modifiable in the Webhooks tab in Workbench. To keep them safe, we recommend that you roll (change) secrets periodically, or when you suspect a compromised secret.
To roll a secret:
Click each endpoint in the Workbench Webhooks tab that you want to roll the secret for.
Navigate to the overflow menu () and click Roll secret. You can choose to immediately expire the current secret or delay its expiration for up to 24 hours to allow yourself time to update the verification code on your server. During this time, multiple secrets are active for the endpoint. Stripe generates one signature per secret until expiration.
Verify events are sent from Stripe
Without verification, an attacker could send fake webhook events to your endpoint to trigger actions like fulfilling orders, granting account access, or modifying records. Always verify that webhook events originate from Stripe before acting on them.
Use both of these protections:
IP allowlisting: Stripe sends webhook events from a set list of IP addresses. Configure your server or firewall to only accept webhook requests from these addresses.
Signature verification: Stripe signs every webhook event by including a signature in the Stripe-Signature header. Verify this signature using our official libraries or manually to confirm the event wasn’t sent or modified by a third party.
The following section describes how to verify webhook signatures:
Retrieve your endpoint’s secret.
Verify the signature.
Retrieving your endpoint’s secret
Use Workbench and go to the Webhooks tab to view all your endpoints. Select an endpoint that you want to obtain the secret for, then click Click to reveal.
Stripe generates a unique secret key for each endpoint. If you use the same endpoint for both test and live API keys, the secret is different for each one. Additionally, if you use multiple endpoints, you must obtain a secret for each one you want to verify signatures on. After this setup, Stripe starts to sign each webhook it sends to the endpoint.
Preventing replay attacks
A replay attack is when an attacker intercepts a valid payload and its signature, then re-transmits them. To mitigate such attacks, Stripe includes a timestamp in the Stripe-Signature header. Because this timestamp is part of the signed payload, it’s also verified by the signature, so an attacker can’t change the timestamp without invalidating the signature. If the signature is valid but the timestamp is too old, you can have your application reject the payload.
Our libraries have a default tolerance of 5 minutes between the timestamp and the current time. You can change this tolerance by providing an additional parameter when verifying signatures. Use Network Time Protocol (NTP) to make sure that your server’s clock is accurate and synchronizes with the time on Stripe’s servers.
Common mistake
Don’t use a tolerance value of 0. Using a tolerance value of 0 disables the recency check entirely.

Stripe generates the timestamp and signature each time we send an event to your endpoint. If Stripe retries an event (for example, your endpoint previously replied with a non-2xx status code), then we generate a new signature and timestamp for the new delivery attempt.
Quickly return a 2xx response
Your endpoint must quickly return a successful status code (2xx) prior to any complex logic that could cause a timeout. For example, you must return a 200 response before updating a customer’s invoice as paid in your accounting system.
See also
Send events to Amazon EventBridge
Send events to Azure Event Grid
List of thin event types
List of snapshot event types
Interactive webhook endpoint builder

Code quickstartOn this page
