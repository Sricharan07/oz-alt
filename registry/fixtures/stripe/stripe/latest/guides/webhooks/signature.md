# Resolve webhook signature verification errors

**Source:** https://docs.stripe.com/webhooks/signature

Resolve webhook signature verification errors | Stripe Documentation

          Skip to content

Resolve webhook signature verification errors

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
Java
Node.js
Go
.NET
 No results

Stripe::Webhook.construct_event(request_body, signature, endpoint_secret)

If you get the following Webhook signature verification failed error, at least one of the three parameters you passed to the constructEvent() function is incorrect.

Webhook signature verification failed. Err: No signatures found matching the expected signature for payload.

Check the endpoint secret
The most common error is using the wrong endpoint secret. If you’re using a webhook endpoint created in the Dashboard, open the endpoint in the Dashboard and click the Reveal secret link near the top of the page to view the secret. If you’re using the Stripe CLI, the secret is printed in the Terminal when you run the stripe listen command.
In both cases, the secret starts with a whsec_ prefix, but the secret itself is different. Don’t verify signatures on events forwarded by the CLI using the secret from a Dashboard-managed endpoint, or the other way around. Finally, print the endpointSecret used in your code, and make sure that it matches the one you found above.
Check the request body
The request body must be the body string that Stripe sends in UTF-8 encoding without any changes. When you print it as a string, it looks similar to this:

{
  &quot;id&quot;: &quot;evt_xxx&quot;,
  &quot;object&quot;: &quot;event&quot;,
  &quot;data&quot;: {
      ...
  }
}

Retrieve the raw request body
Some frameworks might edit the request body by doing things like adding or removing whitespace, reordering the key-value pairs, converting the string to JSON, or changing the encoding. All of these cases lead to a failed signature verification.
The following is a non-exhaustive list of frameworks that might parse or mutate the data using common configurations, and some tips on how to get the raw request body.
FrameworkRetrieval methodstripe-node library with ExpressFollow our integration quickstart guide.stripe-node library with Body ParserTry solutions listed in this GitHub issue.stripe-node library with Next.js App RouterTake a look at this working example.stripe-node library with Next.js Pages RouterTry disabling bodyParser and using buffer(request), like in this example.

If you’re using the stripe-node library with Express, make sure that app.use(express.json()) is placed after the webhook route. In Express, the order of middleware configuration matters. If express.json() is applied before your webhook route, it parses the request body before signature verification, causing the verification to fail. For example:

// Webhook route in its original request form
app.post(&#x27;/webhook&#x27;, ...);

// Parse the request body in JSON for other routes
app.use(express.json());

// Put other routes here
app.post(&#x27;/another-route&#x27;, ...);

AWS API Gateway with Lambda function
To retrieve the raw request body for the AWS API Gateway with Lambda function, in the API Gateway, set up a Body Mapping Template of content type application/json:

{
  &quot;method&quot;: &quot;$context.httpMethod&quot;,
  &quot;body&quot;: $input.json(&#x27;$&#x27;),
  &quot;rawBody&quot;: &quot;$util.escapeJavaScript($input.body).replaceAll(&quot;\\&#x27;&quot;, &quot;&#x27;&quot;)&quot;,
  &quot;headers&quot;: {
    #foreach($param in $input.params().header.keySet())
    &quot;$param&quot;: &quot;$util.escapeJavaScript($input.params().header.get($param))&quot;
    #if($foreach.hasNext),#end
    #end
  }
}

Then, in the Lambda function, access the raw body with the event’s rawBody property and the headers with the event’s headers property.
Check the signature
Print the signature parameter, and confirm that it looks similar to this:

t=xxx,v1=yyy,v0=zzz

If not, check if you have an issue in your code when trying to extract the signature from the header.

On this page
