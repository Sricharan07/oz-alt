# MyViewController

**Kind:** class
**Signature:** `import UIKit`
**Source:** https://docs.stripe.com/payments/accept-a-payment.md?&ui=elements

## Example

```swift
import UIKit
import StripePaymentSheet

class MyViewController: UIViewController {

  @objc
  func didTapLogoutButton() {
    PaymentSheet.resetCustomer()
    // Other logout logic required by your app
  }

}
```
