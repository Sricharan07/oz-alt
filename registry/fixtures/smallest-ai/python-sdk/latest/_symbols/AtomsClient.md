# AtomsClient

**Kind:** expected
**Signature:** `AtomsClient`
**Source:** https://raw.githubusercontent.com/smallest-inc/smallest-python-sdk/main/smallestai/atoms/audience.py#audience

## Example

```markdown
class Audience:
    """
    Manager for audience operations.

    Can be used standalone:
        audience = Audience()
        audience.create(...)

    Or via AtomsClient:
        client = AtomsClient()
        client.audience.create(...)
    """

    def __init__(
        self,
        base_url: str = None,
        api_key: str = None
```
