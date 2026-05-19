use super::*;
use std::io::{IsTerminal, Write};

pub(crate) fn login(api_url: Option<&str>) -> Result<()> {
    let mut config = read_config()?;
    if let Some(api_url) = api_url {
        config.api_url = Some(api_url.trim_end_matches('/').to_string());
    }
    if config.api_url.is_none() {
        config.api_url = Some(DEFAULT_API_URL.to_string());
    }

    let start: DeviceStartResponse = api_post_json_without_auth(
        config.api_url.as_deref().expect("api_url should be set"),
        "/auth/device",
        serde_json::json!({"client": "oz-cli"}),
    )?;
    let verification_uri = start
        .verification_uri_complete
        .as_deref()
        .unwrap_or(&start.verification_uri);
    println!(
        "Open {} and enter code {}",
        verification_uri, start.user_code
    );

    let token = poll_device_token(
        config.api_url.as_deref().expect("api_url should be set"),
        &start,
    )?;
    store_auth_token(&mut config, &token.access_token);
    if let Some(refresh_token) = token.refresh_token.as_deref() {
        store_refresh_token(&mut config, refresh_token);
    }
    if config.telemetry.is_none() {
        config.telemetry = Some(telemetry_preference()?);
    }
    write_config(&config)?;
    println!(
        "logged in to {}",
        config.api_url.as_deref().expect("api_url should be set")
    );
    println!(
        "telemetry is {}; it never sends query text",
        if config.telemetry.unwrap_or(true) {
            "on"
        } else {
            "off"
        }
    );
    Ok(())
}

pub(crate) fn setup(
    project_root: &Path,
    api_url: Option<&str>,
    skip_login: bool,
    skip_install: bool,
    agents: AgentInstallMode,
) -> Result<()> {
    let mut config = read_config()?;
    let mut changed_config = false;
    if let Some(api_url) = api_url {
        config.api_url = Some(api_url.trim_end_matches('/').to_string());
        changed_config = true;
    }
    if config.api_url.is_none() {
        config.api_url = Some(DEFAULT_API_URL.to_string());
        changed_config = true;
    }
    if changed_config {
        write_config(&config)?;
    }

    if !skip_login && auth_token(&config).is_none() && refresh_token(&config).is_none() {
        login(None)?;
    }

    init_project(project_root)?;

    if !skip_install && agents != AgentInstallMode::None {
        install_skill(project_root, InstallTargets::for_mode(agents, project_root))?;
    }

    doctor_impl(project_root, !skip_login)
}

fn telemetry_preference() -> Result<bool> {
    if let Ok(value) = std::env::var("OZ_TELEMETRY") {
        return parse_telemetry_preference(&value);
    }
    if !std::io::stdin().is_terminal() {
        return Ok(true);
    }
    print!("Enable anonymous telemetry? It never sends query text. [Y/n] ");
    std::io::stdout().flush()?;
    let mut answer = String::new();
    std::io::stdin().read_line(&mut answer)?;
    let trimmed = answer.trim();
    if trimmed.is_empty() {
        return Ok(true);
    }
    parse_telemetry_preference(trimmed)
}

fn parse_telemetry_preference(value: &str) -> Result<bool> {
    match value.trim().to_ascii_lowercase().as_str() {
        "1" | "true" | "yes" | "y" | "on" => Ok(true),
        "0" | "false" | "no" | "n" | "off" => Ok(false),
        other => bail!("invalid telemetry preference `{other}`; use on or off"),
    }
}

fn poll_device_token(base_url: &str, start: &DeviceStartResponse) -> Result<TokenResponse> {
    let interval = Duration::from_secs(start.interval.unwrap_or(5).max(1));
    let timeout = Duration::from_secs(start.expires_in.unwrap_or(600).max(30));
    let deadline = Instant::now() + timeout;
    loop {
        match api_post_json_without_auth(
            base_url,
            "/auth/token",
            serde_json::json!({"device_code": start.device_code}),
        ) {
            Ok(token) => return Ok(token),
            Err(error) => {
                let message = error.to_string();
                if !message.contains("authorization_pending") && !message.contains("slow_down") {
                    return Err(error);
                }
                if Instant::now() + interval > deadline {
                    bail!("device authorization timed out");
                }
                std::thread::sleep(interval);
            }
        }
    }
}

pub(crate) fn pull_library(project_root: &Path, spec: &str) -> Result<()> {
    pull_library_impl(project_root, spec, false)
}

pub(crate) fn pull_library_impl(project_root: &Path, spec: &str, quiet: bool) -> Result<()> {
    ensure_project(project_root)?;

    let config = read_config()?;
    if configured_api_url(&config).is_some() {
        return pull_library_remote(project_root, &config, spec, quiet);
    }

    let mut parsed = parse_library_spec(spec)?;
    let source = resolve_registry_source(project_root, &mut parsed)?;
    let version = parsed
        .version
        .clone()
        .context("registry resolution should fill in a version")?;

    let objects_root = global_objects_root()?;
    let manifest = match &source {
        RegistrySource::Pack(pack_path) => ingest_pack(&objects_root, pack_path)?,
        RegistrySource::Fixture(source_root) => ingest_directory(
            &objects_root,
            source_root,
            &parsed.vendor,
            &parsed.library,
            &version,
        )?,
    };

    let target = project_root
        .join(VENDORS_DIR)
        .join(&parsed.vendor)
        .join(format!("{}@{}", parsed.library, version));
    materialize_tree(&objects_root, &target, &manifest)?;

    let telemetry_library = format!("{}/{}", parsed.vendor, parsed.library);
    let mut lock = read_lock(project_root)?;
    upsert_pull(
        &mut lock,
        PulledLibrary {
            vendor: parsed.vendor,
            library: parsed.library,
            version: version.clone(),
            path: to_project_path(project_root, &target),
            source: source.label(project_root),
            pulled_at: Utc::now().to_rfc3339(),
        },
    );
    write_lock(project_root, &lock)?;

    if !quiet {
        println!("{}", to_project_path(project_root, &target));
    }
    emit_telemetry(
        &config,
        "pull_completed",
        serde_json::json!({
            "library": telemetry_library,
            "version": version,
            "source": "local",
        }),
    );
    Ok(())
}

fn pull_library_remote(
    project_root: &Path,
    config: &OzConfig,
    spec: &str,
    quiet: bool,
) -> Result<()> {
    let mut parsed = parse_library_spec(spec)?;
    if parsed.version.is_none() {
        if let Some(version_hint) = lockfile_version_hint(project_root, &parsed) {
            parsed.version = Some(version_hint);
        }
    }
    let refs_route = if let Some(version) = parsed.version.as_deref() {
        format!(
            "/refs/{}/{}?version={}",
            parsed.vendor,
            parsed.library,
            url_component(version)
        )
    } else {
        format!("/refs/{}/{}", parsed.vendor, parsed.library)
    };
    let refs: RefResponse = api_get_json(config, &refs_route)?;
    parsed.version = Some(refs.version);
    let version = parsed
        .version
        .clone()
        .context("remote registry should resolve a version")?;
    let pack_route = format!("/pack/{}/{}/{}", parsed.vendor, parsed.library, version);
    let pack_bytes = api_get_bytes(config, &pack_route)?;
    let objects_root = global_objects_root()?;
    let manifest = ingest_pack_bytes(
        &objects_root,
        &pack_bytes,
        &format!(
            "{}/pack/{}/{}/{}",
            configured_api_url(config).expect("api_url should exist"),
            parsed.vendor,
            parsed.library,
            version
        ),
    )?;

    let target = project_root
        .join(VENDORS_DIR)
        .join(&parsed.vendor)
        .join(format!("{}@{}", parsed.library, version));
    materialize_tree(&objects_root, &target, &manifest)?;

    let mut lock = read_lock(project_root)?;
    upsert_pull(
        &mut lock,
        PulledLibrary {
            vendor: parsed.vendor.clone(),
            library: parsed.library.clone(),
            version: version.clone(),
            path: to_project_path(project_root, &target),
            source: format!(
                "api:{}/pack/{}/{}/{}",
                configured_api_url(config).expect("api_url should exist"),
                parsed.vendor,
                parsed.library,
                version
            ),
            pulled_at: Utc::now().to_rfc3339(),
        },
    );
    write_lock(project_root, &lock)?;

    if !quiet {
        println!("{}", to_project_path(project_root, &target));
    }
    emit_telemetry(
        config,
        "pull_completed",
        serde_json::json!({
            "library": format!("{}/{}", parsed.vendor, parsed.library),
            "version": version,
            "source": "api",
        }),
    );
    Ok(())
}

pub(crate) fn print_status(project_root: &Path) -> Result<()> {
    let lock = read_lock(project_root)?;
    let config = read_config().unwrap_or_default();
    if lock.pulls.is_empty() {
        println!("no libraries pulled");
        return Ok(());
    }

    for pull in lock.pulls {
        let freshness = latest_version_for(project_root, &config, &pull.vendor, &pull.library)?
            .map(|latest| {
                if latest != pull.version {
                    format!("stale latest={latest}")
                } else {
                    "fresh".to_string()
                }
            })
            .unwrap_or_else(|| "unknown".to_string());
        println!(
            "{}/{}@{}  {}  {}",
            pull.vendor, pull.library, pull.version, freshness, pull.path
        );
    }
    Ok(())
}

pub(crate) fn suggest_libraries(project_root: &Path, query: &str, json: bool) -> Result<()> {
    let config = read_config()?;
    if configured_api_url(&config).is_some() {
        return suggest_libraries_remote(project_root, &config, query, json);
    }

    let catalog = load_or_build_catalog(project_root)?;
    let terms = normalize_query(query);
    if terms.is_empty() {
        bail!("suggest query must contain at least one alphanumeric term");
    }

    let mut scored = catalog
        .libraries
        .into_iter()
        .filter_map(|library| {
            let haystack = format!(
                "{} {} {} {} {}",
                library.vendor,
                library.library,
                library.version,
                library.description,
                library.keywords.join(" ")
            )
            .to_ascii_lowercase();
            let score = terms
                .iter()
                .map(|term| haystack.matches(term.as_str()).count())
                .sum::<usize>();
            (score > 0).then_some((score, library))
        })
        .collect::<Vec<_>>();

    scored.sort_by(|a, b| {
        b.0.cmp(&a.0)
            .then_with(|| a.1.vendor.cmp(&b.1.vendor))
            .then_with(|| a.1.library.cmp(&b.1.library))
    });

    if scored.is_empty() {
        record_index_request(project_root, query, None)?;
        if json {
            println!(
                "{}",
                serde_json::to_string_pretty(&serde_json::json!({
                    "results": [],
                    "index_request_submitted": true,
                }))?
            );
        } else {
            println!("no indexed libraries matched; index request submitted");
        }
        return Ok(());
    }

    let results = scored
        .into_iter()
        .take(10)
        .map(|(score, library)| {
            let scope = format!("{}/{}", library.vendor, library.library);
            serde_json::json!({
                "vendor": library.vendor,
                "library": library.library,
                "version": library.version,
                "score": score,
                "reason": library.description,
                "pull_command": format!("oz pull {scope}"),
                "search_command": format!("oz search {:?} {scope}", query),
            })
        })
        .collect::<Vec<_>>();
    if json {
        println!(
            "{}",
            serde_json::to_string_pretty(&serde_json::json!({ "results": results }))?
        );
    } else {
        for result in &results {
            println!(
                "{}/{}@{}  score={}  {}",
                result["vendor"].as_str().unwrap_or_default(),
                result["library"].as_str().unwrap_or_default(),
                result["version"].as_str().unwrap_or_default(),
                result["score"].as_u64().unwrap_or_default(),
                result["reason"].as_str().unwrap_or_default()
            );
            println!(
                "  pull:   {}",
                result["pull_command"].as_str().unwrap_or_default()
            );
            println!(
                "  search: {}",
                result["search_command"].as_str().unwrap_or_default()
            );
        }
    }
    emit_telemetry(
        &config,
        "suggest_query",
        serde_json::json!({
            "query_length": query.len(),
            "result_count": results.len(),
        }),
    );
    Ok(())
}

fn suggest_libraries_remote(
    project_root: &Path,
    config: &OzConfig,
    query: &str,
    json: bool,
) -> Result<()> {
    ensure_project(project_root)?;
    let lock = read_lock(project_root)?;
    let response: SuggestResponse = api_post_json(
        config,
        "/suggest",
        serde_json::json!({
            "query": query,
            "project_fingerprint": lock.project_fingerprint,
            "installed_libraries": installed_libraries_payload(&lock),
            "max_results": 10,
        }),
    )?;

    if response.results.is_empty() {
        let _ = api_post_json::<serde_json::Value>(
            config,
            "/index-request",
            serde_json::json!({
                "library_name": null,
                "vendor_hint": null,
                "source_url_hint": null,
                "requesting_user": "oz-cli",
            }),
        );
        if json {
            println!(
                "{}",
                serde_json::to_string_pretty(&serde_json::json!({
                    "results": [],
                    "index_request_submitted": true,
                }))?
            );
        } else {
            println!("no indexed libraries matched; index request submitted");
        }
        return Ok(());
    }

    warn_stale_response(&response.stale_libraries);
    if json {
        println!(
            "{}",
            serde_json::to_string_pretty(&serde_json::json!({
                "results": suggest_results_with_commands(query, &response.results),
                "stale_libraries": response.stale_libraries,
            }))?
        );
    } else {
        for result in &response.results {
            let scope = format!("{}/{}", result.vendor, result.library);
            println!(
                "{}/{}@{}  score={}  {}",
                result.vendor, result.library, result.version, result.score, result.reason
            );
            println!("  pull:   oz pull {scope}");
            println!("  search: oz search {:?} {scope}", query);
        }
    }
    emit_telemetry(
        config,
        "suggest_query",
        serde_json::json!({
            "query_length": query.len(),
            "result_count": response.results.len(),
        }),
    );
    Ok(())
}

fn suggest_results_with_commands(query: &str, results: &[SuggestResult]) -> Vec<serde_json::Value> {
    results
        .iter()
        .map(|result| {
            let scope = format!("{}/{}", result.vendor, result.library);
            serde_json::json!({
                "vendor": result.vendor,
                "library": result.library,
                "version": result.version,
                "score": result.score,
                "reason": result.reason,
                "pull_command": format!("oz pull {scope}"),
                "search_command": format!("oz search {:?} {scope}", query),
            })
        })
        .collect()
}

pub(crate) fn update_libraries(project_root: &Path, scope: Option<&str>) -> Result<()> {
    let lock = read_lock(project_root)?;
    let config = read_config().unwrap_or_default();
    let parsed_scope = scope.map(parse_library_scope).transpose()?;
    let pulls = lock
        .pulls
        .iter()
        .filter(|pull| {
            parsed_scope
                .as_ref()
                .map(|scope| {
                    pull.vendor == scope.vendor
                        && pull.library == scope.library
                        && scope
                            .version
                            .as_ref()
                            .map(|requested| version_matches(&pull.version, requested))
                            .unwrap_or(true)
                })
                .unwrap_or(true)
        })
        .cloned()
        .collect::<Vec<_>>();

    if pulls.is_empty() {
        bail!("no pulled libraries matched update scope");
    }

    for pull in pulls {
        let version = latest_version_for(project_root, &config, &pull.vendor, &pull.library)?
            .unwrap_or_else(|| pull.version.clone());
        let spec = format!("{}/{}@{}", pull.vendor, pull.library, version);
        pull_library(project_root, &spec)?;
    }
    emit_telemetry(
        &config,
        "update_run",
        serde_json::json!({
            "scope": scope,
        }),
    );
    Ok(())
}

pub(crate) fn dev_command(project_root: &Path, command: DevCommand) -> Result<()> {
    match command {
        DevCommand::Registry { command } => registry_command(project_root, command),
    }
}

fn registry_command(project_root: &Path, command: RegistryCommand) -> Result<()> {
    match command {
        RegistryCommand::Catalog => {
            let catalog = build_catalog(project_root)?;
            write_catalog(project_root, &catalog)?;
            println!("indexed {} libraries", catalog.libraries.len());
        }
        RegistryCommand::BuildPacks => {
            build_packs(project_root)?;
            let catalog = build_catalog(project_root)?;
            write_catalog(project_root, &catalog)?;
            println!("built packs for {} libraries", catalog.libraries.len());
        }
    }
    Ok(())
}

pub(crate) fn doctor(project_root: &Path) -> Result<()> {
    doctor_impl(project_root, true)
}

fn doctor_impl(project_root: &Path, require_auth_token: bool) -> Result<()> {
    let mut failed = false;
    let config = read_config().unwrap_or_default();
    let api_configured = configured_api_url(&config).is_some();
    check(
        "project lock",
        project_root.join(LOCK_FILE).exists(),
        &mut failed,
    );
    check(
        "vendors directory",
        project_root.join(VENDORS_DIR).exists(),
        &mut failed,
    );
    check(
        "global object store",
        global_objects_root()?.exists(),
        &mut failed,
    );
    if api_configured {
        check(
            "network reachability",
            api_get_json::<serde_json::Value>(&config, "/health").is_ok(),
            &mut failed,
        );
        if require_auth_token {
            check("auth token", auth_token(&config).is_some(), &mut failed);
        } else {
            println!("skip auth token");
        }
        check(
            "registry catalog",
            remote_catalog_available(&config),
            &mut failed,
        );
    } else {
        check(
            "development registry",
            fixtures_root(project_root).is_some(),
            &mut failed,
        );
        check(
            "registry catalog",
            catalog_path(project_root).is_some(),
            &mut failed,
        );
    }

    if failed {
        bail!("doctor found problems");
    }
    println!("oz doctor: ok");
    Ok(())
}

fn remote_catalog_available(config: &OzConfig) -> bool {
    api_get_json::<serde_json::Value>(config, "/catalog")
        .ok()
        .and_then(|payload| {
            payload
                .get("libraries")
                .and_then(|value| value.as_array())
                .cloned()
        })
        .is_some_and(|libraries| !libraries.is_empty())
}

fn check(label: &str, ok: bool, failed: &mut bool) {
    if ok {
        println!("ok   {label}");
    } else {
        println!("fail {label}");
        *failed = true;
    }
}
