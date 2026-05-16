# https://vercel.com/docs/integrations/create-integration/marketplace-api/reference/vercel/submit-invoice

**Source:** https://vercel.com/docs/integrations/create-integration/marketplace-api/reference/vercel/submit-invoice

---
title: submit-invoice
product: vercel
url: /docs/integrations/create-integration/marketplace-api/reference/vercel/submit-invoice
canonical_url: "https://vercel.com/docs/integrations/create-integration/marketplace-api/reference/vercel/submit-invoice"
last_updated: 2026-05-16
type: conceptual
prerequisites:
  []
related:
  - /docs/integrations/create-integration/marketplace-api/reference
  - /docs/integrations/create-integration/native-integration
summary: Learn about submit-invoice on Vercel.
install_vercel_plugin: npx plugins add vercel/vercel-plugin
---

# Submit Invoice

```http
POST /v1/installations/{integrationConfigurationId}/billing/invoices
```

This endpoint allows the partner to submit an invoice to Vercel. The invoice is created in Vercel's billing system and sent to the customer. Depending on the type of billing plan, the invoice can be sent at a time of signup, at the start of the billing period, or at the end of the billing period.

 Use the `credentials.access_token` we provided in the [Upsert Installation](#upsert-installation) body to authorize this request.
 There are several limitations to the invoice submission:

 1. A resource can only be billed once per the billing period and the billing plan.
 2. The billing plan used to bill the resource must have been active for this resource during the billing period.
 3. The billing plan used must be a subscription plan.
 4. The interim usage data must be sent hourly for all types of subscriptions. See [Send subscription billing and usage data](#send-subscription-billing-and-usage-data) API on how to send interim billing and usage data.

## Authentication

**bearerToken**: Default authentication mechanism

## Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `integrationConfigurationId` | string | ✓ |  |

## Request Body

**Content-Type**: `application/json`

```json
{
  "externalId": "string",
  "invoiceDate": "string" // required // Invoice date. Must be within the period's start and end.,
  "memo": "string" // Additional memo for the invoice.,
  "period": { // required
    "start": "string" // required,
    "end": "string" // required
  },
  "items": [ // required
    "resourceId": "string" // Partner's resource ID.,
    "billingPlanId": "string" // required // Partner's billing plan ID.,
    "start": "string" // Start and end are only needed if different from the period's start/end.,
    "end": "string" // Start and end are only needed if different from the period's start/end.,
    "name": "string" // required,
    "details": "string",
    "price": "string" // required // Currency amount as a decimal string.,
    "quantity": "number" // required,
    "units": "string" // required,
    "total": "string" // required // Currency amount as a decimal string.
  ],
  "discounts": [
    "resourceId": "string" // Partner's resource ID.,
    "billingPlanId": "string" // required // Partner's billing plan ID.,
    "start": "string" // Start and end are only needed if different from the period's start/end.,
    "end": "string" // Start and end are only needed if different from the period's start/end.,
    "name": "string" // required,
    "details": "string",
    "amount": "string" // required // Currency amount as a decimal string.
  ],
  "final": "boolean" // Set this to `true` if this is the final invoice for the installation. Can only be set when the installation is pending deletion.,
  "test": {
    "validate": "boolean",
    "result": "string"
  }
}
```

## Responses

### 200

Success

**Content-Type**: `application/json`

```json
{
  "invoiceId": "string",
  "test": "boolean",
  "validationErrors": [
"string"
  ]
}
```

### 400

One of the provided values in the request body is invalid.
One of the provided values in the request query is invalid.

### 401

The request is not authorized.

### 403

You do not have permission to access this resource.

### 404

Success

### 409

Success

---

## Related

- [Marketplace API Reference](/docs/integrations/create-integration/marketplace-api/reference)
- [Native Integration Concepts](/docs/integrations/create-integration/native-integration)

---

[View full sitemap](/docs/sitemap)
