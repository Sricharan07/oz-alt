# CheckoutActivity

**Kind:** class
**Signature:** `import com.stripe.android.paymentsheet.PaymentSheet`
**Source:** https://docs.stripe.com/payments/accept-a-payment.md?&ui=elements

## Example

```kotlin
import com.stripe.android.paymentsheet.PaymentSheet

class CheckoutActivity : AppCompatActivity() {
  lateinit var paymentSheet: PaymentSheet

  override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    paymentSheet = PaymentSheet.Builder(::onPaymentSheetResult).build(this)
  }

  fun onPaymentSheetResult(paymentSheetResult: PaymentSheetResult) {
    // implemented in the next steps
  }
}
```
