# Include-dependent response values in API v2

**Source:** https://docs.stripe.com/api-includable-response-values

Include-dependent response values in API v2 | Stripe Documentation

          Skip to content

Include-dependent response values v2

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

Include-dependent response values in API v2
Learn how to manage API responses that return null by default for certain properties.

Ask about this page
Copy for LLM
View as MarkdownInstall skills

API v2 only
The include parameter is a feature of API v2. Requests in API v1 don’t use it.
Some API v2 responses contain null values for certain properties by default, regardless of their actual values. That reduces the size of response payloads while maintaining the basic response structure. To retrieve the actual values for those properties, specify them in the include array request parameter.
To determine whether you need to use the include parameter in a given request, look at the request description. The include parameter’s enum values represent the response properties that depend on the include parameter.
Endpoint dependency
Whether a response property defaults to null depends on the request endpoint, not the object that the endpoint references. If multiple endpoints return data from the same object, a particular property can depend on include in one endpoint and return its actual value by default for a different endpoint.

A hash property can depend on a single include value, or on multiple include values associated with its child properties. For example, when updating an Account, to return actual values for the entire identity hash, specify identity in the include parameter. Otherwise, the identity hash is null in the response. However, to return actual values for the configuration hash, you must specify individual configurations in the request. If you specify at least one configuration, but not all of them, specified configurations return actual values and unspecified configurations return null. If you don’t specify any configurations, the configuration hash is null in the response.
The following example updates an Account to add the customer and merchant configurations, but doesn’t specify any properties in the include parameter:

Command Line

Select a languagecURL
Stripe CLI
Ruby
Python
PHP
Java
Node.js
Go
.NET
 No results

curl -X POST https://api.stripe.com/v2/core/accounts/acct_123 \
  -H &quot;Authorization: Bearer sk_test_REDACTED

&quot; \
  -H &quot;Stripe-Version: preview&quot; \
  --json &#x27;{
    &quot;configuration&quot;: {
        &quot;customer&quot;: {
            &quot;capabilities&quot;: {
                &quot;automatic_indirect_tax&quot;: {
                    &quot;requested&quot;: true
                }
            }
        },
        &quot;merchant&quot;: {
            &quot;capabilities&quot;: {
                &quot;card_payments&quot;: {
                    &quot;requested&quot;: true
                }
            }
        }
    }
  }&#x27;

The response might look like this:

{
  &quot;id&quot;: &quot;acct_123&quot;,
  &quot;object&quot;: &quot;v2.core.account&quot;,
  &quot;applied_configurations&quot;: [
    &quot;customer&quot;,
    &quot;merchant&quot;
  ],
  &quot;configuration&quot;: null,
  &quot;contact_email&quot;: &quot;furever@example.com&quot;,
  &quot;created&quot;: &quot;2025-06-09T21:16:03.000Z&quot;,
  &quot;dashboard&quot;: &quot;full&quot;,
  &quot;defaults&quot;: null,
  &quot;display_name&quot;: &quot;Furever&quot;,
  &quot;identity&quot;: null,
  &quot;livemode&quot;: true,
  &quot;metadata&quot;: {},
  &quot;requirements&quot;: null
}

This example makes the same request, but specifies configuration.customer and identity in the include parameter:

Command Line

Select a languagecURL
Stripe CLI
Ruby
Python
PHP
Java
Node.js
Go
.NET
 No results

curl -X POST https://api.stripe.com/v2/core/accounts/acct_123 \
  -H &quot;Authorization: Bearer sk_test_REDACTED

&quot; \
  -H &quot;Stripe-Version: preview&quot; \
  --json &#x27;{
    &quot;configuration&quot;: {
        &quot;customer&quot;: {
            &quot;capabilities&quot;: {
                &quot;automatic_indirect_tax&quot;: {
                    &quot;requested&quot;: true
                }
            }
        },
        &quot;merchant&quot;: {
            &quot;capabilities&quot;: {
                &quot;card_payments&quot;: {
                    &quot;requested&quot;: true
                }
            }
        }
    },
    &quot;include&quot;: [
        &quot;configuration.customer&quot;,
        &quot;identity&quot;
    ]
  }&#x27;

The response includes details about the customer configuration and identity, but returns null for all other configurations:

{
  &quot;id&quot;: &quot;acct_123&quot;,
  &quot;object&quot;: &quot;v2.core.account&quot;,
  &quot;applied_configurations&quot;: [
    &quot;customer&quot;,
    &quot;merchant&quot;
  ],
  &quot;configuration&quot;: {
    &quot;customer&quot;: {
      &quot;automatic_indirect_tax&quot;: {
        ...
      },
      &quot;billing&quot;: {
        ...
      },
      &quot;capabilities&quot;: {
        ...
      },
      ...
    },
    &quot;merchant&quot;: null,
    &quot;recipient&quot;: null
  },
  &quot;contact_email&quot;: &quot;furever@example.com&quot;,
  &quot;created&quot;: &quot;2025-06-09T21:16:03.000Z&quot;,
  &quot;dashboard&quot;: &quot;full&quot;,
  &quot;defaults&quot;: null,
  &quot;display_name&quot;: &quot;Furever&quot;,
  &quot;identity&quot;: {
    &quot;business_details&quot;: {
      &quot;doing_business_as&quot;: &quot;FurEver&quot;,
      &quot;id_numbers&quot;: [
        {
          &quot;type&quot;: &quot;us_ein&quot;
        }
      ],
      &quot;product_description&quot;: &quot;Saas pet grooming platform at furever.dev using Connect embedded components&quot;,
      &quot;structure&quot;: &quot;sole_proprietorship&quot;,
      &quot;url&quot;: &quot;http://accessible.stripe.com&quot;
    },
    &quot;country&quot;: &quot;US&quot;
  },
  &quot;livemode&quot;: true,
  &quot;metadata&quot;: {},
  &quot;requirements&quot;: null
}
