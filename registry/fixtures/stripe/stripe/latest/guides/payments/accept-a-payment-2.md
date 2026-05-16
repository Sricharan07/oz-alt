# Accept a payment

**Source:** https://docs.stripe.com/payments/accept-a-payment?payment-ui=elements&api-integration=paymentintents

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

Build a custom payment form using Stripe Elements and the Payment Intents API. See how this integration compares to Stripe’s other integration types.
The Payment Intents API is a lower-level API that you can use to build your own checkout or payments flow, but requires significantly more code and ongoing maintenance. We recommend Payment Element with Checkout Sessions for most integrations because it covers similar payment flows as Payment Intents. Learn more about when to use Checkout Sessions instead of PaymentIntents.
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
API

Integration type
Combine UI components into a custom payment flow

UI customization
CSS-level customization with the Appearance API

Interested in using Stripe Tax, discounts, shipping, or currency conversion?
Stripe has a Payment Element integration that manages tax, discounts, shipping, and currency conversion for you. See build a checkout page to learn more.

Set up StripeServer-side

First, create a Stripe account or sign in.
Use our official libraries to access the Stripe API from your application:

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

Create a PaymentIntentServer-side

Note
If you want to render the Payment Element without first creating a PaymentIntent, see Collect payment details before creating an Intent.

The PaymentIntent object represents your intent to collect payment from a customer and tracks charge attempts and state changes throughout the payment process.

Create the PaymentIntent
Create a PaymentIntent on your server with an amount and currency. In the latest version of the API, specifying the automatic_payment_methods parameter is optional because Stripe enables its functionality by default. You can manage payment methods from the Dashboard. Stripe handles the return of eligible payment methods based on factors such as the transaction’s amount, currency, and payment flow.
Stripe uses your payment methods settings to display the payment methods you’ve enabled. To see how your payment methods appear to customers, enter a transaction ID or set an order amount and currency in the Dashboard. To override payment methods, manually list any that you want to enable using the payment_method_types attribute.

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

curl https://api.stripe.com/v1/payment_intents \
  -u &quot;sk_test_REDACTED

:&quot; \
  -d amount=1099 \
  -d currency=usd \
  -d &quot;automatic_payment_methods[enabled]=true&quot;

Note
Always decide how much to charge on the server side, a trusted environment, as opposed to the client. This prevents malicious customers from being able to choose their own prices.

Retrieve the client secret
The PaymentIntent includes a client secret that the client side uses to securely complete the payment process. You can use different approaches to pass the client secret to the client side.
Single-page application

Server-side rendering

Retrieve the client secret from an endpoint on your server, using the browser’s fetch function. This approach is best if your client side is a single-page application, particularly one built with a modern frontend framework like React. Create the server endpoint that serves the client secret:

main.rb

Select a languageRuby
Python
PHP
Java
Node.js
Go
.NET
 No results

get &#x27;/secret&#x27; do
  intent = # ... Create or retrieve the PaymentIntent
  {client_secret: intent.client_secret}.to_json
end

And then fetch the client secret with JavaScript on the client side:

(async () => {
  const response = await fetch(&#x27;/secret&#x27;);
  const {client_secret: clientSecret} = await response.json();
  // Render the form using the clientSecret
})();

Collect payment detailsClient-side

Collect payment details on the client with the Payment Element. The Payment Element is a prebuilt UI component that simplifies collecting payment details for a variety of payment methods.
The Payment Element contains an iframe that securely sends payment information to Stripe over an HTTPS connection. Avoid placing the Payment Element within another iframe because some payment methods require redirecting to another page for payment confirmation.
If you choose to use an iframe and want to accept Apple Pay or Google Pay, the iframe must have the allow attribute set to equal &quot;payment *&quot;.
The checkout page address must start with https:// rather than http:// for your integration to work. You can test your integration without using HTTPS, but remember to enable it when you’re ready to accept live payments.
HTML + JS

React

Set up Stripe.js
The Payment Element is automatically available as a feature of Stripe.js. Include the Stripe.js script on your checkout page by adding it to the head of your HTML file. Always load Stripe.js directly from js.stripe.com to remain PCI compliant. Don’t include the script in a bundle or host a copy of it yourself.

checkout.html

<head>
  <title>Checkout</title>
  <script src=&quot;https://js.stripe.com/dahlia/stripe.js&quot;></script>
</head>

Create an instance of Stripe with the following JavaScript on your checkout page:

checkout.js

// Set your publishable key: remember to change this to your live publishable key in production
// See your keys here: https://dashboard.stripe.com/apikeys
const stripe = Stripe(&#x27;pk_test_REDACTED&#x27;

);

Add the Payment Element to your payment page
The Payment Element needs a place to live on your payment page. Create an empty DOM node (container) with a unique ID in your payment form:

checkout.html

<form id=&quot;payment-form&quot;>
  <div id=&quot;payment-element&quot;>
    <!-- Elements will create form elements here -->
  </div>
  <button id=&quot;submit&quot;>Submit</button>
  <div id=&quot;error-message&quot;>
    <!-- Display error message to your customers here -->
  </div>
</form>

When the previous form loads, create an instance of the Payment Element and mount it to the container DOM node. Pass the client secret from the previous step into options when you create the Elements instance:
Handle the client secret carefully because it can complete the charge. Don’t log it, embed it in URLs, or expose it to anyone but the customer.

checkout.js

const options = {
  clientSecret: &#x27;{{CLIENT_SECRET}}&#x27;,
  // Fully customizable with appearance API.
  appearance: {/*...*/},
};

// Set up Stripe.js and Elements to use in checkout form, passing the client secret obtained in a previous step
const elements = stripe.elements(options);

// Create and mount the Payment Element
const paymentElementOptions = { layout: &#x27;accordion&#x27;};
const paymentElement = elements.create(&#x27;payment&#x27;, paymentElementOptions);
paymentElement.mount(&#x27;#payment-element&#x27;);

Browse Stripe Elements
Stripe Elements is a collection of drop-in UI components. To further customize your form or collect different customer information, browse the Elements docs.
The Payment Element renders a dynamic form that allows your customer to pick a payment method. For each payment method, the form automatically asks the customer to fill in all necessary payment details.
Customize appearance
Customize the Payment Element to match the design of your site by passing the appearance object into options when creating the Elements provider.
Collect addresses
By default, the Payment Element only collects the necessary billing address details. Some behavior, such as calculating tax or entering shipping details, requires your customer’s full address. You can:
Use the Address Element to take advantage of autocomplete and localization features to collect your customer’s full address. This helps ensure the most accurate tax calculation.
Collect address details using your own custom form.
Request Apple Pay merchant token
If you’ve configured your integration to accept Apple Pay payments, we recommend configuring the Apple Pay interface to return a merchant token to enable merchant initiated transactions (MIT). Request the relevant merchant token type in the Payment Element.

OptionalSave and retrieve customer payment methods

OptionalLink in your checkout pageClient-side

OptionalFetch updates from the serverClient-side

Submit the payment to StripeClient-side

Use stripe.confirmPayment to complete the payment using details from the Payment Element. Provide a return_url to this function to indicate where Stripe should redirect the user after they complete the payment. Your user may be first redirected to an intermediate site, like a bank authorization page, before being redirected to the return_url. Card payments immediately redirect to the return_url when a payment is successful.
If you don’t want to redirect for card payments after payment completion, you can set redirect to if_required. This only redirects customers that check out with redirect-based payment methods.
HTML + JS

React

checkout.js

const form = document.getElementById(&#x27;payment-form&#x27;);

form.addEventListener(&#x27;submit&#x27;, async (event) => {
  event.preventDefault();

  const {error} = await stripe.confirmPayment({
    //`Elements` instance that was used to create the Payment Element
    elements,
    confirmParams: {
      return_url: &#x27;https://example.com/order/123/complete&#x27;,
    },
  });

  if (error) {
    // This point will only be reached if there is an immediate error when
    // confirming the payment. Show error to your customer (for example, payment
    // details incomplete)
    const messageContainer = document.querySelector(&#x27;#error-message&#x27;);
    messageContainer.textContent = error.message;
  } else {
    // Your customer will be redirected to your `return_url`. For some payment
    // methods like iDEAL, your customer will be redirected to an intermediate
    // site first to authorize the payment, then redirected to the `return_url`.
  }
});

Make sure the return_url corresponds to a page on your website that provides the status of the payment. When Stripe redirects the customer to the return_url, we provide the following URL query parameters:
ParameterDescriptionpayment_intentThe unique identifier for the PaymentIntent.payment_intent_client_secretThe client secret of the PaymentIntent object.

Caution
If you have tooling that tracks the customer’s browser session, you might need to add the stripe.com domain to the referrer exclude list. Redirects cause some tools to create new sessions, which prevents you from tracking the complete session.

Use one of the query parameters to retrieve the PaymentIntent. Inspect the status of the PaymentIntent to decide what to show your customers. You can also append your own query parameters when providing the return_url, which persist through the redirect process.
HTML + JS

React

status.js

// Initialize Stripe.js using your publishable key
const stripe = Stripe(&#x27;pk_test_REDACTED&#x27;

);

// Retrieve the &quot;payment_intent_client_secret&quot; query parameter appended to
// your return_url by Stripe.js
const clientSecret = new URLSearchParams(window.location.search).get(
  &#x27;payment_intent_client_secret&#x27;
);

// Retrieve the PaymentIntent
stripe.retrievePaymentIntent(clientSecret).then(({paymentIntent}) => {
  const message = document.querySelector(&#x27;#message&#x27;)

  // Inspect the PaymentIntent `status` to indicate the status of the payment
  // to your customer.
  //
  // Some payment methods will [immediately succeed or fail][0] upon
  // confirmation, while others will first enter a `processing` state.
  //
  // [0]: https://stripe.com/docs/payments/payment-methods#payment-notification
  switch (paymentIntent.status) {
    case &#x27;succeeded&#x27;:
      message.innerText = &#x27;Success! Payment received.&#x27;;
      break;

    case &#x27;processing&#x27;:
      message.innerText = &quot;Payment processing. We&#x27;ll update you when payment is received.&quot;;
      break;

    case &#x27;requires_payment_method&#x27;:
      message.innerText = &#x27;Payment failed. Please try another payment method.&#x27;;
      // Redirect your user back to your payment page to attempt collecting
      // payment again
      break;

    default:
      message.innerText = &#x27;Something went wrong.&#x27;;
      break;
  }
});

Handle post-payment eventsServer-side

Stripe sends a payment_intent.succeeded event when the payment completes. Use the Dashboard webhook tool or follow the webhook guide to receive these events and run actions, such as sending an order confirmation email to your customer, logging the sale in a database, or starting a shipping workflow.
Listen for these events rather than waiting on a callback from the client. On the client, the customer could close the browser window or quit the app before the callback executes, and malicious clients could manipulate the response. Setting up your integration to listen for asynchronous events is what enables you to accept different types of payment methods with a single integration.
In addition to handling the payment_intent.succeeded event, we recommend handling these other events when collecting payments with the Payment Element:
EventDescriptionActionpayment_intent.succeededSent when a customer successfully completes a payment.Send the customer an order confirmation and fulfill their order.payment_intent.processingSent when a customer successfully initiates a payment, but the payment has yet to complete. This event is most commonly sent when the customer initiates a bank debit. It’s followed by either a payment_intent.succeeded or payment_intent.payment_failed event in the future.Send the customer an order confirmation that indicates their payment is pending. For digital goods, you might want to fulfill the order before waiting for payment to complete.payment_intent.payment_failedSent when a customer attempts a payment, but the payment fails.If a payment transitions from processing to payment_failed, offer the customer another attempt to pay.

Test your integration

To test your custom payments integration:
Create a Payment Intent and retrieve the client secret.
Fill out the payment details with a method from the following table.Enter any future date for card expiry.
Enter any 3-digit number for CVC.
Enter any billing postal code.

Submit the payment to Stripe. You’re redirected to your return_url.
Go to the Dashboard and look for the payment on the Transactions page. If your payment succeeded, you’ll see it in that list.
Click your payment to see more details, like billing information and the list of purchased items. You can use this information to fulfill the order.
Learn more about testing your integration.
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

OptionalAdd more payment methods

Disclose Stripe to your customers
Stripe collects information on customer interactions with Elements to provide services to you, prevent fraud, and improve its services. This includes using cookies and IP addresses to identify which Elements a customer saw during a single checkout session. You’re responsible for disclosing and obtaining all rights and consents necessary for Stripe to use data in these ways. For more information, visit our privacy center.
See also
Stripe Elements
Set up future payments
Save payment details during payment
Calculate sales tax, GST and VAT in your payment flow

Code quickstartRelated Guides
Elements Appearance API

More payment scenarios

How cards work
