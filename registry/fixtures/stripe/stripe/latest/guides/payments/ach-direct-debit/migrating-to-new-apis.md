# Migrating to new ACH Direct Debit APIs

**Source:** https://docs.stripe.com/payments/ach-direct-debit/migrating-to-new-apis

Migrating to new ACH Direct Debit APIs | Stripe Documentation

          Skip to content

Migrating to new ACH Direct Debit APIs

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

OverviewAccept a paymentUpgrade your integrationOnline payments
OverviewFind your use caseUse Payment Links

Build a payments page

Build a custom integration with Elements

Build an in-app integration

Use Managed Payments

Use Checkout studio

Recurring paymentsIn-person payments
Terminal

Payment methods
Add payment methodsOverview
Payment method integration options
Manage default payment methods in the Dashboard
Payment method types
Cards

Pay with Stripe balance
Stablecoin payments

Bank debitsACH Direct DebitAccept a payment
Save bank details
Migrating to new ACH Direct Debit APIsMigrate existing bank accounts

Migrating from another processor
Blocked bank accounts
SEC codes
Nacha rule for consumer e-commerce purchases

Bacs Direct Debit

Pre-authorized debit in Canada

Australia BECS Direct Debit

New Zealand BECS Direct Debit

SEPA Direct Debit

Bank redirects

Bank transfers

Meal vouchers

Credit transfers (Sources)

Buy now, pay later

Real-time payments

Vouchers

Wallets

Special regional requirements

Custom payment methods

Manage payment methods

Faster checkout with Link

Payment operations
Analytics

Balances and settlement timeCompliance and security

Currencies

Declines

Disputes

Radar fraud protection

Payouts

ReceiptsRefunds and cancellationsAdvanced integrations
Custom payment flows

Flexible acquiring

Off-Session Payments

Multiprocessor orchestration

Beyond payments
Incorporate your company

Crypto

Agentic commerce

Financial Connections

Climate

Verify identities

United States
English (United States)

Migrating to new ACH Direct Debit APIs
Learn why and how to migrate to new APIs.

Ask about this page
Copy for LLM
View as MarkdownInstall skills

Stripe is removing support for ACH Direct Debit using legacy integrations.
If you create legacy ACH Direct Debit payments, you must migrate to the Payment Intents API or Checkout Sessions API.
Feature comparison
Stripe’s new APIs offer features that aren’t available in legacy integrations:
FeatureLegacy IntegrationsPayment Intents API or Checkout Sessions APICheckout supportNoYesPayment Element supportNoYesDynamic payment method supportNoYesSettlement speedT+6T+4 (T+2 when using faster settlement)Instant bank account verificationOnly available through custom, third-party integrationsInstant verification with Financial ConnectionsFraud preventionNoRadar for ACH
Balance checks using Financial Connections
Smart Retries
Supported countriesUSUS, EU, and UK

Compare the Checkout Sessions and Payment Intents APIs
Stripe offers two new APIs to accept ACH Direct Debits payments: Payment Intents and Checkout Sessions APIs.
Checkout Sessions API: Supports common checkout workflows with built-in features that remove the need for custom code and is recommended for most developers.

Payment Intents API: A lower-level API for building your own checkout flow. It requires significantly more code and ongoing maintenance. We recommend Checkout Sessions for most integrations.

Learn more about the differences, and how to evaluate which is right for you.
Build an ACH Direct Debit integration
To build an ACH Direct Debit integration on Payment Intents or Checkout Sessions:
Enable ACH Direct Debit in your Payment methods settings.

To collect and use new payment methods, integrate with ACH on Payment Intents or Checkout Sessions.

For bank accounts previously collected using the Tokens API, you can continue to use saved BankAccount objects as PaymentMethod objects with the Payment Intents API. For details, see Migrate existing bank accounts.

Test your integration.

Gradually migrate all payments using existing bank accounts to the Payment Intents or Checkout Sessions API.

Remove your legacy integration.

Behavioral differences
Some features that exist in both APIs work differently. If you rely on any of the following behaviors, update your integration accordingly.
BehaviorLegacy IntegrationsPayment Intents or Checkout Sessions APIMandatesNot enforced by the API.Enforced by the API. Payments can’t be initiated without an active mandate.
Mandates can become inactive, which renders the payment method unusable. This can occur when a customer disputes a payment, when certain payment failures occur, or when Stripe becomes aware that the payment method is no longer valid. For more information, see Blocked bank accounts.
If you reuse bank accounts created with the Tokens API, you must first create mandates for them. See Migrate existing bank accounts.
Balance transactionsCreated when the charge is created.
The Balance transaction object is present in the charge.pending event and the API response.
Created when the payment is submitted to the banking partner.
The Balance transaction object is present in the charge.updated event, but not the API response.
Balance typeFunds settle in source_type=bank_account.Funds settle in source_type=card, shared with cards and other payment methods.
If you manually specify the balance type for payouts or Connect transfers, update your integration to use the new balance type.
During migration, you receive one payout for each balance type until all new payments use the new API.
For separate charges and transfers with source_transaction, wait for the charge.updated webhook before creating a transfer.
MicrodepositsTwo microdeposits of random, small amounts for verification.
No hosted verification UI.
One 1¢ microdeposit with a descriptor code for verification. In rare cases, Stripe sends two microdeposits of random, small amounts instead.
Stripe provides a hosted verification page and sends automatic reminder emails to customers.
Customers must verify their bank account within 10 days. If they don’t verify in time, the PaymentIntent or SetupIntent reverts to requiring new payment method details.
EmailsStripe doesn’t send automatic emails.Stripe automatically emails customers a mandate confirmation when mandates are created.
When a customer attempts to verify a bank account using microdeposits, Stripe emails customers with a link to a hosted verification page.
You can disable Stripe emails and send custom notifications instead. For sample mandate text and required content, see Mandate and microdeposit emails.

Webhook differences
If you previously listened to Charge events, you might need to update your integration to listen to new event types. The following table shows how webhook events differ.
Old webhookNew webhook on CheckoutNew webhook on Payment IntentsSpecial instructionscharge.pendingpayment_intent.processingpayment_intent.processingIn legacy integrations, charge.pending includes balance transaction. In new integrations, the balance transaction isn’t available until the charge.updated event.charge.updatedcharge.updatedcharge.updatedSent when the payment is submitted to the banking partner. Includes the balance transaction.charge.succeededcheckout.session.completedpayment_intent.succeededThe charge.succeeded webhook is also sent, so you don’t have to update your integration to listen to the new webhook.charge.failedNot applicable. The customer can re-attempt the payment on the same Checkout Session until it expires, at which point you receive a checkout.session.expired event.payment_intent.payment_failedThe charge.failed webhook is also sent, so you don’t have to update your integration to listen to the new webhook.charge.dispute.createdcharge.dispute.createdcharge.dispute.createdNot applicableNot applicablemandate.updatedmandate.updatedSent when a mandate becomes inactive.

Identify Legacy ACH Payments
On a Charge object, the payment_method_details.type property is ach_debit for the legacy integration and us_bank_account for the newer integration.
A legacy ACH payment is created when a legacy BankAccount is the payment source. This happens when:
You call the Create Charge API.
A Subscription or Invoice charges a customer whose default_source is a legacy BankAccount, and no default_payment_method is set on the customer, subscription, or invoice.
You call the PaymentIntent API with a payment_method_type of ach_debit.

On this page
