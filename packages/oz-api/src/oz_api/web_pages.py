from __future__ import annotations

from pathlib import Path
from typing import Any

from oz_api.auth import AuthPrincipal, PASSWORD_MIN_LENGTH, public_base_url
from oz_api.html_utils import esc


def render_home_page() -> str:
    api_url = public_base_url()
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Oz</title>
  <style>
    body {{ margin: 0; background: #f7f7f4; color: #202124; font-family: ui-sans-serif, system-ui, sans-serif; }}
    main {{ width: min(760px, calc(100vw - 32px)); margin: 56px auto; }}
    h1 {{ margin: 0 0 12px; font-size: 28px; line-height: 1.15; }}
    p {{ color: #51565c; font-size: 15px; line-height: 1.55; }}
    nav {{ display: flex; flex-wrap: wrap; gap: 10px; margin: 22px 0 28px; }}
    a.button {{ border: 1px solid #202124; border-radius: 6px; color: #202124; padding: 9px 12px; text-decoration: none; }}
    a.primary {{ background: #202124; color: #fff; }}
    section {{ border-top: 1px solid #d8dee4; padding: 20px 0; }}
    code {{ background: #fff; border: 1px solid #d8dee4; border-radius: 6px; padding: 2px 5px; }}
    pre {{ overflow-x: auto; background: #fff; border: 1px solid #d8dee4; border-radius: 8px; padding: 14px; }}
  </style>
</head>
<body>
  <main>
    <h1>Oz</h1>
    <p>Version-pinned documentation packs for coding agents. Pull docs into <code>.codo/vendors</code>, then use normal local search and read tools.</p>
    <nav>
      <a class="button primary" href="/signup">Create account</a>
      <a class="button" href="/libraries">Libraries</a>
      <a class="button" href="/login">Sign in</a>
      <a class="button" href="/status">Status</a>
    </nav>
    <section>
      <p>Install with npm or the shell installer.</p>
      <pre>npm install -g @hiringbae/oz
oz login --api-url {esc(api_url)}</pre>
    </section>
    <section>
      <p>CLI/API backend: <code>{esc(api_url)}</code></p>
    </section>
  </main>
</body>
</html>"""


def render_libraries_page(rows: list[dict[str, Any]]) -> str:
    items = "\n".join(
        f"""
        <tr>
          <td><a href="/libraries/{esc(row.get('vendor'))}/{esc(row.get('library'))}">{esc(row.get('vendor'))}/{esc(row.get('library'))}</a></td>
          <td>{esc(row.get('version'))}</td>
          <td>{esc(compact_count(row.get('chunk_count')))}</td>
          <td>{esc(compact_count(row.get('token_count')))}</td>
          <td>{esc(row.get('last_crawled_at') or row.get('indexed_at') or '')}</td>
          <td>{esc(row.get('description') or '')}</td>
        </tr>
        """
        for row in rows
    )
    if not items:
        items = '<tr><td colspan="6">No libraries are indexed yet.</td></tr>'
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Oz Libraries</title>
  <style>{public_catalog_css()}</style>
</head>
<body>
  <main>
    <header>
      <p><a href="/">Oz</a></p>
      <h1>Libraries</h1>
      <p>Browse indexed documentation packs, freshness, corpus size, and pull commands.</p>
    </header>
    <table>
      <thead><tr><th>Library</th><th>Version</th><th>Chunks</th><th>Tokens</th><th>Updated</th><th>Description</th></tr></thead>
      <tbody>{items}</tbody>
    </table>
  </main>
</body>
</html>"""


def render_library_detail_page(detail: dict[str, Any]) -> str:
    label = f"{detail.get('vendor')}/{detail.get('library')}"
    version = str(detail.get("version") or "latest")
    sources = list_rows(
        detail.get("sources") or [],
        lambda row: f'<a href="{esc(row.get("source_url"))}">{esc(row.get("source_url"))}</a> <span>{esc(row.get("source_type") or "")}</span>',
    )
    versions = list_rows(
        detail.get("versions") or [],
        lambda row: f'{esc(row.get("version"))} <span>{esc(row.get("chunk_count") or "")} chunks</span>',
    )
    content_types = list_rows(
        detail.get("content_types") or [],
        lambda row: f'{esc(row.get("content_type"))} <span>{esc(compact_count(row.get("chunk_count")))} chunks · {esc(compact_count(row.get("token_count")))} tokens</span>',
    )
    top_files = list_rows(
        detail.get("top_files") or [],
        lambda row: f'<code>{esc(row.get("path"))}</code> <span>{esc(compact_count(row.get("chunk_count")))} chunks</span>',
    )
    quality = list_rows(
        detail.get("quality") or [],
        lambda row: f'{status_label(row.get("passed"))} <span>{esc(row.get("created_at"))}</span>',
    )
    evals = list_rows(
        detail.get("evals") or [],
        lambda row: f'{status_label(row.get("passed"))} {esc(row.get("eval_type"))} <span>{esc(row.get("created_at"))}</span>',
    )
    pack_url = f"/pack/{detail.get('vendor')}/{detail.get('library')}/{version}"
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>{esc(label)} - Oz</title>
  <style>{public_catalog_css()}</style>
</head>
<body>
  <main>
    <header>
      <p><a href="/libraries">Libraries</a></p>
      <h1>{esc(label)}</h1>
      <p>{esc(detail.get("description") or "")}</p>
    </header>
    <section class="command">
      <pre>oz pull {esc(label)}@{esc(version)}
oz search "how do I use this?" {esc(label)}</pre>
    </section>
    <section class="grid">
      {metric("Version", version)}
      {metric("Files", compact_count(detail.get("file_count")))}
      {metric("Chunks", compact_count(detail.get("chunk_count")))}
      {metric("Tokens", compact_count(detail.get("token_count")))}
      {metric("Benchmark", f'{float(detail.get("benchmark_score") or 0):.2f}')}
      {metric("Trust", f'{float(detail.get("trust_score") or 0):.2f}')}
    </section>
    <section>
      <h2>Pack</h2>
      <dl>
        <dt>Ref</dt><dd><code>{esc(detail.get("ref_sha") or "")}</code></dd>
        <dt>Key</dt><dd><code>{esc(detail.get("pack_key") or "")}</code></dd>
        <dt>Size</dt><dd>{esc(compact_count(detail.get("pack_bytes")))} bytes</dd>
        <dt>Download</dt><dd><a href="{esc(pack_url)}">{esc(pack_url)}</a></dd>
        <dt>Last crawled</dt><dd>{esc(detail.get("last_crawled_at") or "")}</dd>
      </dl>
    </section>
    <section class="columns">
      <div><h2>Versions</h2>{versions}</div>
      <div><h2>Sources</h2>{sources}</div>
    </section>
    <section class="columns">
      <div><h2>Content Types</h2>{content_types}</div>
      <div><h2>Quality</h2>{quality}<h2>Evals</h2>{evals}</div>
    </section>
    <section>
      <h2>Top Files</h2>
      {top_files}
    </section>
  </main>
</body>
</html>"""


def public_catalog_css() -> str:
    return """
    body { margin: 0; background: #f7f7f4; color: #202124; font-family: ui-sans-serif, system-ui, sans-serif; }
    main { width: min(1120px, calc(100vw - 32px)); margin: 34px auto 64px; }
    a { color: #202124; }
    header { margin-bottom: 24px; }
    h1 { margin: 0 0 8px; font-size: 28px; line-height: 1.15; }
    h2 { margin: 22px 0 10px; font-size: 16px; }
    p, span, dd, dt { color: #51565c; font-size: 14px; line-height: 1.5; }
    table { border-collapse: collapse; width: 100%; background: #fff; border: 1px solid #d8dee4; }
    th, td { border-bottom: 1px solid #e6e8eb; padding: 10px; text-align: left; font-size: 14px; vertical-align: top; }
    th { color: #51565c; font-weight: 600; background: #fafafa; }
    code, pre { background: #fff; border: 1px solid #d8dee4; border-radius: 6px; }
    code { padding: 2px 5px; }
    pre { overflow-x: auto; padding: 14px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; }
    .metric, .command { background: #fff; border: 1px solid #d8dee4; border-radius: 8px; padding: 14px; }
    .metric strong { display: block; font-size: 20px; margin-top: 4px; }
    .columns { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 24px; }
    ul { padding-left: 18px; }
    li { margin: 7px 0; font-size: 14px; }
    dl { display: grid; grid-template-columns: 120px 1fr; gap: 8px 14px; }
    """


def metric(label: str, value: str) -> str:
    return f'<div class="metric"><span>{esc(label)}</span><strong>{esc(value)}</strong></div>'


def list_rows(rows: list[dict[str, Any]], render) -> str:
    if not rows:
        return "<p>Not recorded yet.</p>"
    return "<ul>" + "".join(f"<li>{render(row)}</li>" for row in rows) + "</ul>"


def status_label(value: Any) -> str:
    return "passed" if bool(value) else "failed"


def compact_count(value: Any) -> str:
    try:
        number = int(value or 0)
    except (TypeError, ValueError):
        return "0"
    if number >= 1_000_000:
        return f"{number / 1_000_000:.1f}M"
    if number >= 1_000:
        return f"{number / 1_000:.1f}k"
    return str(number)


def render_login_page(error: str = "") -> str:
    error_html = f'<p class="error">{esc(error)}</p>' if error else ""
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Oz Login</title>
  <style>
    body {{ margin: 0; min-height: 100vh; display: grid; place-items: center; background: #f7f7f4; color: #202124; font-family: ui-sans-serif, system-ui, sans-serif; }}
    main {{ width: min(420px, calc(100vw - 32px)); border: 1px solid #d8dee4; background: #fff; border-radius: 8px; padding: 24px; box-shadow: 0 16px 40px rgba(0,0,0,.08); }}
    h1 {{ margin: 0 0 16px; font-size: 22px; }}
    p {{ color: #51565c; font-size: 14px; line-height: 1.5; }}
    .error {{ color: #b42318; }}
    label {{ display: block; margin: 0 0 8px; font-size: 13px; color: #51565c; }}
    input {{ box-sizing: border-box; width: 100%; border: 1px solid #c7cbd1; border-radius: 6px; padding: 10px 12px; font: inherit; }}
    button {{ margin-top: 14px; width: 100%; border: 0; border-radius: 6px; background: #202124; color: #fff; padding: 10px 12px; font: inherit; cursor: pointer; }}
  </style>
</head>
<body>
  <main>
    <h1>Oz</h1>
    <p>Sign in to Oz.</p>
    {error_html}
    <form method="post" action="/login">
      <label for="email">Email</label>
      <input id="email" name="email" type="email" autocomplete="email" required>
      <label for="password">Password</label>
      <input id="password" name="password" type="password" autocomplete="current-password" required>
      <button type="submit">Sign in</button>
    </form>
    <p><a href="/signup">Create an account</a></p>
  </main>
</body>
</html>"""


def render_signup_page(error: str = "") -> str:
    error_html = f'<p class="error">{esc(error)}</p>' if error else ""
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Create Oz Account</title>
  <style>
    body {{ margin: 0; min-height: 100vh; display: grid; place-items: center; background: #f7f7f4; color: #202124; font-family: ui-sans-serif, system-ui, sans-serif; }}
    main {{ width: min(420px, calc(100vw - 32px)); border: 1px solid #d8dee4; background: #fff; border-radius: 8px; padding: 24px; box-shadow: 0 16px 40px rgba(0,0,0,.08); }}
    h1 {{ margin: 0 0 16px; font-size: 22px; }}
    p {{ color: #51565c; font-size: 14px; line-height: 1.5; }}
    .error {{ color: #b42318; }}
    label {{ display: block; margin: 0 0 8px; font-size: 13px; color: #51565c; }}
    input {{ box-sizing: border-box; width: 100%; border: 1px solid #c7cbd1; border-radius: 6px; padding: 10px 12px; font: inherit; margin-bottom: 12px; }}
    button {{ width: 100%; border: 0; border-radius: 6px; background: #202124; color: #fff; padding: 10px 12px; font: inherit; cursor: pointer; }}
  </style>
</head>
<body>
  <main>
    <h1>Create account</h1>
    <p>Use at least {PASSWORD_MIN_LENGTH} characters.</p>
    {error_html}
    <form method="post" action="/signup">
      <label for="email">Email</label>
      <input id="email" name="email" type="email" autocomplete="email" required>
      <label for="password">Password</label>
      <input id="password" name="password" type="password" autocomplete="new-password" minlength="{PASSWORD_MIN_LENGTH}" required>
      <label for="confirm_password">Confirm password</label>
      <input id="confirm_password" name="confirm_password" type="password" autocomplete="new-password" minlength="{PASSWORD_MIN_LENGTH}" required>
      <button type="submit">Create account</button>
    </form>
    <p><a href="/login">Sign in instead</a></p>
  </main>
</body>
</html>"""


def render_password_token_page(token: str, *, error: str = "", reset: bool = False) -> str:
    title = "Reset Password" if reset else "Set Password"
    error_html = f'<p class="error">{esc(error)}</p>' if error else ""
    action = "/reset-password" if reset else "/invite"
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    body {{ margin: 0; min-height: 100vh; display: grid; place-items: center; background: #f7f7f4; color: #202124; font-family: ui-sans-serif, system-ui, sans-serif; }}
    main {{ width: min(420px, calc(100vw - 32px)); border: 1px solid #d8dee4; background: #fff; border-radius: 8px; padding: 24px; box-shadow: 0 10px 28px rgba(0,0,0,.08); }}
    h1 {{ margin: 0 0 16px; font-size: 22px; }}
    p {{ color: #51565c; font-size: 14px; line-height: 1.5; }}
    .error {{ color: #b42318; }}
    label {{ display: block; margin: 0 0 8px; font-size: 13px; color: #51565c; }}
    input {{ box-sizing: border-box; width: 100%; border: 1px solid #c7cbd1; border-radius: 6px; padding: 10px 12px; font: inherit; margin-bottom: 12px; }}
    button {{ width: 100%; border: 0; border-radius: 6px; background: #202124; color: #fff; padding: 10px 12px; font: inherit; cursor: pointer; }}
  </style>
</head>
<body>
  <main>
    <h1>{title}</h1>
    <p>Use at least {PASSWORD_MIN_LENGTH} characters.</p>
    {error_html}
    <form method="post" action="{action}">
      <input type="hidden" name="token" value="{esc(token)}">
      <label for="password">Password</label>
      <input id="password" name="password" type="password" autocomplete="new-password" minlength="{PASSWORD_MIN_LENGTH}" required>
      <label for="confirm_password">Confirm password</label>
      <input id="confirm_password" name="confirm_password" type="password" autocomplete="new-password" minlength="{PASSWORD_MIN_LENGTH}" required>
      <button type="submit">Save password</button>
    </form>
  </main>
</body>
</html>"""


def render_dashboard(principal: AuthPrincipal, usage_rows: list[dict[str, Any]] | None = None) -> str:
    admin_link = '<p><a href="/admin">Open admin</a></p>' if principal.is_admin else ""
    api_url = public_base_url()
    rows = "\n".join(
        f"<tr><td>{esc(row.get('event'))}</td><td>{esc(row.get('library'))}</td><td>{esc(row.get('count'))}</td></tr>"
        for row in usage_rows or []
    )
    usage_html = (
        "<p>No usage recorded yet.</p>"
        if not rows
        else f"<table><thead><tr><th>Event</th><th>Library</th><th>Count</th></tr></thead><tbody>{rows}</tbody></table>"
    )
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Oz Dashboard</title>
  <style>
    body {{ margin: 32px; color: #202124; font-family: ui-sans-serif, system-ui, sans-serif; }}
    main {{ max-width: 880px; }}
    h1 {{ font-size: 24px; }}
    section {{ border-top: 1px solid #d8dee4; padding-top: 18px; margin-top: 22px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border-bottom: 1px solid #d8dee4; padding: 8px; text-align: left; font-size: 14px; }}
    code {{ background: #f6f8fa; border: 1px solid #d8dee4; border-radius: 4px; padding: 2px 5px; }}
  </style>
</head>
<body>
  <main>
    <h1>Oz Dashboard</h1>
    <p>{esc(principal.email)} · {esc(principal.role)}</p>
    {admin_link}
    <p><a href="/account">Account settings</a> · <a href="/device">Approve CLI device</a></p>
    <section>
      <h2>CLI Setup</h2>
      <p>Install Oz, then run <code>oz login --api-url {esc(api_url)}</code>.</p>
    </section>
    <section>
      <h2>Usage</h2>
      <p>Usage tracking is tied to this account and does not store source code or raw query text.</p>
      {usage_html}
    </section>
  </main>
</body>
</html>"""


def render_account_page(
    principal: AuthPrincipal,
    *,
    csrf: str = "",
    error: str = "",
    message: str = "",
    cli_sessions: list[dict[str, Any]] | None = None,
) -> str:
    error_html = f'<p class="error">{esc(error)}</p>' if error else ""
    message_html = f'<p class="ok">{esc(message)}</p>' if message else ""
    session_rows = "\n".join(render_cli_session_row(row, csrf) for row in cli_sessions or [])
    empty_sessions = "<p>No CLI sessions yet.</p>" if not session_rows else ""
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Oz Account</title>
  <style>
    body {{ margin: 32px; color: #202124; font-family: ui-sans-serif, system-ui, sans-serif; }}
    main {{ max-width: 640px; }}
    p {{ color: #51565c; line-height: 1.5; }}
    label {{ display: block; margin: 0 0 8px; font-size: 13px; color: #51565c; }}
    input {{ box-sizing: border-box; width: 100%; border: 1px solid #c7cbd1; border-radius: 6px; padding: 10px 12px; font: inherit; margin-bottom: 12px; }}
    button {{ border: 0; border-radius: 6px; background: #202124; color: #fff; padding: 10px 14px; font: inherit; cursor: pointer; }}
    button.secondary {{ border: 1px solid #c7cbd1; background: #fff; color: #202124; padding: 6px 10px; }}
    section {{ border-top: 1px solid #d8dee4; padding-top: 18px; margin-top: 22px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border-bottom: 1px solid #d8dee4; padding: 8px; text-align: left; font-size: 14px; vertical-align: top; }}
    .ok {{ color: #116329; }}
    .error {{ color: #b42318; }}
  </style>
</head>
<body>
  <main>
    <h1>Account</h1>
    <p>{esc(principal.email)} · {esc(principal.role)}</p>
    {message_html}
    {error_html}
    <section>
      <h2>Change password</h2>
      <form method="post" action="/account/password">
        <input type="hidden" name="csrf" value="{esc(csrf)}">
        <label for="current_password">Current password</label>
        <input id="current_password" name="current_password" type="password" autocomplete="current-password" required>
        <label for="new_password">New password</label>
        <input id="new_password" name="new_password" type="password" autocomplete="new-password" minlength="{PASSWORD_MIN_LENGTH}" required>
        <label for="confirm_password">Confirm new password</label>
        <input id="confirm_password" name="confirm_password" type="password" autocomplete="new-password" minlength="{PASSWORD_MIN_LENGTH}" required>
        <button type="submit">Update password</button>
      </form>
    </section>
    <section>
      <h2>CLI sessions</h2>
      {empty_sessions}
      <table><thead><tr><th>Machine</th><th>Created</th><th>Last used</th><th>Expires</th><th>Revoked</th><th></th></tr></thead><tbody>{session_rows}</tbody></table>
    </section>
    <p><a href="/dashboard">Back to dashboard</a></p>
  </main>
</body>
</html>"""


def render_cli_session_row(row: dict[str, Any], csrf: str) -> str:
    revoked = str(row.get("revoked_at") or "")
    action = ""
    if not revoked:
        action = (
            '<form method="post" action="/account/cli-sessions/revoke">'
            f'<input type="hidden" name="csrf" value="{esc(csrf)}">'
            f'<input type="hidden" name="token_id" value="{esc(row.get("id"))}">'
            '<button class="secondary" type="submit">Revoke</button>'
            "</form>"
        )
    return (
        f"<tr><td>{esc(row.get('machine_id'))}</td><td>{esc(row.get('created_at'))}</td>"
        f"<td>{esc(row.get('last_used_at'))}</td><td>{esc(row.get('expires_at'))}</td>"
        f"<td>{esc(revoked)}</td><td>{action}</td></tr>"
    )


def render_device_page(
    principal: AuthPrincipal,
    code: str = "",
    *,
    csrf: str = "",
    message: str = "",
    error: str = "",
) -> str:
    notice = f'<p class="ok">{esc(message)}</p>' if message else ""
    problem = f'<p class="error">{esc(error)}</p>' if error else ""
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Approve Oz CLI</title>
  <style>
    body {{ margin: 32px; color: #202124; font-family: ui-sans-serif, system-ui, sans-serif; }}
    main {{ max-width: 520px; }}
    p {{ color: #51565c; line-height: 1.5; }}
    label {{ display: block; margin-bottom: 8px; font-size: 13px; color: #51565c; }}
    input {{ box-sizing: border-box; width: 100%; border: 1px solid #c7cbd1; border-radius: 6px; padding: 10px 12px; font: inherit; text-transform: uppercase; }}
    button {{ margin-top: 14px; border: 0; border-radius: 6px; background: #202124; color: #fff; padding: 10px 14px; font: inherit; cursor: pointer; }}
    .ok {{ color: #116329; }}
    .error {{ color: #b42318; }}
  </style>
</head>
<body>
  <main>
    <h1>Approve Oz CLI</h1>
    <p>Signed in as {esc(principal.email)}.</p>
    {notice}
    {problem}
    <form method="post" action="/device">
      <input type="hidden" name="csrf" value="{esc(csrf)}">
      <label for="user_code">Device code</label>
      <input id="user_code" name="user_code" value="{esc(code)}" required>
      <button type="submit">Approve device</button>
    </form>
  </main>
</body>
</html>"""


def status_page() -> str:
    return """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Oz Status</title>
  <style>
    body { margin: 32px; color: #202124; font-family: ui-sans-serif, system-ui, sans-serif; }
    main { max-width: 720px; }
    h1 { font-size: 24px; }
    section { border-top: 1px solid #d8dee4; padding-top: 16px; margin-top: 20px; }
    .ok { color: #116329; font-weight: 600; }
    code { background: #f6f8fa; border: 1px solid #d8dee4; border-radius: 4px; padding: 2px 5px; }
  </style>
</head>
<body>
  <main>
    <h1>Oz Status</h1>
    <p class="ok">Operational</p>
    <section>
      <h2>Public endpoints</h2>
      <p>API health: <code>https://api.tryoz.dev/health</code></p>
      <p>Catalog: <code>https://api.tryoz.dev/catalog</code></p>
      <p>Status JSON: <code>https://api.tryoz.dev/status.json</code></p>
    </section>
    <section>
      <h2>Incident policy</h2>
      <p>During an active incident, this page is updated with affected endpoints, start time, mitigation, and next update time.</p>
    </section>
  </main>
</body>
</html>"""


def admin_result_page(title: str, message: str, *, link: str = "") -> str:
    link_html = ""
    if link:
        link_html = (
            '<label for="result_link">Link</label>'
            f'<input id="result_link" value="{esc(link)}" readonly>'
        )
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>{esc(title)}</title>
  <style>
    body {{ margin: 32px; color: #202124; font-family: ui-sans-serif, system-ui, sans-serif; }}
    main {{ max-width: 720px; }}
    a {{ color: #0969da; }}
    label {{ display: block; margin: 18px 0 6px; color: #51565c; font-size: 13px; }}
    input {{ box-sizing: border-box; width: 100%; border: 1px solid #c7cbd1; border-radius: 6px; padding: 10px 12px; font: inherit; }}
  </style>
</head>
<body>
  <main>
    <h1>{esc(title)}</h1>
    <p>{esc(message)}</p>
    {link_html}
    <p><a href="/admin">Back to admin</a></p>
  </main>
</body>
</html>"""


def public_markdown_html(raw_path: str) -> str:
    filename = "PRIVACY.md" if raw_path == "/privacy" else "TERMS.md"
    path = Path("docs") / filename
    if not path.exists():
        return "<!doctype html><p>Not found</p>"
    return f"<!doctype html><pre>{esc(path.read_text(encoding='utf-8'))}</pre>"
