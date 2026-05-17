from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


def deliver_alert(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    url = os.environ.get("OZ_ALERT_WEBHOOK_URL", "").strip()
    if not url:
        return None, None
    body = json.dumps(payload, sort_keys=True).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "oz-ops-alerts/1"},
        method="POST",
    )
    extra_header = os.environ.get("OZ_ALERT_WEBHOOK_HEADER", "").strip()
    if extra_header and ":" in extra_header:
        key, value = extra_header.split(":", 1)
        request.add_header(key.strip(), value.strip())
    try:
        with urlopen(request, timeout=10) as response:
            status = int(response.status)
    except URLError as exc:
        return "failed", str(exc)
    except Exception as exc:
        return "failed", str(exc)
    if 200 <= status < 300:
        return "delivered", None
    return "failed", f"webhook returned HTTP {status}"
