# CheckoutViewModel

**Kind:** class
**Signature:** `import StripePaymentSheet`
**Source:** https://docs.stripe.com/payments/accept-a-payment.md?&ui=elements

## Example

```swift
import StripePaymentSheet
import SwiftUI

class CheckoutViewModel: ObservableObject {
  let backendCheckoutUrl = URL(string: "Your back-end endpoint/payment-sheet")! // Your back-end endpoint
  @Published var paymentSheet: PaymentSheet?
  @Published var paymentResult: PaymentSheetResult?
}
```
