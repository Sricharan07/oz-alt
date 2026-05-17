use super::*;

pub(crate) fn config(command: ConfigCommand) -> Result<()> {
    let mut config = read_config()?;
    match command {
        ConfigCommand::List => {
            println!("{}", serde_json::to_string_pretty(&config)?);
        }
        ConfigCommand::Get { key } => {
            let value = get_config_value(&config, &key)
                .with_context(|| format!("unknown config key `{key}`"))?;
            println!("{value}");
        }
        ConfigCommand::Set { key, value } => {
            set_config_value(&mut config, &key, &value)?;
            write_config(&config)?;
        }
        ConfigCommand::Unset { key } => {
            unset_config_value(&mut config, &key)?;
            write_config(&config)?;
        }
    }
    Ok(())
}

fn config_path() -> Result<PathBuf> {
    Ok(dirs::home_dir()
        .context("failed to locate home directory")?
        .join(".codo")
        .join("config.json"))
}

pub(crate) fn read_config() -> Result<OzConfig> {
    let path = config_path()?;
    if !path.exists() {
        return Ok(OzConfig::default());
    }
    let content =
        fs::read_to_string(&path).with_context(|| format!("failed to read {}", path.display()))?;
    serde_json::from_str(&content).with_context(|| format!("failed to parse {}", path.display()))
}

pub(crate) fn write_config(config: &OzConfig) -> Result<()> {
    let path = config_path()?;
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)
            .with_context(|| format!("failed to create {}", parent.display()))?;
    }
    fs::write(
        &path,
        format!("{}\n", serde_json::to_string_pretty(config)?),
    )
    .with_context(|| format!("failed to write {}", path.display()))
}

pub(crate) fn auth_token(config: &OzConfig) -> Option<String> {
    if keychain_disabled() {
        return config.auth_token.clone();
    }
    read_keychain_token()
        .ok()
        .flatten()
        .or_else(|| config.auth_token.clone())
}

pub(crate) fn store_auth_token(config: &mut OzConfig, token: &str) {
    if keychain_disabled() {
        config.auth_token = Some(token.to_string());
        return;
    }
    if write_keychain_token(token).is_ok() {
        config.auth_token = None;
    } else {
        config.auth_token = Some(token.to_string());
    }
}

pub(crate) fn refresh_token(config: &OzConfig) -> Option<String> {
    if keychain_disabled() {
        return config.refresh_token.clone();
    }
    read_keychain_refresh_token()
        .ok()
        .flatten()
        .or_else(|| config.refresh_token.clone())
}

pub(crate) fn store_refresh_token(config: &mut OzConfig, token: &str) {
    if keychain_disabled() {
        config.refresh_token = Some(token.to_string());
        return;
    }
    if write_keychain_refresh_token(token).is_ok() {
        config.refresh_token = None;
    } else {
        config.refresh_token = Some(token.to_string());
    }
}

fn keychain_disabled() -> bool {
    std::env::var("OZ_DISABLE_KEYCHAIN")
        .map(|value| matches!(value.as_str(), "1" | "true" | "yes" | "on"))
        .unwrap_or(false)
}

#[cfg(target_os = "macos")]
fn write_keychain_token(token: &str) -> Result<()> {
    write_macos_keychain_secret(KEYCHAIN_SERVICE, "Oz CLI token", token)
}

#[cfg(target_os = "macos")]
fn write_keychain_refresh_token(token: &str) -> Result<()> {
    write_macos_keychain_secret(KEYCHAIN_REFRESH_SERVICE, "Oz CLI refresh token", token)
}

#[cfg(target_os = "macos")]
fn write_macos_keychain_secret(service: &str, label: &str, token: &str) -> Result<()> {
    let status = ProcessCommand::new("security")
        .args([
            "add-generic-password",
            "-a",
            KEYCHAIN_ACCOUNT,
            "-s",
            service,
            "-l",
            label,
            "-w",
            token,
            "-U",
        ])
        .status()
        .context("failed to invoke macOS security command")?;
    if !status.success() {
        bail!("macOS keychain rejected the credential");
    }
    Ok(())
}

#[cfg(target_os = "macos")]
fn read_keychain_token() -> Result<Option<String>> {
    read_macos_keychain_secret(KEYCHAIN_SERVICE)
}

#[cfg(target_os = "macos")]
fn read_keychain_refresh_token() -> Result<Option<String>> {
    read_macos_keychain_secret(KEYCHAIN_REFRESH_SERVICE)
}

#[cfg(target_os = "macos")]
fn read_macos_keychain_secret(service: &str) -> Result<Option<String>> {
    let output = ProcessCommand::new("security")
        .args([
            "find-generic-password",
            "-a",
            KEYCHAIN_ACCOUNT,
            "-s",
            service,
            "-w",
        ])
        .output()
        .context("failed to invoke macOS security command")?;
    if !output.status.success() {
        return Ok(None);
    }
    let token = String::from_utf8_lossy(&output.stdout).trim().to_string();
    Ok((!token.is_empty()).then_some(token))
}

#[cfg(target_os = "macos")]
fn delete_keychain_token() -> Result<()> {
    delete_macos_keychain_secret(KEYCHAIN_SERVICE)
}

#[cfg(target_os = "macos")]
fn delete_keychain_refresh_token() -> Result<()> {
    delete_macos_keychain_secret(KEYCHAIN_REFRESH_SERVICE)
}

#[cfg(target_os = "macos")]
fn delete_macos_keychain_secret(service: &str) -> Result<()> {
    let _ = ProcessCommand::new("security")
        .args([
            "delete-generic-password",
            "-a",
            KEYCHAIN_ACCOUNT,
            "-s",
            service,
        ])
        .status();
    Ok(())
}

#[cfg(target_os = "linux")]
fn write_keychain_token(token: &str) -> Result<()> {
    write_linux_keychain_secret(KEYCHAIN_SERVICE, "Oz CLI token", token)
}

#[cfg(target_os = "linux")]
fn write_keychain_refresh_token(token: &str) -> Result<()> {
    write_linux_keychain_secret(KEYCHAIN_REFRESH_SERVICE, "Oz CLI refresh token", token)
}

#[cfg(target_os = "linux")]
fn write_linux_keychain_secret(service: &str, label: &str, token: &str) -> Result<()> {
    let mut child = ProcessCommand::new("secret-tool")
        .args([
            "store",
            &format!("--label={label}"),
            "service",
            service,
            "account",
            KEYCHAIN_ACCOUNT,
        ])
        .stdin(std::process::Stdio::piped())
        .spawn()
        .context("failed to invoke secret-tool")?;
    child
        .stdin
        .as_mut()
        .context("failed to open secret-tool stdin")?
        .write_all(token.as_bytes())
        .context("failed to write token to secret-tool")?;
    let status = child.wait().context("failed waiting for secret-tool")?;
    if !status.success() {
        bail!("secret-tool rejected the credential");
    }
    Ok(())
}

#[cfg(target_os = "linux")]
fn read_keychain_token() -> Result<Option<String>> {
    read_linux_keychain_secret(KEYCHAIN_SERVICE)
}

#[cfg(target_os = "linux")]
fn read_keychain_refresh_token() -> Result<Option<String>> {
    read_linux_keychain_secret(KEYCHAIN_REFRESH_SERVICE)
}

#[cfg(target_os = "linux")]
fn read_linux_keychain_secret(service: &str) -> Result<Option<String>> {
    let output = ProcessCommand::new("secret-tool")
        .args([
            "lookup",
            "service",
            service,
            "account",
            KEYCHAIN_ACCOUNT,
        ])
        .output()
        .context("failed to invoke secret-tool")?;
    if !output.status.success() {
        return Ok(None);
    }
    let token = String::from_utf8_lossy(&output.stdout).trim().to_string();
    Ok((!token.is_empty()).then_some(token))
}

#[cfg(target_os = "linux")]
fn delete_keychain_token() -> Result<()> {
    delete_linux_keychain_secret(KEYCHAIN_SERVICE)
}

#[cfg(target_os = "linux")]
fn delete_keychain_refresh_token() -> Result<()> {
    delete_linux_keychain_secret(KEYCHAIN_REFRESH_SERVICE)
}

#[cfg(target_os = "linux")]
fn delete_linux_keychain_secret(service: &str) -> Result<()> {
    let _ = ProcessCommand::new("secret-tool")
        .args([
            "clear",
            "service",
            service,
            "account",
            KEYCHAIN_ACCOUNT,
        ])
        .status();
    Ok(())
}

#[cfg(target_os = "windows")]
fn write_keychain_token(token: &str) -> Result<()> {
    write_windows_keychain_secret(KEYCHAIN_SERVICE, token)
}

#[cfg(target_os = "windows")]
fn write_keychain_refresh_token(token: &str) -> Result<()> {
    write_windows_keychain_secret(KEYCHAIN_REFRESH_SERVICE, token)
}

#[cfg(target_os = "windows")]
fn write_windows_keychain_secret(service: &str, token: &str) -> Result<()> {
    let status = ProcessCommand::new("cmdkey")
        .args([
            &format!("/generic:{service}"),
            &format!("/user:{KEYCHAIN_ACCOUNT}"),
            &format!("/pass:{token}"),
        ])
        .status()
        .context("failed to invoke Windows Credential Manager")?;
    if !status.success() {
        bail!("Windows Credential Manager rejected the credential");
    }
    Ok(())
}

#[cfg(target_os = "windows")]
fn read_keychain_token() -> Result<Option<String>> {
    Ok(None)
}

#[cfg(target_os = "windows")]
fn read_keychain_refresh_token() -> Result<Option<String>> {
    Ok(None)
}

#[cfg(target_os = "windows")]
fn delete_keychain_token() -> Result<()> {
    delete_windows_keychain_secret(KEYCHAIN_SERVICE)
}

#[cfg(target_os = "windows")]
fn delete_keychain_refresh_token() -> Result<()> {
    delete_windows_keychain_secret(KEYCHAIN_REFRESH_SERVICE)
}

#[cfg(target_os = "windows")]
fn delete_windows_keychain_secret(service: &str) -> Result<()> {
    let _ = ProcessCommand::new("cmdkey")
        .arg(&format!("/delete:{service}"))
        .status();
    Ok(())
}

#[cfg(not(any(target_os = "macos", target_os = "linux", target_os = "windows")))]
fn write_keychain_token(_token: &str) -> Result<()> {
    bail!("no OS keychain integration for this platform")
}

#[cfg(not(any(target_os = "macos", target_os = "linux", target_os = "windows")))]
fn write_keychain_refresh_token(_token: &str) -> Result<()> {
    bail!("no OS keychain integration for this platform")
}

#[cfg(not(any(target_os = "macos", target_os = "linux", target_os = "windows")))]
fn read_keychain_token() -> Result<Option<String>> {
    Ok(None)
}

#[cfg(not(any(target_os = "macos", target_os = "linux", target_os = "windows")))]
fn read_keychain_refresh_token() -> Result<Option<String>> {
    Ok(None)
}

#[cfg(not(any(target_os = "macos", target_os = "linux", target_os = "windows")))]
fn delete_keychain_token() -> Result<()> {
    Ok(())
}

#[cfg(not(any(target_os = "macos", target_os = "linux", target_os = "windows")))]
fn delete_keychain_refresh_token() -> Result<()> {
    Ok(())
}

fn get_config_value(config: &OzConfig, key: &str) -> Option<String> {
    match key {
        "telemetry" => config.telemetry.map(|value| value.to_string()),
        "api_url" => config.api_url.clone(),
        "auth_token" => auth_token(config),
        "refresh_token" => refresh_token(config),
        "auto_update_skill" => config.auto_update_skill.map(|value| value.to_string()),
        _ => None,
    }
}

fn set_config_value(config: &mut OzConfig, key: &str, value: &str) -> Result<()> {
    match key {
        "telemetry" => config.telemetry = Some(parse_bool(value)?),
        "api_url" => config.api_url = Some(value.trim_end_matches('/').to_string()),
        "auth_token" => store_auth_token(config, value),
        "refresh_token" => store_refresh_token(config, value),
        "auto_update_skill" => config.auto_update_skill = Some(parse_bool(value)?),
        _ => bail!("unknown config key `{key}`"),
    }
    Ok(())
}

fn unset_config_value(config: &mut OzConfig, key: &str) -> Result<()> {
    match key {
        "telemetry" => config.telemetry = None,
        "api_url" => config.api_url = None,
        "auth_token" => {
            delete_keychain_token().ok();
            config.auth_token = None;
        }
        "refresh_token" => {
            delete_keychain_refresh_token().ok();
            config.refresh_token = None;
        }
        "auto_update_skill" => config.auto_update_skill = None,
        _ => bail!("unknown config key `{key}`"),
    }
    Ok(())
}

fn parse_bool(value: &str) -> Result<bool> {
    match value {
        "true" | "on" | "1" | "yes" => Ok(true),
        "false" | "off" | "0" | "no" => Ok(false),
        _ => bail!("expected boolean value, got `{value}`"),
    }
}
