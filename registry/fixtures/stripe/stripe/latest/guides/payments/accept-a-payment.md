# Accept a payment

**Source:** https://docs.stripe.com/payments/accept-a-payment?payment-ui=elements&api-integration=checkout

Accept a payment | Stripe Documentation

          Skip to content

Accept a payment

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

Accept a payment
Securely accept payments online.

Ask about this page
Copy for LLM
View as MarkdownInstall skills

Build a payment form or use a prebuilt checkout page to start accepting online payments.
Not a developer?
Use Stripe’s no-code options or apps from our partners to get started and do more with your Stripe account—no code required. If you use a third-party platform to build and maintain a website, you can add Stripe payments with a plugin.

Checkout

Elements

Mobile

Checkout Sessions API

Payment Intents API

Build a custom payment form using Stripe Elements and the Checkout Sessions API. See how this integration compares to Stripe’s other integration types.
The Checkout Sessions API provides built-in support for tax calculation, discounts, shipping, and currency conversion, reducing the amount of custom code you need to write. This is the recommended approach for most integrations. Learn more about when to use Checkout Sessions instead of PaymentIntents.
The client-side and server-side code builds a checkout form that accepts various payment methods.
Customer location

United States (USD)

Size

Desktop

Theme

Stripe

Layout

Accordion

To see how Link works for a returning user, enter the email demo@stripe.com. To see how Link works during a new signup, enter any other email and complete the rest of the form. This demo only displays Google Pay or Apple Pay if you have an active card with either wallet.

Integration effort
Some code

Integration type
Combine UI components into a custom payment flow

UI customization
CSS-level customization with the Appearance API

Set up the serverServer-side

Before you begin, you need to register for a Stripe account.
Use the official Stripe libraries to access the API from your application.

Command Line

Select a languageRuby
Python
PHP
Java
Node.js
Go
.NET
 No results

# Available as a gem
sudo gem install stripe

Gemfile

Select a languageRuby
Python
PHP
Java
Node.js
Go
.NET
 No results

# If you use bundler, you can add this line to your Gemfile
gem &#x27;stripe&#x27;

Create a Checkout SessionServer-side

Add an endpoint on your server that creates a Checkout Session and returns its client_secret to your front end. A Checkout Session represents your customer’s session as they pay for one-time purchases or subscriptions. Checkout Sessions expire 24 hours after creation.

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

curl https://api.stripe.com/v1/checkout/sessions \
  -u &quot;sk_test_REDACTED

:&quot; \
  -d ui_mode=elements \
  -d &quot;line_items[0][price_data][currency]=usd&quot; \
  -d &quot;line_items[0][price_data][product_data][name]=T-shirt&quot; \
  -d &quot;line_items[0][price_data][unit_amount]=2000&quot; \
  -d &quot;line_items[0][quantity]=1&quot; \
  -d mode=payment \
  --data-urlencode &quot;return_url=https://example.com/return?session_id={CHECKOUT_SESSION_ID}&quot;

Set up the front endClient-side

HTML + JS

React

Include the Stripe.js script on your checkout page by adding it to the head of your HTML file. Always load Stripe.js directly from js.stripe.com to remain PCI compliant. Don’t include the script in a bundle or host a copy of it yourself.
Make sure you’re using the latest Stripe.js version. Learn more about Stripe.js versioning.

checkout.html

<head>
  <title>Checkout</title>
  <script src=&quot;https://js.stripe.com/dahlia/stripe.js&quot;></script>
</head>

Note
Stripe provides an npm package that you can use to load Stripe.js as a module. See the project on GitHub. Version 7.0.0 or later is required.

Initialize stripe.js.

checkout.js

// Set your publishable key: remember to change this to your live publishable key in production
// See your keys here: https://dashboard.stripe.com/apikeys
const stripe = Stripe(
  &#x27;pk_test_REDACTED&#x27;

,
);

Initialize CheckoutClient-side

HTML + JS

React

Call initCheckoutElementsSdk, passing in clientSecret.
initCheckoutElementsSdk returns a Checkout object that contains data from the Checkout Session and methods to update it.
Read the total and lineItems from actions.getSession(), and display them in your UI. This lets you turn on new features with minimal code changes. For example, adding manual currency prices requires no UI changes if you display the total.

checkout.html

<div id=&quot;checkout-container&quot;></div>

checkout.js

const clientSecret = fetch(&#x27;/create-checkout-session&#x27;, {method: &#x27;POST&#x27;})
  .then((response) => response.json())
  .then((json) => json.client_secret);

const checkout = stripe.initCheckoutElementsSdk({clientSecret});
const loadActionsResult = await checkout.loadActions();

if (loadActionsResult.type === &#x27;success&#x27;) {
  const session = loadActionsResult.actions.getSession();
  const checkoutContainer = document.getElementById(&#x27;checkout-container&#x27;);

  checkoutContainer.append(JSON.stringify(session.lineItems, null, 2));
  checkoutContainer.append(document.createElement(&#x27;br&#x27;));
  checkoutContainer.append(`Total: ${session.total.total.amount}`);
}

Collect customer emailClient-side

HTML + JS

React

You must provide a valid customer email when completing a Checkout Session.
These instructions create an email input and use updateEmail from the Checkout object.
Alternatively, you can:
Pass in customer_email, customer_account (for customers represented as customer-configured Account objects), or customer (for customers represented as Customer objects) when creating the Checkout Session. Stripe validates emails provided this way.
Pass in an email you already validated on checkout.confirm.

checkout.html

<input type=&quot;text&quot; id=&quot;email&quot; />
<div id=&quot;email-errors&quot;></div>

checkout.js

const checkout = stripe.initCheckoutElementsSdk({clientSecret});
const loadActionsResult = await checkout.loadActions();

if (loadActionsResult.type === &#x27;success&#x27;) {
  const {actions} = loadActionsResult;
  const emailInput = document.getElementById(&#x27;email&#x27;);
  const emailErrors = document.getElementById(&#x27;email-errors&#x27;);

  emailInput.addEventListener(&#x27;input&#x27;, () => {
    // Clear any validation errors
    emailErrors.textContent = &#x27;&#x27;;
  });

  emailInput.addEventListener(&#x27;blur&#x27;, () => {
    const newEmail = emailInput.value;
    actions.updateEmail(newEmail).then((result) => {
      if (result.error) {
        emailErrors.textContent = result.error.message;
      }
    });
  });
}

Collect payment detailsClient-side

Collect payment details on the client with the Payment Element. The Payment Element is a prebuilt UI component that simplifies collecting payment details for a variety of payment methods.
The Payment Element contains an iframe that securely sends payment information to Stripe over an HTTPS connection. Avoid placing the Payment Element within another iframe because some payment methods require redirecting to another page for payment confirmation.
If you choose to use an iframe and want to accept Apple Pay or Google Pay, the iframe must have the allow attribute set to equal &quot;payment *&quot;.
The checkout page address must start with https:// rather than http:// for your integration to work. You can test your integration without using HTTPS, but remember to enable it when you’re ready to accept live payments.
HTML + JS

React

First, create a container DOM element to mount the Payment Element. Then create an instance of the Payment Element using checkout.createPaymentElement and mount it by calling element.mount, providing either a CSS selector or the container DOM element.

checkout.html

<div id=&quot;payment-element&quot;></div>

checkout.js

const paymentElement = checkout.createPaymentElement();
paymentElement.mount(&#x27;#payment-element&#x27;);

See the Stripe.js docs to view the supported options.
You can customize the appearance of all Elements by passing elementsOptions.appearance when initializing Checkout on the front end.

Submit the paymentClient-side

HTML + JS

React

Render a Pay button that calls confirm from the Checkout instance to submit the payment.

checkout.html

<button id=&quot;pay-button&quot;>Pay</button>
<div id=&quot;confirm-errors&quot;></div>

checkout.js

const checkout = stripe.initCheckoutElementsSdk({clientSecret});

checkout.on(&#x27;change&#x27;, (session) => {
  document.getElementById(&#x27;pay-button&#x27;).disabled = !session.canConfirm;
});

const loadActionsResult = await checkout.loadActions();

if (loadActionsResult.type === &#x27;success&#x27;) {
  const {actions} = loadActionsResult;
  const button = document.getElementById(&#x27;pay-button&#x27;);
  const errors = document.getElementById(&#x27;confirm-errors&#x27;);
  button.addEventListener(&#x27;click&#x27;, () => {
    // Clear any validation errors
    errors.textContent = &#x27;&#x27;;

    actions.confirm().then((result) => {
      if (result.type === &#x27;error&#x27;) {
        errors.textContent = result.error.message;
      }
    });
  });
}

Test your integration

Navigate to your checkout page.
Fill out the payment details with a payment method from the following table. For card payments:Enter any future date for card expiry.
Enter any 3-digit number for CVC.
Enter any billing postal code.

Submit the payment to Stripe.
Go to the Dashboard and look for the payment on the Transactions page. If your payment succeeded, you’ll see it in that list.
Click your payment to see more details, like billing information and the list of purchased items. You can use this information to fulfill the order.
Cards

Wallets

Bank redirects

Bank debits

Vouchers

Card numberScenarioHow to test4242424242424242
The card payment succeeds and doesn’t require authentication.Fill out the credit card form using the credit card number with any expiration, CVC, and postal code.4000002500003155
The card payment requires authentication.Fill out the credit card form using the credit card number with any expiration, CVC, and postal code.4000000000009995
The card is declined with a decline code like insufficient_funds.Fill out the credit card form using the credit card number with any expiration, CVC, and postal code.6205500000000000004
The UnionPay card has a variable length of 13-19 digits.Fill out the credit card form using the credit card number with any expiration, CVC, and postal code.

See Testing for additional information to test your integration.

OptionalCreate products and prices

OptionalPrefill customer dataServer-side

OptionalSave payment method details

OptionalListen for Checkout Session changes

OptionalCollect billing and shipping addresses

OptionalSeparate authorization and captureServer-side

OptionalCustomer account managementNo code

OptionalOrder fulfillment

See also
Add discounts for one-time payments
Collect taxes
Enable adjustable line item quantities
Add one-click buttons
Sample project on GitHub

Code quickstartRelated Guides
Elements Appearance API

More payment scenarios

How cards work
