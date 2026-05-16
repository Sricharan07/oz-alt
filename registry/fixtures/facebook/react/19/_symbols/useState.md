# useState

**Kind:** expected
**Signature:** `useState`
**Source:** https://react.dev/reference/react/useRef

## Example

```markdown
By using a ref, you ensure that:

You can store information between re-renders (unlike regular variables, which reset on every render).

Changing it does not trigger a re-render (unlike state variables, which trigger a re-render).

The information is local to each copy of your component (unlike the variables outside, which are shared).

Changing a ref does not trigger a re-render, so refs are not appropriate for storing information you want to display on the screen. Use state for that instead. Read more about choosing between useRef and useState.

Examples of referencing a value with useRef
1. Click counter 2. A stopwatch

Example 1 of 2:
Click counter
This component uses a ref to keep track of how many times the button was clicked. Note that it’s okay to use a ref instead of state here because the click count is only read and written in an event handler.
App.js
```
