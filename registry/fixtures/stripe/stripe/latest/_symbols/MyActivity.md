# MyActivity

**Kind:** class
**Signature:** `class MyActivity: Activity {`
**Source:** https://docs.stripe.com/payments/accept-a-payment.md?&ui=elements

## Example

```kotlin
class MyActivity: Activity {

  fun onLogoutButtonClicked() {
    PaymentSheet.resetCustomer(this)
    // Other logout logic required by your app
  }
}
```
