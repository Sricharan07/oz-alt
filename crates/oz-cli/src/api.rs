use super::*;

pub(crate) fn url_component(value: &str) -> String {
    let mut encoded = String::new();
    for byte in value.bytes() {
        match byte {
            b'A'..=b'Z' | b'a'..=b'z' | b'0'..=b'9' | b'-' | b'_' | b'.' | b'~' => {
                encoded.push(byte as char)
            }
            _ => encoded.push_str(&format!("%{byte:02X}")),
        }
    }
    encoded
}

pub(crate) fn emit_telemetry(config: &OzConfig, event: &str, properties: serde_json::Value) {
    if config.telemetry == Some(false) || configured_api_url(config).is_none() {
        return;
    }
    let _ = api_post_json::<serde_json::Value>(
        config,
        "/telemetry",
        serde_json::json!({
            "event": event,
            "properties": properties,
        }),
    );
}

pub(crate) fn configured_api_url(config: &OzConfig) -> Option<String> {
    config
        .api_url
        .as_ref()
        .map(|value| value.trim().trim_end_matches('/').to_string())
        .filter(|value| !value.is_empty())
}

pub(crate) fn api_get_json<T: DeserializeOwned>(config: &OzConfig, route: &str) -> Result<T> {
    let base_url = configured_api_url(config).context("api_url is not configured")?;
    let url = route_url(&base_url, route);
    let response = response_with_refresh(config, |runtime_config| {
        let mut request = ureq::get(&url);
        if let Some(token) = auth_token(runtime_config) {
            request = request.set("Authorization", &format!("Bearer {token}"));
        }
        request.call()
    })?;
    response
        .into_json::<T>()
        .with_context(|| format!("failed to decode JSON response from {url}"))
}

pub(crate) fn api_get_bytes(config: &OzConfig, route: &str) -> Result<Vec<u8>> {
    let base_url = configured_api_url(config).context("api_url is not configured")?;
    let url = route_url(&base_url, route);
    let response = response_with_refresh(config, |runtime_config| {
        let mut request = ureq::get(&url);
        if let Some(token) = auth_token(runtime_config) {
            request = request.set("Authorization", &format!("Bearer {token}"));
        }
        request.call()
    })?;
    let mut reader = response.into_reader();
    let mut bytes = Vec::new();
    reader
        .read_to_end(&mut bytes)
        .with_context(|| format!("failed reading response bytes from {url}"))?;
    Ok(bytes)
}

pub(crate) fn api_post_json<T: DeserializeOwned>(
    config: &OzConfig,
    route: &str,
    body: serde_json::Value,
) -> Result<T> {
    let base_url = configured_api_url(config).context("api_url is not configured")?;
    let url = route_url(&base_url, route);
    let response = response_with_refresh(config, |runtime_config| {
        let mut request = ureq::post(&url).set("Content-Type", "application/json");
        if let Some(token) = auth_token(runtime_config) {
            request = request.set("Authorization", &format!("Bearer {token}"));
        }
        request.send_json(body.clone())
    })?;
    response
        .into_json::<T>()
        .with_context(|| format!("failed to decode JSON response from {url}"))
}

pub(crate) fn api_post_json_without_auth<T: DeserializeOwned>(
    base_url: &str,
    route: &str,
    body: serde_json::Value,
) -> Result<T> {
    let url = route_url(base_url.trim_end_matches('/'), route);
    let response = ureq::post(&url)
        .set("Content-Type", "application/json")
        .send_json(body)
        .map_err(format_ureq_error)?;
    response
        .into_json::<T>()
        .with_context(|| format!("failed to decode JSON response from {url}"))
}

fn route_url(base_url: &str, route: &str) -> String {
    format!(
        "{}/{}",
        base_url.trim_end_matches('/'),
        route.trim_start_matches('/')
    )
}

fn response_with_refresh<F>(config: &OzConfig, mut request: F) -> Result<ureq::Response>
where
    F: FnMut(&OzConfig) -> std::result::Result<ureq::Response, ureq::Error>,
{
    let mut runtime_config = config.clone();
    match request(&runtime_config) {
        Ok(response) => Ok(response),
        Err(ureq::Error::Status(401, _)) => {
            if refresh_access_token(&mut runtime_config)? {
                request(&runtime_config).map_err(format_ureq_error)
            } else {
                bail!("registry API returned HTTP 401: run `oz login`")
            }
        }
        Err(error) => Err(format_ureq_error(error)),
    }
}

fn refresh_access_token(config: &mut OzConfig) -> Result<bool> {
    let Some(refresh) = refresh_token(config) else {
        return Ok(false);
    };
    let base_url = configured_api_url(config).context("api_url is not configured")?;
    let token: TokenResponse = api_post_json_without_auth(
        &base_url,
        "/auth/refresh",
        serde_json::json!({ "refresh_token": refresh }),
    )?;
    store_auth_token(config, &token.access_token);
    if let Some(refresh_token) = token.refresh_token.as_deref() {
        store_refresh_token(config, refresh_token);
    }
    write_config(config)?;
    Ok(true)
}

fn format_ureq_error(error: ureq::Error) -> anyhow::Error {
    match error {
        ureq::Error::Status(code, response) => {
            let body = response.into_string().unwrap_or_default();
            anyhow::anyhow!("registry API returned HTTP {code}: {body}")
        }
        ureq::Error::Transport(error) => anyhow::anyhow!("registry API transport error: {error}"),
    }
}
