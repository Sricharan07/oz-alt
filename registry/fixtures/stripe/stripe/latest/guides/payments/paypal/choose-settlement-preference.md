# Choose settlement preference

**Source:** https://docs.stripe.com/payments/paypal/choose-settlement-preference

Choose settlement preference | Stripe Documentation

          Skip to content

Choose settlement preference

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

Bank debits

Bank redirects

Bank transfers

Meal vouchers

Credit transfers (Sources)

Buy now, pay later

Real-time payments

Vouchers

WalletsAlipay

Amazon Pay

Apple Pay

Cash App Pay

Google Pay
GrabPay

Link
MB WAY

MobilePay

PayPalPayPal button
Activate PayPal payments
Accept a payment
Set up future payments
Choose settlement preference
Disputed payments
Payout reconciliation
Import saved PayPal payment methods

PayPay

Revolut Pay

Satispay

Secure Remote Commerce
Vipps

WeChat Pay

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

Choose settlement preference
Learn about settlement modes for PayPal payments.

Ask about this page
Copy for LLM
View as MarkdownInstall skills

Settlement choice determines how you access and manage funds, use the Dashboard, perform reconciliation, and so on.
Getting started
If you’re a Connect user, your funds always settle on Stripe, similar to other payment methods. If you operate as a direct business, when you connect your PayPal and Stripe accounts you can set the funds settlement preference for your PayPal payments. Read this guide to learn more about differences between PayPal and Stripe settlement options.
If you already use PayPal through Stripe, you can check your current settlement preference on the Payment Methods Settings page in the Stripe Dashboard.
Money flow and payouts
If you settle funds from the PayPal payments on Stripe, you can access the money from your Stripe balance according to your payouts schedule, similar to other payment methods at Stripe. The funds from the payments you receive are immediately transferred from PayPal to your Stripe balance, without the need for you to take any action.
If you settle PayPal payments to PayPal, you’ll need to manage payouts on PayPal.
Refunds and disputes
Settlement on Stripe uses the funds available in your Stripe account if you want to refund a payment or need to cover the funds from a dispute, similarly to other payment methods on Stripe. If PayPal charges a fee when a dispute closes, it’s withdrawn from your Stripe balance through a Balance Transaction of type adjustment.
For settlement on PayPal, you can still manage refunds and disputes from your Stripe Dashboard, but the relevant funds are the funds on your PayPal account. If you settle on PayPal, Stripe doesn’t transfer any funds from your PayPal account to your Stripe account or vice-versa. Make sure there is always a positive balance in both accounts to cover expected refund amounts or disputes, and fees that PayPal might charge when the dispute closes.
Dashboard
If you settle your funds from PayPal payments on Stripe, the Stripe Dashboard functionality is the same as with other payment methods on Stripe.
If you settle your PayPal funds on a PayPal account, the balance transaction linked to the corresponding payment has a zero amount regardless of the payment, because funds settle in your PayPal balance, and no money goes to your Stripe balance.
Additionally, the Gross and Net volume charts won’t reflect your sales volume from PayPal if you settle your funds on a PayPal account. In this case, we recommend using the Payment methods report to track the volume from PayPal sales.
The payment details view is also different if you settle your PayPal funds to your PayPal account. The Net value reflects the change on the net volume of your Stripe balance. This is a negative value of the fee amount that Stripe takes for the payment.
Reconciliation impact
Reconciliation is the process of matching and verifying payments that have been received and processed with the corresponding PayPal orders.
When settling your funds on Stripe, you get automatic transactions reconciliation.
If you settle on PayPal, you need to manually reconcile the transactions. Learn about how Stripe provides support for PayPal transaction reconciliation.
Changing your settlement preference
If for any reason you need to change your current settlement mode, you can initiate the process from the Stripe Dashboard.
Go to the Payment Methods Settings page.
Find PayPal settings.
Click Contact Support to change. You’ll be redirected to the FAQ page where you can file a support ticket.
File a support ticket to request a change.
The change shows up in the PayPal settings accordingly.
Currency conversions
A currency conversion occurs when the presentment currency differs from the settlement currency. See currency conversions for more information. Prevent currency conversions by adding a settlement currency for every currency you present to your customers.

On this page
