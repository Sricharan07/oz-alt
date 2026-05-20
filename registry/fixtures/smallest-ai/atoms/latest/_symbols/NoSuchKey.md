# NoSuchKey

**Kind:** heading
**Signature:** `NoSuchKey`
**Source:** https://docs.smallest.ai/atoms/atoms-platform/troubleshooting/error-reference

## Example

```markdown
### 500 Internal Server Error

A server-side issue. Not caused by the request payload in most cases.

**Fix.** Retry once after a short delay. If it persists, file a support ticket and include the `x-request-id` value from the response headers so the server-side trace can be located.

## Storage and file errors

### `NoSuchKey` (from pre-recorded uploads)

The audio object referenced in the request does not exist in storage.

**Common causes.**

* Upload has not finished. The object key becomes available only after the PUT completes; polling immediately after starting an upload can return `NoSuchKey`.
* The key in the request does not match the uploaded object exactly. Keys are case-sensitive.
* The file was deleted or never uploaded.
```
