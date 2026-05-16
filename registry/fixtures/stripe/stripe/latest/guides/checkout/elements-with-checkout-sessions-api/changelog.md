# Elements with Checkout Sessions API beta changelog

**Source:** https://docs.stripe.com/checkout/elements-with-checkout-sessions-api/changelog

Elements with Checkout Sessions API beta changelog | Stripe Documentation

          Skip to content

Elements with Checkout Sessions API beta changelog

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

Build a custom integration with ElementsOverview
Quickstart guides

Stripe Elements

Compare Checkout Sessions and PaymentIntents
Design an advanced integration
Customize look and feel
Manage payment methods

Collect additional information

Build a subscriptions integration
Dynamic updates

Add discounts
Collect taxes on your payments
Collect surcharges
Redeem credits
Let customers pay in their local currency

Save and retrieve customer payment methods

Send receipts and paid invoices
Manually approve payments on your server
Authorize and capture a payment separately
Elements with Checkout Sessions API beta changelog

Build an in-app integration

Use Managed Payments

Use Checkout studio

Recurring paymentsIn-person payments
Terminal

Payment methods
Add payment methods

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

Elements with Checkout Sessions API beta changelog
Keep track of changes to the Elements with Checkout Sessions API beta integration.

Ask about this page
Copy for LLM
View as MarkdownInstall skills

Warning
This doc contains changelogs related to beta versions of Elements with Checkout Sessions API.
This changelog doesn’t apply to you if you’re on Clover or later. Refer to the Stripe changelog instead.

Migrating to Clover
Clover changes
Breaking The stripe.initCheckout method is now synchronous instead of asynchronous. This reduces render latency and enables Elements to show skeleton loaders earlier. See Updates initCheckout to be synchronous for migration details.
Breaking Saved payment methods are now automatically enabled in the Payment Element when configured on the Checkout Session, without requiring additional client-side configuration. See Updates default behavior for saved payment methods for details.
Breaking Postal codes are no longer automatically collected for card payments in Canada, UK, and Puerto Rico. See Removes postal code for card payments if you rely on this data.
Breaking For React integrations:Import paths have changed from @stripe/react-stripe-js to @stripe/react-stripe-js/checkout.
useCheckout now returns a disjoint union describing the asynchronous state ({type: &#x27;loading&#x27;}, {type: &#x27;success&#x27;, checkout: ...}, or {type: &#x27;error&#x27;, error: ...}) instead of throwing an error.
CheckoutProvider now renders children unconditionally instead of rendering null when initCheckout hasn’t succeeded.

Clover upgrade
Before migrating to Clover, first update your integration to Basil.
If you’re using any Stripe NPM packages, you must upgrade @stripe/stripe-js to at least 8.0.0 and @stripe/react-stripe-js to at least 5.0.0.
If you’re loading Stripe.js through the script tag, update the tag to reference clover using the versioned Stripe.js nomenclature as follows:

checkout.html

<head>
  <title>Checkout</title>
  <script src=&quot;https://js.stripe.com/basil/stripe.js&quot;></script>
  <script src=&quot;https://js.stripe.com/clover/stripe.js&quot;></script>
</head>

Update the API version to be at least 2025-09-30.clover on your back-end integration.
HTML + JS

React

Update your integration as follows:
Remove any await or .then() calls associated with initCheckout.
Replace your fetchClientSecret function with a client secret string or Promise that resolves to a client secret string.
Call the new asynchronous function checkout.loadActions() to access actions such as getSession(), which replaces session(), or confirm(). You only need to call loadActions() once.
If you previously wrapped initCheckout in a try...catch block, examine the resolved type value of loadActions() instead to check for errors.

checkout.js

const clientSecret = fetch(&quot;/create-checkout-session&quot;, {
  method: &quot;POST&quot;,
  headers: { &quot;Content-Type&quot;: &quot;application/json&quot; },
})
  .then((r) => r.json())
  .then((r) => r.clientSecret);

const checkout = await stripe.initCheckout({
  fetchClientSecret: () => clientSecret
});
const checkout = stripe.initCheckout({
  clientSecret
});
const paymentElement = checkout.createPaymentElement();
paymentElement.mount(&quot;#payment-element&quot;);

const session = checkout.session();
const loadActionsResult = await checkout.loadActions();
if (loadActionsResult.type === &#x27;success&#x27;) {
  const session = loadActionsResult.actions.getSession();
}

For more details, see the Updates initCheckout to be synchronous changelog entry.
Migrating to Basil
Basil changes
Breaking Asynchronous methods, such as confirm or applyPromotionCode, resolve with a different schema:If successful, the updated session state is populated under the session key. Previously, this was under the success key.

Breaking An error is now thrown when passing in returnUrl on confirm when return_url has been already set on the Checkout Session.
Breaking The return URL redirected to after a successful confirmation previously had inconsistent query parameters. Extra parameters are now removed and the URL only contains what’s provided in returnUrl on confirm or return_url on the Checkout Session.
Breaking Improves latency on Checkout Session API for subscription-mode Sessions and fixes a bug that prevented your customers from updating a Session after the first payment attemptThe change creates the subscription after the user has completed the payment, so checkout_session.invoice and checkout_session.subscription are null until the Checkout Session completes.
If you currently rely on the deprecated payment_intent.invoice field, we recommend using the checkout_session.completed webhook, which ensures an invoice is present, and checkout_session.invoice or Invoice Payment list to find the associated invoice.
To learn more, read the 2025-03-31.basil API changelog.

Added percentOff to discountAmounts as an option to display discounts.
Basil upgrade
Before migrating to Basil, first update your integration to custom_checkout_beta_6.
If you’re using any Stripe NPM packages, you must first upgrade @stripe/stripe-js to at least 7.0.0 and @stripe/react-stripe-js to at least 3.6.0.
If you’re loading Stripe.js through the script tag, and you’re still using v3 or acacia, update the tag to reference basil using the versioned Stripe.js nomenclature as follows:

checkout.html

<head>
  <title>Checkout</title>
  <script src=&quot;https://js.stripe.com/v3/stripe.js&quot;></script>
  <script src=&quot;https://js.stripe.com/basil/stripe.js&quot;></script>
</head>

Remove the Stripe.js beta header when initializing Stripe.js.
HTML + JS

React

checkout.js

const stripe = Stripe(
  &#x27;pk_test_REDACTED&#x27;

, {
  betas: [&#x27;custom_checkout_beta_6&#x27;],
  }
);

Remove the API version beta header and specify the API version to be at least 2025-03-31.basil on your back-end integration.
Before
After

Select a languageTypeScript
Node.js
Ruby
PHP
Python
Go
.NET
Java
 No results

// Set your secret key. Remember to switch to your live secret key in production.
// See your keys here: https://dashboard.stripe.com/apikeys
import Stripe from &#x27;stripe&#x27;;
// Don&#x27;t put any keys in code. See https://docs.stripe.com/keys-best-practices.
const stripe = new Stripe(&#x27;sk_test_REDACTED&#x27;

, {
  apiVersion: &#x27;2026-04-22.dahlia; custom_checkout_beta=v1&#x27; as any,
});

Select a languageTypeScript
Node.js
Ruby
PHP
Python
Go
.NET
Java
 No results

// Set your secret key. Remember to switch to your live secret key in production.
// See your keys here: https://dashboard.stripe.com/apikeys
import Stripe from &#x27;stripe&#x27;;
// Don&#x27;t put any keys in code. See https://docs.stripe.com/keys-best-practices.
const stripe = new Stripe(&#x27;sk_test_REDACTED&#x27;

, {
  apiVersion: &#x27;2025-03-31.basil&#x27; as any,
});

Beta changelog
Elements with Checkout Sessions API beta uses two kinds of beta versions:
A Stripe.js beta header (for example, custom_checkout_beta_6), which is set on your front-end integration.
An API version beta header (for example, custom_checkout_beta=v1), which is set on your back-end integration.
Front-end beta versions
Specify the front-end beta version when initializing Stripe.js.
custom_checkout_beta_6
If you’re using any Stripe NPM packages, you must first upgrade @stripe/stripe-js to at least 6.1.0 and @stripe/react-stripe-js to at least 3.5.0.
Breaking The sign of total.appliedBalance has been flipped. A positive number now increases the amount to be paid, and a negative number decreases the amount to be paid.
Breaking Replaced clientSecret with fetchClientSecret. Update your integration to pass an async function resolving to the client secret instead of passing a static value.
Breaking Elements methods has been renamed.If you’re using React Stripe.js, you don’t need to do anything except upgrade @stripe/react-stripe-js.
If you’re using HTML/JS:Use createPaymentElement() instead of createElement(&#x27;payment&#x27;).
Use createBillingAddressElement() instead of createElement(&#x27;address&#x27;, {mode: &#x27;billing&#x27;}).
Use createShippingAddressElement() instead of createElement(&#x27;address&#x27;, {mode: &#x27;shipping&#x27;}).
Use createExpressCheckoutElement() instead of createElement(&#x27;expressCheckout&#x27;).
Use getPaymentElement() instead of getElement(&#x27;payment&#x27;).
Use getBillingAddressElement() instead of getElement(&#x27;address&#x27;, {mode: &#x27;billing&#x27;}).
Use getShippingAddressElement() instead of getElement(&#x27;address&#x27;, {mode: &#x27;shipping&#x27;}).
Use getExpressCheckoutElement() instead of getElement(&#x27;expressCheckout&#x27;).

Breaking Updated fields related to confirmation to more accurately reflect session state.canConfirm now responds to any mounted Billing Address Element or Shipping Address Element.
canConfirm now becomes false if there is an in-flight confirmation.
Removed confirmationRequirements.

Breaking updateEmail now throws an error if customer_email was provided when creating the Checkout Session. If you intend to prefill an email that your customer can update, call updateEmail as soon as the page loads instead of passing customer_email.
Breaking returnUrl must be an absolute URL (for example, starts with https:// rather than a relative URL, like /success).
Breaking Updated pricing fields to a nested object for ease of rendering.Replaced numeric values with an object containing amount (a formatted currency string, such as $10.00) and minorUnitsAmount, an integer representing the value in the currency’s smallest unit. If you’re already reading the amount, read instead from minorUnitsAmount.For example, replace total.total with total.total.minorUnitsAmount.

You must either read total.total.amount or each of total.total.minorUnitsAmount and currency and minorUnitsAmountDivisor from the checkout object and display in your UI, otherwise an error will be thrown. This helps keep your checkout page in sync as the CheckoutSession updates, including adding future Stripe features, with minimal UI code changes.

Customer tax IDs can now be collected. Learn how to collect tax IDs.
A test mode-only assistant is now available at the bottom of your checkout page, offering guidance for your integration and shortcuts for common test scenarios.
custom_checkout_beta_5
Breaking The initCustomCheckout function has been renamed to initCheckoutWithin React Stripe.js, CustomCheckoutProvider has been renamed to CheckoutProvider and useCustomCheckout has been renamed to useCheckout.

Breaking To confirm the Express Checkout Element, call confirm, passing the confirm event as expressCheckoutConfirmEvent.Previously, Express Checkout Element was confirmed by calling event.confirm().

Breaking When confirm is called, Payment Element and Address Element will validate form inputs and render any errors.
Breaking Error messages have been standardized and improved.Errors returned/resolved by a function represent known scenarios like invalid payment details or insufficient funds. These are predictable issues that can be communicated to your customer by displaying the message on the checkout page.
Errors thrown/rejected by a function represent errors in the integration itself, such as invalid parameters or configuration. These errors aren’t meant to be displayed to your customers.

Breaking Asynchronous methods, such as confirm or applyPromotionCode, resolve with a different schema:A type=&quot;success&quot;|&quot;error&quot; discriminator field has been added.
If successful, the updated session state is populated under the success key. Previously, this was under the session key.
Otherwise, the error continues to be populated under the error key.

Added the email, phoneNumber, billingAddress, and shippingAddress options to confirm.
Breaking Address Element no longer automatically updates the billingAddress or shippingAddress fields on the Session.So long as Address Element is mounted, form values will automatically be used when calling confirm.
Listen to the change event to use the Address Element value before confirmation.

custom_checkout_beta_4
Added images to the Session object.
Added fields as an option when creating the Payment Element.
Added paymentMethods as an option when creating the Express Checkout Element.
Breaking Passing invalid options to createElement now throws an error. Previously, unrecognized options would be silently ignored.
Breaking updateEmail and updatePhoneNumber apply changes asynchronously. Calling these methods before the customer finishes entering complete values might cause poor performance.Instead of calling updateEmail or updatePhoneNumber on each input’s change event, wait until your customer finishes the input, such as on input blur or when they submit the form for payment.
updateEmail now validates that the input is a properly formed email address and returns an error if an invalid input is used.
updatePhoneNumber still performs no validation on the input string.

custom_checkout_beta_3
The following fields have been added to the Session object:id
livemode
businessName

Saved cards can now be reused. Learn how to save and reuse payment methods.
Breaking The default layout of the Payment Element has been changed to accordion.To continue using the previous default layout, you must explicitly specify layout=&#x27;tabs&#x27;.

Breaking The default behavior of confirm has been changed to always redirect to your return_url after a successful confirmation.Previously, confirm redirected only if the customer chooses a redirect-based payment method. To continue using the old behavior, you must pass redirect=‘if_required’ to confirm.

custom_checkout_beta_2
Breaking The lineItem.recurring.interval_count field has been removed and replaced with lineItem.recurring.intervalCount.
Breaking The lineItem.amount field has been removed and replaced with the following:lineItem.amountSubtotal
lineItem.amountDiscount
lineItem.amountTaxInclusive
lineItem.amountTaxExclusive

custom_checkout_beta_1
This is the initial front-end beta version.
Back-end versions
Specify the back-end beta version when setting up your server library.
There are no changes to the back-end beta version.

On this page
