# The FX Quotes APIPublic preview

**Source:** https://docs.stripe.com/payments/currencies/localize-prices/fx-quotes-api

The FX Quotes API | Stripe Documentation

          Skip to content

FX Quotes API

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

CurrenciesOverview
Localize pricesAdaptive Pricing
FX Quotes API
Manual currency prices

Settle in additional currencies

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

Public previewThe FX Quotes APIPublic preview
Select which currencies to localize, lock in exchange rates, and decide whether to pass along fees to your customers.

Ask about this page
Copy for LLM
View as MarkdownInstall skills

Displaying prices in a customer’s local currency can improve conversion rates and payment authorization rates. To convert currencies, you must account for:
The appropriate foreign currency amounts to display on your site before checkout.
The current exchange rates and foreign exchange (FX) fees for transactions.
The amount of money credited to your Stripe balance in your currency.
The frequency of exchange rate changes and when to update localized prices.
The FX Quotes API provides the following currency conversion capabilities:
Current exchange rates: Stripe’s current exchange rate for any given currency pair.
Extended exchange rate quotes: Create a 5 minute, 1 hour, or 24 hour rate quote to reduce the uncertainty from FX fluctuations.
FX fee information: Details about Stripe’s FX fees for your transactions, helping you estimate settlement amounts before payment costs.
Terms of use
Merchant Category Codes (MCC) restriction
Stripe doesn’t support the FX Quotes API for certain MCCs. Use the form at the bottom of this page to request access.
By using the FX Quotes API, you agree to the following Terms of Service:
The FX Quotes API is currently offered as a preview service. This means Stripe offers the service “as is” and disclaims all expressed or implied warranties and guarantees around this service. You’re relying on a preview service at your own risk and Stripe isn’t liable for losses, damages, or costs arising that relate to the accuracy of the preview service.
The FX Quotes API might provide you with a quote for a specific currency pair that’s valid for a period of time in the future. This is called an Extended Rate Quote. This quote isn’t an offer to enter into foreign exchange, and we can withdraw it at any time.
Use of the FX Quotes API and Extended Rate Quotes must be used as part of a commercial transaction of goods and services you sell on Stripe.
Extended Rate Quotes can help you manage general uncertainty in foreign exchange (FX) rates. You’re not permitted to selectively use Extended Rate Quotes in certain situations but not others. For example, you cannot only use Extended Rate Quotes in instances where the market FX rate is less favorable than the Extended Rate Quote.
Stripe might add or remove supported currencies from the FX Quotes API at any time, without notice.
Set up to use the FX Quotes API
If you’re using the SDK, refer to SDK versioning to add configurations to access preview features. If you call the API endpoints directly instead of using the SDK, make sure you’re using a preview API version in the API call.
Use Stripe&#x27;s SDK

Call the API directly

Below is a sample for Ruby. You can run the equivalent command for all SDKs in other languages.
gem install stripe -v 14.0.0-beta.1

Sample Ruby SDK

require &#x27;stripe&#x27;
# Don&#x27;t put any keys in code. See https://docs.stripe.com/keys-best-practices.
client = Stripe::StripeClient.new(&#x27;sk_test_REDACTED&#x27;

, stripe_version: &#x27;2025-07-30.preview&#x27;)

Set the optimal localized price
Using the rates from the FX Quotes API, you can set your localized prices for other countries based on the price you charge customers in your home country. When finalizing your localized prices, consider any local market pricing nuances and whether you want to round prices to the nearest whole number.
To make sure that you receive the same amount regardless of the currency your customer pays in, you can pass Stripe’s FX fee to the customer. For example, say you’re a US-based merchant who wants to sell your 100 USD product in France. To calculate the equivalent price in EUR, use the exchange_rate parameter to pass the FX fee to the customer. If you don’t want to pass on this fee, use the base_rate parameter. The following example response shows a quote created to convert prices presented in the local currency, EUR, to your settlement currency, USD:

fx_quote.json

{
  &quot;id&quot;: &quot;fxq_1R6BWhL05bA97JHQELB5EROs&quot;,
  &quot;object&quot;: &quot;fx_quote&quot;,
  &quot;created&quot;: 1742824731,
  &quot;lock_duration&quot;: &quot;five_minutes&quot;,
  &quot;lock_expires_at&quot;: 1742825031,
  &quot;lock_status&quot;: &quot;active&quot;,
  &quot;to_currency&quot;: &quot;usd&quot;,
  &quot;rates&quot;: {
    &quot;eur&quot;: {
      &quot;exchange_rate&quot;: 1.06053,
      &quot;rate_details&quot;: {
        &quot;base_rate&quot;: 1.08295,
        &quot;duration_premium&quot;: 0.0007,
        &quot;fx_fee_rate&quot;: 0.02,
        &quot;reference_rate&quot;: 1.0827,
        &quot;reference_rate_provider&quot;: &quot;ecb&quot;
      }
    }
  },
  &quot;usage&quot;: {
    &quot;payment&quot;: {
      &quot;destination&quot;: null,
      &quot;on_behalf_of&quot;: null
    },
    &quot;transfer&quot;: null,
    &quot;type&quot;: &quot;payment&quot;
  }
}

Using the above example, to pass on the FX fee to the customer, divide the product price (100 USD) by the exchange rate (1.06053) to get the price for your customers in France inclusive of the FX fee: 94.29 EUR. If you don’t want to pass on the FX fee, divide the product price (100 USD) by the base rate (1.08295) for the price excluding the FX fee: 92.34 EUR. Cross-border transactions also carry an international payment method fee, depending on the geography and payment method. See Stripe’s pricing page for more details.
Quote durations and rate changes
If you’re interested in a longer quote lock_duration, contact us using the form at the bottom of this page.
When you localize your pricing using exchange rate information provided by the FX Quotes API, you might want certainty around how long a given rate is valid. The FX Quotes API offers three time periods for lock_duration: five_minutes, hour, and day. This duration indicates that your transaction will be converted at the quoted exchange rate as long as you use the provided rate before it expires, as indicated by lock_expires_at.
The FX Quotes API also provides exchange rate information for the current live Stripe exchange rate. For this, set lock_duration to none.
When lock_duration is set to 5 minutes, 1 hour, or 1 day, the duration_premium field includes the fee charged for the extended rate quote. To determine the right lock duration, consider how regularly local prices are refreshed and how long a checkout session lasts.
Currency markets might experience volatility, affecting our ability to honor a given quote. An extended rate quote created for payments has a 3.5% rate threshold, and an extended rate quote for transfers has a 1% rate threshold. If an exchange rate exceeds these thresholds, the extended rate quote is invalidated, with lock_status changing to expired.
When you use an expired quote for a PaymentIntent or Transfer, you receive an error.code of either payment_intent_fx_quote_invalid or transfers_fx_quote_invalid. You can use these error codes to handle expired quotes.
Use locked exchange rates to localize prices
As an example, if you’re a UK-based merchant that localizes prices for US customers, and you want to receive 100 GBP regardless of changes in the USD-GBP exchange rate. In this scenario, we recommend fetching an extended rate quote with a lock_duration of hour:

Command Line

Select a languagecURL
 No results

curl https://api.stripe.com/v1/fx_quotes \
  -u &quot;sk_test_REDACTED

:&quot; \
  -d to_currency=gbp \
  -d &quot;from_currencies[]=usd&quot; \
  -d lock_duration=day

European Central Bank reference rates
If you want to show the European Central Bank’s exchange rates as a reference, the FX Quotes object contains all of the rates that the European Central Bank supports.
If the latest exchange rate for USD is, for example, 0.8, divide your price (100 GBP) by the exchange rate (0.8) to calculate your localized price: 125 USD. Because this exchange rate is locked for the next hour, you can show 125 USD to your US customers, from your site to the checkout page.
You can pass your US price 125 USD into the Payment Intents API to make the payment using the fx_quote parameter:

Command Line

Select a languagecURL
 No results

curl https://api.stripe.com/v1/payment_intents \
  -u &quot;sk_test_REDACTED

:&quot; \
  -d amount=125 \
  -d currency=usd \
  -d fx_quote=fxq_1QBck4FTKRd55CNDdboZYz9g

Handle minor units
Disputes and Refunds
Stripe converts disputed or refunded payments back to the presentment currency at the current exchange rate, instead of at the previous rate.
All API requests expect amount values in the currency’s minor unit. After using the rates provided by the FX Quotes API, convert the resulting converted amount into Stripe’s minor units. See Minor units in API amounts and Zero-decimal currenciesfor more details.
Handle quote expiry
Stripe sends an fx_quote.expired webhook when a quote becomes invalid due to expiration or significant rate drifts. Attaching an already expired FX Quote object to the PaymentIntent API or Transfer API returns a 400 status code. We recommend subscribing to the fx_quote.expired webhook event and creating a new extended rate quote after receiving the event so that localized prices can be updated based on the new FX Quote object.
Mid-market rate fallback
Some non-card payment methods take longer to process payments than a 24-hour locking period covers. For these payments, the extended rate quote might expire or become unusable because of significant mid-market rate changes. In these cases, we use the mid-market rate to process the payment.
Pricing
We don’t charge for extended rate quotes with a lock duration of none. When lock_duration is set to five_minutes, hour, or day, Stripe charges a fee to cover the risk and cost incurred. You can see this fee in the duration_premium field and it’s added to the base_rate to calculate the exchange_rate.
The exact fee depends on the lock_duration, and the currency pair used for the currency conversion. Refer to the table below to calculate the fee for an extended rate quote. If you’re converting from a currency in Group 2 to a currency in Group 1 (or the other way around), the fee listed for Group 2 applies. For example, a USD-KRW currency pair with a 1-hour duration has a 0.15% fee because KRW is in Group 2. If both currencies are in the same group, the fee for that group applies.
The FX Quote API only supports the currencies in the following two groups:
Group5 minutes1 hour24 hours

Group 1: aed, aud, awg, bbd, bhd, bmd, bsd, cad, chf, dkk, eur, gbp, hkd, idr, inr, jod, jpy, kwd, myr, nzd, omr, pab, ron, sar, sek, sgd, thb, usd, xcd, yer0.07%0.10%0.20%Group 2: afn, all, amd, ang, aoa, azn, bam, bdt, bif, bnd, bob, brl, bwp, bzd, clp, cny, cop, crc, cve, czk, djf, dop, dzd, fkp, gel, gip, gmd, gnf, gtq, gyd, hnl, htg, huf, ils, isk, jmd, kes, kgs, khr, krw, kyd, kzt, lkr, lrd, mad, mdl, mga, mkd, mnt, mop, mur, mvr, mxn, mzn, nad, nok, npr, pen, php, pkr, pln, pyg, qar, rsd, rwf, shp, std, tjs, tnd, try, ttd, twd, tzs, uah, ugx, uyu, uzs, vnd, xaf, xof, xpf, zar, zmw0.12%0.15%0.30%

Availability Preview
The FX Quotes API is available in the following countries, and you can use it to display localized prices in the supported currencies:
Austria
Belgium
Bulgaria
Canada
Croatia
Cyprus
Czech Republic
Denmark
Estonia
Finland
France
Germany
Gibraltar
Greece
Hungary
Ireland
Italy
Latvia
Lithuania
Luxembourg
Malta
Netherlands
Norway
Poland
Portugal
Romania
Slovakia
Slovenia
Spain
Sweden
Switzerland
United Kingdom
United States

On this page
