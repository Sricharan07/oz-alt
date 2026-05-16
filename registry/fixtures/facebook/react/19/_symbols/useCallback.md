# useCallback

**Kind:** expected
**Signature:** `useCallback`
**Source:** https://react.dev/reference/react/useMemo

## Example

```markdown
};

  }, [productId, referrer]);

  return <Form onSubmit={handleSubmit} />;

}

This looks clunky! Memoizing functions is common enough that React has a built-in Hook specifically for that. Wrap your functions into useCallback instead of useMemo to avoid having to write an extra nested function:

export default function Page({ productId, referrer }) {

  const handleSubmit = useCallback((orderDetails) => {

    post(&#x27;/product/&#x27; + productId + &#x27;/buy&#x27;, {

      referrer,
```
