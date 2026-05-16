use anyhow::{bail, Context, Result};
use chrono::Utc;
use clap::{Parser, Subcommand};
use oz_objects::{
    ingest_directory, ingest_pack, ingest_pack_bytes, materialize_tree, sha256_hex, write_pack,
};
use serde::de::DeserializeOwned;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;
use std::fs;
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::process::Command as ProcessCommand;
use walkdir::WalkDir;

const CODO_DIR: &str = ".codo";
const LOCK_FILE: &str = ".codo/lock.json";
const VENDORS_DIR: &str = ".codo/vendors";
const REGISTRY_DIR: &str = "registry";
const FIXTURES_DIR: &str = "registry/fixtures";
const PACKS_DIR: &str = "registry/packs";
const CATALOG_FILE: &str = "registry/catalog.json";
const SKILL_START: &str = "<!-- oz-skill:start -->";
const SKILL_END: &str = "<!-- oz-skill:end -->";
const KEYCHAIN_SERVICE: &str = "dev.oz.auth-token";
const KEYCHAIN_ACCOUNT: &str = "oz-cli";

#[derive(Debug, Parser)]
#[command(name = "oz")]
#[command(about = "Version-pinned local documentation for coding agents")]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Debug, Subcommand)]
enum Command {
    /// Log in to an Oz registry API and store a local token.
    Login {
        /// Registry API URL, for example http://127.0.0.1:8765.
        #[arg(long)]
        api_url: Option<String>,
    },

    /// Initialize Oz metadata in the current project.
    Init,

    /// Pull docs for a library from the local development registry.
    Pull {
        /// Library specs, for example vercel/next.js@15.
        libraries: Vec<String>,
    },

    /// Suggest indexed libraries for a task description.
    Suggest {
        /// One-line task or integration description.
        query: String,

        /// Print machine-readable JSON.
        #[arg(long)]
        json: bool,
    },

    /// Search already-pulled docs with a simple local keyword scorer.
    Search {
        /// Query text.
        query: String,

        /// Optional library scope, for example vercel/next.js.
        library: Option<String>,

        /// Print machine-readable JSON.
        #[arg(long)]
        json: bool,
    },

    /// Show pulled libraries for this project.
    Status,

    /// Re-pull one library or every pulled library.
    Update {
        /// Optional library scope, for example vercel/next.js.
        library: Option<String>,
    },

    /// Remove temporary files and report object-store state.
    Gc,

    /// Read or write local Oz configuration.
    Config {
        #[command(subcommand)]
        command: ConfigCommand,
    },

    /// Local registry maintenance commands.
    Registry {
        #[command(subcommand)]
        command: RegistryCommand,
    },

    /// Validate the local Oz project and object store.
    Doctor,

    /// Install the Oz agent instructions into AGENTS.md.
    Install {
        #[arg(long)]
        codex: bool,
        #[arg(long = "claude-code")]
        claude_code: bool,
        #[arg(long)]
        cursor: bool,
        #[arg(long)]
        cline: bool,
        #[arg(long)]
        continue_agent: bool,
    },
}

#[derive(Debug, Subcommand)]
enum ConfigCommand {
    List,
    Get { key: String },
    Set { key: String, value: String },
    Unset { key: String },
}

#[derive(Debug, Subcommand)]
enum RegistryCommand {
    /// Rebuild registry/catalog.json from fixture metadata.
    Catalog,

    /// Build .ozpack files for every local fixture and refresh the catalog.
    BuildPacks,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
struct ProjectLock {
    schema_version: u32,
    generated_at: String,
    project_fingerprint: String,
    dependencies: Vec<Dependency>,
    pulls: Vec<PulledLibrary>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
struct Dependency {
    ecosystem: String,
    name: String,
    requirement: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
struct PulledLibrary {
    vendor: String,
    library: String,
    version: String,
    path: String,
    source: String,
    pulled_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
struct OzConfig {
    telemetry: Option<bool>,
    api_url: Option<String>,
    auth_token: Option<String>,
    auto_update_skill: Option<bool>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
struct RegistryCatalog {
    schema_version: u32,
    generated_at: String,
    libraries: Vec<CatalogLibrary>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
struct CatalogLibrary {
    vendor: String,
    library: String,
    version: String,
    description: String,
    source_urls: Vec<String>,
    keywords: Vec<String>,
    fixture_path: String,
    pack_path: Option<String>,
    ref_sha: String,
    indexed_at: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
struct LibrarySpec {
    vendor: String,
    library: String,
    version: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
enum RegistrySource {
    Pack(PathBuf),
    Fixture(PathBuf),
}

impl RegistrySource {
    fn label(&self, project_root: &Path) -> String {
        match self {
            RegistrySource::Pack(path) => format!("pack:{}", to_project_path(project_root, path)),
            RegistrySource::Fixture(path) => {
                format!("fixture:{}", to_project_path(project_root, path))
            }
        }
    }
}

#[derive(Debug, Clone)]
struct SearchHit {
    path: PathBuf,
    line: usize,
    score: usize,
    preview: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct DeviceStartResponse {
    device_code: String,
    user_code: String,
    verification_uri: String,
    interval: Option<u64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct TokenResponse {
    access_token: String,
    token_type: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct SuggestResponse {
    results: Vec<SuggestResult>,
    stale_libraries: Vec<serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct SuggestResult {
    vendor: String,
    library: String,
    version: String,
    score: serde_json::Value,
    reason: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct SearchResponse {
    results: Vec<SearchResult>,
    libraries_to_pull: Vec<LibraryToPull>,
    stale_libraries: Vec<serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct SearchResult {
    path: String,
    line: Option<usize>,
    score: serde_json::Value,
    library: String,
    version: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct LibraryToPull {
    vendor: String,
    library: String,
    version: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct RefResponse {
    vendor: String,
    library: String,
    version: String,
    ref_sha: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct BulkRefsResponse {
    stale_libraries: Vec<StaleLibrary>,
    fingerprint: Option<String>,
    catalog_generated_at: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct StaleLibrary {
    vendor: String,
    library: String,
    version: String,
    newer_version: String,
}

#[derive(Debug, Clone)]
struct InstallTargets {
    codex: bool,
    claude_code: bool,
    cursor: bool,
    cline: bool,
    continue_agent: bool,
}

impl InstallTargets {
    fn has_selection(&self) -> bool {
        if self.codex || self.claude_code || self.cursor || self.cline || self.continue_agent {
            true
        } else {
            false
        }
    }

    fn selected_or_detected(self, project_root: &Path) -> Self {
        if self.has_selection() {
            return self;
        }
        let detected = detect_install_targets(project_root);
        if detected.has_selection() {
            detected
        } else {
            Self {
                codex: true,
                claude_code: true,
                cursor: true,
                cline: true,
                continue_agent: true,
            }
        }
    }
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    let project_root = std::env::current_dir()?;

    if should_check_freshness(&cli.command) {
        warn_stale_libraries(&project_root).ok();
    }
    if should_sync_skill(&cli.command) {
        sync_installed_skill(&project_root).ok();
    }

    match cli.command {
        Command::Login { api_url } => login(api_url.as_deref())?,
        Command::Init => init_project(&project_root)?,
        Command::Pull { libraries } => {
            if libraries.is_empty() {
                bail!("at least one library spec is required");
            }
            for library in libraries {
                pull_library(&project_root, &library)?;
            }
        }
        Command::Suggest { query, json } => suggest_libraries(&project_root, &query, json)?,
        Command::Search {
            query,
            library,
            json,
        } => search_docs(&project_root, &query, library.as_deref(), json)?,
        Command::Status => print_status(&project_root)?,
        Command::Update { library } => update_libraries(&project_root, library.as_deref())?,
        Command::Gc => gc(&project_root)?,
        Command::Config { command } => config(command)?,
        Command::Registry { command } => registry_command(&project_root, command)?,
        Command::Doctor => doctor(&project_root)?,
        Command::Install {
            codex,
            claude_code,
            cursor,
            cline,
            continue_agent,
        } => install_skill(
            &project_root,
            InstallTargets {
                codex,
                claude_code,
                cursor,
                cline,
                continue_agent,
            },
        )?,
    }

    Ok(())
}

fn should_check_freshness(command: &Command) -> bool {
    !matches!(
        command,
        Command::Login { .. } | Command::Config { .. } | Command::Registry { .. } | Command::Init
    )
}

fn should_sync_skill(command: &Command) -> bool {
    !matches!(command, Command::Install { .. } | Command::Registry { .. })
}

fn init_project(project_root: &Path) -> Result<()> {
    fs::create_dir_all(project_root.join(VENDORS_DIR)).with_context(|| {
        format!(
            "failed to create {}",
            project_root.join(VENDORS_DIR).display()
        )
    })?;

    let existing = read_lock(project_root).unwrap_or_default();
    let mut dependencies = detect_dependencies(project_root)?;
    dependencies.sort_by(|a, b| {
        (&a.ecosystem, &a.name, &a.requirement).cmp(&(&b.ecosystem, &b.name, &b.requirement))
    });

    let lock = ProjectLock {
        schema_version: 1,
        generated_at: Utc::now().to_rfc3339(),
        project_fingerprint: fingerprint_dependencies(&dependencies)?,
        dependencies,
        pulls: existing.pulls,
    };

    write_lock(project_root, &lock)?;
    update_gitignore(project_root)?;

    println!(
        "initialized Oz project metadata at {}",
        project_root.join(LOCK_FILE).display()
    );
    Ok(())
}

fn login(api_url: Option<&str>) -> Result<()> {
    let mut config = read_config()?;
    if let Some(api_url) = api_url {
        config.api_url = Some(api_url.trim_end_matches('/').to_string());
    }
    if config.api_url.is_none() {
        config.api_url = Some("http://127.0.0.1:8765".to_string());
    }

    let start: DeviceStartResponse = api_post_json_without_auth(
        config.api_url.as_deref().expect("api_url should be set"),
        "/auth/device",
        serde_json::json!({"client": "oz-cli"}),
    )?;
    println!(
        "Open {} and enter code {}",
        start.verification_uri, start.user_code
    );

    let token: TokenResponse = api_post_json_without_auth(
        config.api_url.as_deref().expect("api_url should be set"),
        "/auth/token",
        serde_json::json!({"device_code": start.device_code}),
    )?;
    store_auth_token(&mut config, &token.access_token);
    if config.telemetry.is_none() {
        config.telemetry = Some(true);
    }
    write_config(&config)?;
    println!(
        "logged in to {}",
        config.api_url.as_deref().expect("api_url should be set")
    );
    println!("telemetry is on by default and never sends query text; disable with `oz config set telemetry off`");
    Ok(())
}

fn pull_library(project_root: &Path, spec: &str) -> Result<()> {
    pull_library_impl(project_root, spec, false)
}

fn pull_library_impl(project_root: &Path, spec: &str, quiet: bool) -> Result<()> {
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
    if parsed.version.is_none() {
        let refs: RefResponse = api_get_json(
            config,
            &format!("/refs/{}/{}", parsed.vendor, parsed.library),
        )?;
        parsed.version = Some(refs.version);
    }
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

fn search_docs(
    project_root: &Path,
    query: &str,
    library_scope: Option<&str>,
    json: bool,
) -> Result<()> {
    let vendors_root = project_root.join(VENDORS_DIR);
    ensure_project(project_root)?;

    let terms = normalize_query(query);
    if terms.is_empty() {
        bail!("search query must contain at least one alphanumeric term");
    }

    let config = read_config()?;
    if configured_api_url(&config).is_some() {
        return search_docs_remote(project_root, &config, query, library_scope, json);
    }

    let scope = library_scope.map(parse_scope).transpose()?;
    let mut hits = search_vendor_tree(project_root, &vendors_root, &terms, &scope)?;

    if hits.is_empty() {
        if let Some(spec) = best_registry_match(project_root, &terms, &scope)? {
            pull_library_impl(project_root, &spec, true)?;
            hits = search_vendor_tree(project_root, &vendors_root, &terms, &scope)?;
        }
    }

    hits.sort_by(|a, b| {
        b.score
            .cmp(&a.score)
            .then_with(|| a.path.cmp(&b.path))
            .then(a.line.cmp(&b.line))
    });

    let output = hits
        .into_iter()
        .take(20)
        .map(|hit| {
            serde_json::json!({
                "path": to_project_path(project_root, &hit.path),
                "line": hit.line,
                "score": hit.score,
            })
        })
        .collect::<Vec<_>>();

    if json {
        println!(
            "{}",
            serde_json::to_string_pretty(&serde_json::json!({ "results": output }))?
        );
    } else {
        for hit in &output {
            println!(
                "{}:{}",
                hit["path"].as_str().unwrap_or_default(),
                hit["line"].as_u64().unwrap_or_default()
            );
        }
    }
    emit_telemetry(
        &config,
        "search_query",
        serde_json::json!({
            "query_length": query.len(),
            "result_count": output.len(),
            "library_scope": library_scope,
        }),
    );

    Ok(())
}

fn search_docs_remote(
    project_root: &Path,
    config: &OzConfig,
    query: &str,
    library_scope: Option<&str>,
    json: bool,
) -> Result<()> {
    let lock = read_lock(project_root)?;
    let response: SearchResponse = api_post_json(
        config,
        "/search",
        serde_json::json!({
            "query": query,
            "project_fingerprint": lock.project_fingerprint,
            "library_scope": library_scope,
            "max_results": 20,
        }),
    )?;

    for library in &response.libraries_to_pull {
        let spec = format!("{}/{}@{}", library.vendor, library.library, library.version);
        pull_library_impl(project_root, &spec, true)?;
    }

    if json {
        println!("{}", serde_json::to_string_pretty(&response)?);
    } else {
        for result in &response.results {
            if let Some(line) = result.line {
                println!("{}:{}", result.path, line);
            } else {
                println!("{}", result.path);
            }
        }
    }
    emit_telemetry(
        config,
        "search_query",
        serde_json::json!({
            "query_length": query.len(),
            "result_count": response.results.len(),
            "library_scope": library_scope,
        }),
    );
    Ok(())
}

fn search_vendor_tree(
    project_root: &Path,
    root: &Path,
    terms: &[String],
    scope: &Option<(String, String)>,
) -> Result<Vec<SearchHit>> {
    let mut hits = Vec::new();
    if !root.exists() {
        return Ok(hits);
    }

    for entry in WalkDir::new(root).sort_by_file_name() {
        let entry = entry.with_context(|| format!("failed walking {}", root.display()))?;
        if !entry.file_type().is_file()
            || entry.path().extension().and_then(|s| s.to_str()) != Some("md")
        {
            continue;
        }
        if !path_matches_scope(entry.path(), scope) {
            continue;
        }
        collect_file_hits(entry.path(), terms, &mut hits)?;
    }
    for hit in &mut hits {
        if hit.preview.is_empty() {
            hit.preview = to_project_path(project_root, &hit.path);
        }
    }
    Ok(hits)
}

fn print_status(project_root: &Path) -> Result<()> {
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

fn suggest_libraries(project_root: &Path, query: &str, json: bool) -> Result<()> {
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
            serde_json::json!({
                "vendor": library.vendor,
                "library": library.library,
                "version": library.version,
                "score": score,
                "reason": library.description,
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

    if json {
        println!("{}", serde_json::to_string_pretty(&response)?);
    } else {
        for result in &response.results {
            println!(
                "{}/{}@{}  score={}  {}",
                result.vendor, result.library, result.version, result.score, result.reason
            );
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

fn update_libraries(project_root: &Path, scope: Option<&str>) -> Result<()> {
    let lock = read_lock(project_root)?;
    let config = read_config().unwrap_or_default();
    let parsed_scope = scope.map(parse_scope).transpose()?;
    let pulls = lock
        .pulls
        .iter()
        .filter(|pull| {
            parsed_scope
                .as_ref()
                .map(|(vendor, library)| pull.vendor == *vendor && pull.library == *library)
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

fn gc(project_root: &Path) -> Result<()> {
    let tmp = project_root.join(CODO_DIR).join("tmp");
    if tmp.exists() {
        fs::remove_dir_all(&tmp).with_context(|| format!("failed to remove {}", tmp.display()))?;
    }

    let objects_root = global_objects_root()?;
    let referenced = referenced_object_shas(project_root)?;
    let mut removed = 0usize;
    if objects_root.exists() {
        for entry in WalkDir::new(objects_root.join("blobs"))
            .into_iter()
            .filter_map(|entry| entry.ok())
            .filter(|entry| entry.file_type().is_file())
        {
            let name = entry.file_name().to_string_lossy().to_string();
            if !referenced.contains(&name) {
                fs::remove_file(entry.path())
                    .with_context(|| format!("failed to remove {}", entry.path().display()))?;
                removed += 1;
            }
        }
    }
    let object_count = if objects_root.exists() {
        WalkDir::new(&objects_root)
            .into_iter()
            .filter_map(|entry| entry.ok())
            .filter(|entry| entry.file_type().is_file())
            .count()
    } else {
        0
    };
    println!(
        "removed {removed} unreferenced blobs; global object store contains {object_count} blobs"
    );
    Ok(())
}

fn referenced_object_shas(project_root: &Path) -> Result<BTreeSet<String>> {
    let mut referenced = BTreeSet::new();
    let mut roots = registered_projects().unwrap_or_default();
    roots.push(project_root.to_path_buf());
    roots.sort();
    roots.dedup();
    for root in roots {
        referenced.extend(referenced_object_shas_for_project(&root)?);
    }
    Ok(referenced)
}

fn referenced_object_shas_for_project(project_root: &Path) -> Result<BTreeSet<String>> {
    let mut referenced = BTreeSet::new();
    let lock = match read_lock(project_root) {
        Ok(lock) => lock,
        Err(_) => return Ok(referenced),
    };
    for pull in lock.pulls {
        let root = project_root.join(pull.path);
        if !root.exists() {
            continue;
        }
        for entry in WalkDir::new(&root)
            .into_iter()
            .filter_map(|entry| entry.ok())
            .filter(|entry| entry.file_type().is_file())
        {
            let bytes = fs::read(entry.path())
                .with_context(|| format!("failed to read {}", entry.path().display()))?;
            referenced.insert(sha256_hex(&bytes));
        }
    }
    Ok(referenced)
}

fn project_registry_path() -> Result<PathBuf> {
    Ok(dirs::home_dir()
        .context("failed to locate home directory")?
        .join(".codo")
        .join("projects.json"))
}

fn register_project(project_root: &Path) -> Result<()> {
    let path = project_registry_path()?;
    let mut projects = registered_projects().unwrap_or_default();
    let canonical = project_root
        .canonicalize()
        .unwrap_or_else(|_| project_root.to_path_buf())
        .to_string_lossy()
        .to_string();
    if !projects
        .iter()
        .any(|path| path.to_string_lossy() == canonical)
    {
        projects.push(PathBuf::from(canonical));
    }
    projects.sort();
    projects.dedup();
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)
            .with_context(|| format!("failed to create {}", parent.display()))?;
    }
    let encoded = projects
        .iter()
        .map(|path| path.to_string_lossy().to_string())
        .collect::<Vec<_>>();
    fs::write(
        &path,
        format!("{}\n", serde_json::to_string_pretty(&encoded)?),
    )
    .with_context(|| format!("failed to write {}", path.display()))
}

fn registered_projects() -> Result<Vec<PathBuf>> {
    let path = project_registry_path()?;
    if !path.exists() {
        return Ok(Vec::new());
    }
    let content =
        fs::read_to_string(&path).with_context(|| format!("failed to read {}", path.display()))?;
    let projects = serde_json::from_str::<Vec<String>>(&content)
        .with_context(|| format!("failed to parse {}", path.display()))?;
    Ok(projects
        .into_iter()
        .map(PathBuf::from)
        .filter(|path| path.join(LOCK_FILE).exists())
        .collect())
}

fn config(command: ConfigCommand) -> Result<()> {
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

fn doctor(project_root: &Path) -> Result<()> {
    let mut failed = false;
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
    let config = read_config().unwrap_or_default();
    if configured_api_url(&config).is_some() {
        check(
            "network reachability",
            api_get_json::<serde_json::Value>(&config, "/health").is_ok(),
            &mut failed,
        );
        check("auth token", auth_token(&config).is_some(), &mut failed);
    }

    if failed {
        bail!("doctor found problems");
    }
    println!("oz doctor: ok");
    Ok(())
}

fn install_skill(project_root: &Path, targets: InstallTargets) -> Result<()> {
    let targets = targets.selected_or_detected(project_root);
    let mut installed = Vec::new();
    if targets.codex {
        write_markdown_skill(&project_root.join("AGENTS.md"))?;
        installed.push("Codex");
    }
    if targets.claude_code {
        write_markdown_skill(&project_root.join("CLAUDE.md"))?;
        let claude_skill = project_root.join(".claude").join("skills").join("oz.md");
        write_markdown_skill(&claude_skill)?;
        installed.push("Claude Code");
    }
    if targets.cursor {
        write_markdown_skill(&project_root.join(".cursorrules"))?;
        let cursor_rule = project_root.join(".cursor").join("rules").join("oz.mdc");
        write_markdown_skill(&cursor_rule)?;
        installed.push("Cursor");
    }
    if targets.cline {
        write_markdown_skill(&project_root.join(".clinerules"))?;
        installed.push("Cline");
    }
    if targets.continue_agent {
        write_continue_config(&project_root.join(".continuerc"))?;
        installed.push("Continue");
    }
    installed.sort();
    println!("installed Oz instructions for {}", installed.join(", "));
    Ok(())
}

fn detect_install_targets(project_root: &Path) -> InstallTargets {
    let home = dirs::home_dir();
    let exists = |path: PathBuf| path.exists();
    InstallTargets {
        codex: exists(project_root.join("AGENTS.md"))
            || exists(project_root.join(".agents"))
            || home
                .as_ref()
                .map(|home| exists(home.join(".codex")))
                .unwrap_or(false),
        claude_code: exists(project_root.join("CLAUDE.md"))
            || exists(project_root.join(".claude"))
            || home
                .as_ref()
                .map(|home| exists(home.join(".claude")))
                .unwrap_or(false),
        cursor: exists(project_root.join(".cursor"))
            || exists(project_root.join(".cursorrules"))
            || home
                .as_ref()
                .map(|home| exists(home.join(".cursor")))
                .unwrap_or(false),
        cline: exists(project_root.join(".clinerules"))
            || exists(project_root.join(".cline"))
            || home
                .as_ref()
                .map(|home| exists(home.join(".cline")))
                .unwrap_or(false),
        continue_agent: exists(project_root.join(".continuerc"))
            || exists(project_root.join(".continue"))
            || home
                .as_ref()
                .map(|home| exists(home.join(".continue")))
                .unwrap_or(false),
    }
}

fn write_markdown_skill(path: &Path) -> Result<()> {
    let previous = fs::read_to_string(path).unwrap_or_default();
    let block = format!("{SKILL_START}\n{}\n{SKILL_END}", oz_skill());

    let next = if let Some(start) = previous.find(SKILL_START) {
        let end = previous
            .find(SKILL_END)
            .map(|idx| idx + SKILL_END.len())
            .context("AGENTS.md contains oz skill start marker without end marker")?;
        format!("{}{}{}", &previous[..start], block, &previous[end..])
    } else if previous.trim().is_empty() {
        format!("{block}\n")
    } else {
        format!("{}\n\n{}\n", previous.trim_end(), block)
    };

    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)
            .with_context(|| format!("failed to create {}", parent.display()))?;
    }
    fs::write(path, next).with_context(|| format!("failed to write {}", path.display()))?;
    Ok(())
}

fn sync_installed_skill(project_root: &Path) -> Result<()> {
    let config = read_config().unwrap_or_default();
    if config.auto_update_skill == Some(false) {
        return Ok(());
    }
    for path in [
        project_root.join("AGENTS.md"),
        project_root.join("CLAUDE.md"),
        project_root.join(".claude").join("skills").join("oz.md"),
        project_root.join(".cursorrules"),
        project_root.join(".cursor").join("rules").join("oz.mdc"),
        project_root.join(".clinerules"),
    ] {
        let content = fs::read_to_string(&path).unwrap_or_default();
        if content.contains(SKILL_START) {
            write_markdown_skill(&path)?;
        }
    }
    let continue_path = project_root.join(".continuerc");
    let content = fs::read_to_string(&continue_path).unwrap_or_default();
    if content.contains("ozSkill") {
        write_continue_config(&continue_path)?;
    }
    Ok(())
}

fn write_continue_config(path: &Path) -> Result<()> {
    let existing = fs::read_to_string(path)
        .ok()
        .and_then(|content| serde_json::from_str::<serde_json::Value>(&content).ok())
        .unwrap_or_else(|| serde_json::json!({}));
    let mut value = existing;
    value["ozSkill"] = serde_json::Value::String(oz_skill().to_string());
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)
            .with_context(|| format!("failed to create {}", parent.display()))?;
    }
    fs::write(path, format!("{}\n", serde_json::to_string_pretty(&value)?))
        .with_context(|| format!("failed to write {}", path.display()))?;
    Ok(())
}

fn ensure_project(project_root: &Path) -> Result<()> {
    if project_root.join(LOCK_FILE).exists() {
        return Ok(());
    }

    init_project(project_root)
}

fn read_lock(project_root: &Path) -> Result<ProjectLock> {
    let path = project_root.join(LOCK_FILE);
    let content =
        fs::read_to_string(&path).with_context(|| format!("failed to read {}", path.display()))?;
    serde_json::from_str(&content).with_context(|| format!("failed to parse {}", path.display()))
}

fn write_lock(project_root: &Path, lock: &ProjectLock) -> Result<()> {
    let path = project_root.join(LOCK_FILE);
    let parent = path.parent().context("lock path should have a parent")?;
    fs::create_dir_all(parent).with_context(|| format!("failed to create {}", parent.display()))?;
    let content = serde_json::to_string_pretty(lock)?;
    fs::write(&path, format!("{content}\n"))
        .with_context(|| format!("failed to write {}", path.display()))?;
    register_project(project_root).ok();
    Ok(())
}

fn update_gitignore(project_root: &Path) -> Result<()> {
    append_unique_line(&project_root.join(".gitignore"), ".codo/vendors/")?;
    append_unique_line(&project_root.join(".gitignore"), ".codo/tmp/")?;

    let codo_gitignore = project_root.join(CODO_DIR).join(".gitignore");
    fs::write(&codo_gitignore, "vendors/\ntmp/\n")
        .with_context(|| format!("failed to write {}", codo_gitignore.display()))?;
    Ok(())
}

fn append_unique_line(path: &Path, line: &str) -> Result<()> {
    let mut content = fs::read_to_string(path).unwrap_or_default();
    let normalized_line = line.trim().trim_start_matches('/');
    if content
        .lines()
        .map(|existing| existing.trim().trim_start_matches('/'))
        .any(|existing| existing == normalized_line)
    {
        return Ok(());
    }
    if !content.is_empty() && !content.ends_with('\n') {
        content.push('\n');
    }
    content.push_str(line);
    content.push('\n');
    fs::write(path, content).with_context(|| format!("failed to update {}", path.display()))
}

fn detect_dependencies(project_root: &Path) -> Result<Vec<Dependency>> {
    let mut dependencies = Vec::new();
    read_package_json(project_root, &mut dependencies)?;
    read_requirements(project_root, &mut dependencies)?;
    read_go_mod(project_root, &mut dependencies)?;
    read_cargo_toml(project_root, &mut dependencies)?;
    Ok(dependencies)
}

fn read_package_json(project_root: &Path, dependencies: &mut Vec<Dependency>) -> Result<()> {
    let path = project_root.join("package.json");
    if !path.exists() {
        return Ok(());
    }
    let value: serde_json::Value = serde_json::from_str(&fs::read_to_string(&path)?)
        .with_context(|| format!("failed to parse {}", path.display()))?;
    for section in [
        "dependencies",
        "devDependencies",
        "peerDependencies",
        "optionalDependencies",
    ] {
        if let Some(map) = value.get(section).and_then(|v| v.as_object()) {
            for (name, requirement) in map {
                dependencies.push(Dependency {
                    ecosystem: "npm".to_string(),
                    name: name.clone(),
                    requirement: requirement.as_str().unwrap_or("*").to_string(),
                });
            }
        }
    }
    Ok(())
}

fn read_requirements(project_root: &Path, dependencies: &mut Vec<Dependency>) -> Result<()> {
    let path = project_root.join("requirements.txt");
    if !path.exists() {
        return Ok(());
    }
    for line in fs::read_to_string(&path)?.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') || line.starts_with('-') {
            continue;
        }
        let name = line
            .split(['=', '<', '>', '~', '!', '['])
            .next()
            .unwrap_or(line)
            .trim();
        if !name.is_empty() {
            dependencies.push(Dependency {
                ecosystem: "python".to_string(),
                name: name.to_string(),
                requirement: line.to_string(),
            });
        }
    }
    Ok(())
}

fn read_go_mod(project_root: &Path, dependencies: &mut Vec<Dependency>) -> Result<()> {
    let path = project_root.join("go.mod");
    if !path.exists() {
        return Ok(());
    }
    let mut in_require_block = false;
    for raw in fs::read_to_string(&path)?.lines() {
        let line = raw.trim();
        if line == "require (" {
            in_require_block = true;
            continue;
        }
        if in_require_block && line == ")" {
            in_require_block = false;
            continue;
        }
        let candidate = if let Some(rest) = line.strip_prefix("require ") {
            rest
        } else if in_require_block {
            line
        } else {
            continue;
        };
        let mut parts = candidate.split_whitespace();
        if let (Some(name), Some(requirement)) = (parts.next(), parts.next()) {
            dependencies.push(Dependency {
                ecosystem: "go".to_string(),
                name: name.to_string(),
                requirement: requirement.to_string(),
            });
        }
    }
    Ok(())
}

fn read_cargo_toml(project_root: &Path, dependencies: &mut Vec<Dependency>) -> Result<()> {
    let path = project_root.join("Cargo.toml");
    if !path.exists() {
        return Ok(());
    }
    let mut in_deps = false;
    for raw in fs::read_to_string(&path)?.lines() {
        let line = raw.trim();
        if line.starts_with('[') {
            in_deps = matches!(
                line,
                "[dependencies]" | "[dev-dependencies]" | "[build-dependencies]"
            );
            continue;
        }
        if !in_deps || line.is_empty() || line.starts_with('#') {
            continue;
        }
        if let Some((name, requirement)) = line.split_once('=') {
            dependencies.push(Dependency {
                ecosystem: "rust".to_string(),
                name: name.trim().to_string(),
                requirement: requirement.trim().trim_matches('"').to_string(),
            });
        }
    }
    Ok(())
}

fn fingerprint_dependencies(dependencies: &[Dependency]) -> Result<String> {
    let encoded = serde_json::to_vec(dependencies)?;
    Ok(hex_digest(&encoded))
}

fn hex_digest(bytes: &[u8]) -> String {
    let digest = Sha256::digest(bytes);
    let mut output = String::with_capacity(digest.len() * 2);
    for byte in digest {
        output.push_str(&format!("{byte:02x}"));
    }
    output
}

fn parse_library_spec(input: &str) -> Result<LibrarySpec> {
    let (name, version) = match input.rfind('@') {
        Some(idx) if idx > 0 => (&input[..idx], Some(input[idx + 1..].to_string())),
        _ => (input, None),
    };
    if name.trim().is_empty() {
        bail!("library name cannot be empty");
    }

    let (vendor, library) = name
        .split_once('/')
        .map(|(vendor, library)| (vendor.to_string(), library.to_string()))
        .unwrap_or_else(|| ("npm".to_string(), name.to_string()));
    if vendor.is_empty() || library.is_empty() {
        bail!("library spec must be <vendor>/<library> or <library>");
    }

    Ok(LibrarySpec {
        vendor,
        library,
        version,
    })
}

fn parse_scope(input: &str) -> Result<(String, String)> {
    let spec = parse_library_spec(input)?;
    Ok((spec.vendor, spec.library))
}

fn resolve_registry_source(project_root: &Path, spec: &mut LibrarySpec) -> Result<RegistrySource> {
    let catalog = load_or_build_catalog(project_root).ok();
    if let Some(catalog) = catalog {
        apply_lockfile_version_hint(project_root, spec, &catalog);
        if let Some(entry) = best_catalog_entry(&catalog, spec) {
            spec.version = Some(entry.version.clone());
            if let Some(pack_path) = &entry.pack_path {
                let absolute_pack = repo_root(project_root)
                    .unwrap_or_else(|| project_root.to_path_buf())
                    .join(pack_path);
                if absolute_pack.exists() {
                    return Ok(RegistrySource::Pack(absolute_pack));
                }
            }
            let absolute_fixture = repo_root(project_root)
                .unwrap_or_else(|| project_root.to_path_buf())
                .join(&entry.fixture_path);
            if absolute_fixture.exists() {
                return Ok(RegistrySource::Fixture(absolute_fixture));
            }
        }
    }

    resolve_fixture_source(project_root, spec).map(RegistrySource::Fixture)
}

fn best_catalog_entry<'a>(
    catalog: &'a RegistryCatalog,
    spec: &LibrarySpec,
) -> Option<&'a CatalogLibrary> {
    let mut matches = catalog
        .libraries
        .iter()
        .filter(|entry| {
            entry.vendor == spec.vendor
                && entry.library == spec.library
                && spec
                    .version
                    .as_ref()
                    .map(|version| entry.version == *version)
                    .unwrap_or(true)
        })
        .collect::<Vec<_>>();
    matches.sort_by(|a, b| a.version.cmp(&b.version));
    matches.pop()
}

fn apply_lockfile_version_hint(
    project_root: &Path,
    spec: &mut LibrarySpec,
    catalog: &RegistryCatalog,
) {
    if spec.version.is_some() {
        return;
    }
    for version_hint in lockfile_version_hints(project_root, spec) {
        if catalog.libraries.iter().any(|entry| {
            entry.vendor == spec.vendor
                && entry.library == spec.library
                && entry.version == version_hint
        }) {
            spec.version = Some(version_hint);
            return;
        }
    }
}

fn lockfile_version_hint(project_root: &Path, spec: &LibrarySpec) -> Option<String> {
    lockfile_version_hints(project_root, spec)
        .into_iter()
        .find(|candidate| !candidate.is_empty())
}

fn lockfile_version_hints(project_root: &Path, spec: &LibrarySpec) -> Vec<String> {
    let Ok(lock) = read_lock(project_root) else {
        return Vec::new();
    };
    let aliases = library_aliases(spec);
    lock.dependencies
        .iter()
        .filter(|dependency| aliases.contains(&dependency.name.to_ascii_lowercase()))
        .flat_map(|dependency| version_candidates_from_requirement(&dependency.requirement))
        .collect()
}

fn library_aliases(spec: &LibrarySpec) -> BTreeSet<String> {
    let mut aliases = BTreeSet::new();
    aliases.insert(spec.library.to_ascii_lowercase());
    aliases.insert(spec.library.replace(".js", "").to_ascii_lowercase());
    aliases.insert(spec.library.replace("-node", "").to_ascii_lowercase());
    aliases.insert(spec.library.replace("-typescript", "").to_ascii_lowercase());
    match (spec.vendor.as_str(), spec.library.as_str()) {
        ("vercel", "next.js") => {
            aliases.insert("next".to_string());
        }
        ("facebook", "react") => {
            aliases.insert("react".to_string());
            aliases.insert("react-dom".to_string());
        }
        ("tailwindlabs", "tailwindcss") => {
            aliases.insert("tailwind".to_string());
            aliases.insert("tailwindcss".to_string());
        }
        ("openai", "openai-node") => {
            aliases.insert("openai".to_string());
        }
        ("anthropics", "anthropic-sdk-typescript") => {
            aliases.insert("@anthropic-ai/sdk".to_string());
            aliases.insert("anthropic".to_string());
        }
        _ => {}
    }
    aliases
}

fn version_candidates_from_requirement(requirement: &str) -> Vec<String> {
    let cleaned = requirement
        .trim()
        .trim_matches('"')
        .trim_start_matches(['^', '~', '>', '<', '=', 'v', ' ']);
    let numeric = cleaned
        .split(|ch: char| !(ch.is_ascii_digit() || ch == '.'))
        .find(|part| part.chars().any(|ch| ch.is_ascii_digit()))
        .unwrap_or("");
    if numeric.is_empty() {
        return Vec::new();
    }
    let mut candidates = Vec::new();
    if let Some(major) = numeric.split('.').next() {
        if !major.is_empty() {
            candidates.push(major.to_string());
        }
    }
    if candidates.iter().all(|candidate| candidate != numeric) {
        candidates.push(numeric.to_string());
    }
    candidates
}

fn resolve_fixture_source(project_root: &Path, spec: &mut LibrarySpec) -> Result<PathBuf> {
    let registry = fixtures_root(project_root)
        .context("could not find registry/fixtures from current project")?;
    let library_root = registry.join(&spec.vendor).join(&spec.library);
    if !library_root.exists() {
        bail!(
            "library {}/{} is not in the local development registry",
            spec.vendor,
            spec.library
        );
    }

    if let Some(version) = &spec.version {
        let exact = library_root.join(version);
        if exact.exists() {
            return Ok(exact);
        }
        bail!(
            "version {} is not available for {}/{} in the local development registry",
            version,
            spec.vendor,
            spec.library
        );
    }

    let mut versions = fs::read_dir(&library_root)?
        .filter_map(|entry| entry.ok())
        .filter(|entry| entry.file_type().map(|kind| kind.is_dir()).unwrap_or(false))
        .map(|entry| entry.file_name().to_string_lossy().to_string())
        .collect::<Vec<_>>();
    versions.sort();
    let version = versions
        .pop()
        .with_context(|| format!("no versions found under {}", library_root.display()))?;
    spec.version = Some(version.clone());
    Ok(library_root.join(version))
}

fn best_registry_match(
    project_root: &Path,
    terms: &[String],
    scope: &Option<(String, String)>,
) -> Result<Option<String>> {
    let fixtures = match fixtures_root(project_root) {
        Some(path) => path,
        None => return Ok(None),
    };

    let mut best: Option<(usize, String)> = None;
    for entry in WalkDir::new(&fixtures).sort_by_file_name() {
        let entry = entry.with_context(|| format!("failed walking {}", fixtures.display()))?;
        if !entry.file_type().is_file()
            || entry.path().extension().and_then(|s| s.to_str()) != Some("md")
        {
            continue;
        }

        let Some((vendor, library, version)) = fixture_identity(&fixtures, entry.path()) else {
            continue;
        };
        if scope
            .as_ref()
            .map(|(scope_vendor, scope_library)| {
                vendor == *scope_vendor && library == *scope_library
            })
            .unwrap_or(false)
            == false
            && scope.is_some()
        {
            continue;
        }

        let content = fs::read_to_string(entry.path())
            .with_context(|| format!("failed to read {}", entry.path().display()))?
            .to_ascii_lowercase();
        let score = terms
            .iter()
            .map(|term| content.matches(term.as_str()).count())
            .sum::<usize>();
        if score == 0 {
            continue;
        }
        let spec = format!("{vendor}/{library}@{version}");
        if best
            .as_ref()
            .map(|(best_score, _)| score > *best_score)
            .unwrap_or(true)
        {
            best = Some((score, spec));
        }
    }
    Ok(best.map(|(_, spec)| spec))
}

fn fixture_identity(fixtures_root: &Path, file_path: &Path) -> Option<(String, String, String)> {
    let relative = file_path.strip_prefix(fixtures_root).ok()?;
    let mut components = relative.components();
    let vendor = components.next()?.as_os_str().to_string_lossy().to_string();
    let library = components.next()?.as_os_str().to_string_lossy().to_string();
    let version = components.next()?.as_os_str().to_string_lossy().to_string();
    Some((vendor, library, version))
}

fn fixtures_root(project_root: &Path) -> Option<PathBuf> {
    repo_root(project_root).map(|root| root.join(FIXTURES_DIR))
}

fn packs_root(project_root: &Path) -> Option<PathBuf> {
    repo_root(project_root).map(|root| root.join(PACKS_DIR))
}

fn catalog_path(project_root: &Path) -> Option<PathBuf> {
    repo_root(project_root).map(|root| root.join(CATALOG_FILE))
}

fn repo_root(project_root: &Path) -> Option<PathBuf> {
    for ancestor in project_root.ancestors() {
        let candidate = ancestor.join(REGISTRY_DIR);
        if candidate.exists() {
            return Some(ancestor.to_path_buf());
        }
    }
    None
}

fn load_or_build_catalog(project_root: &Path) -> Result<RegistryCatalog> {
    if let Some(path) = catalog_path(project_root) {
        if path.exists() {
            let content = fs::read_to_string(&path)
                .with_context(|| format!("failed to read {}", path.display()))?;
            return serde_json::from_str(&content)
                .with_context(|| format!("failed to parse {}", path.display()));
        }
    }
    build_catalog(project_root)
}

fn build_catalog(project_root: &Path) -> Result<RegistryCatalog> {
    let fixtures = fixtures_root(project_root)
        .context("could not find registry/fixtures from current project")?;
    let mut libraries = Vec::new();

    for vendor_entry in fs::read_dir(&fixtures)
        .with_context(|| format!("failed to read {}", fixtures.display()))?
        .filter_map(|entry| entry.ok())
    {
        if !vendor_entry
            .file_type()
            .map(|kind| kind.is_dir())
            .unwrap_or(false)
        {
            continue;
        }
        let vendor = vendor_entry.file_name().to_string_lossy().to_string();
        for library_entry in fs::read_dir(vendor_entry.path())
            .with_context(|| format!("failed to read {}", vendor_entry.path().display()))?
            .filter_map(|entry| entry.ok())
        {
            if !library_entry
                .file_type()
                .map(|kind| kind.is_dir())
                .unwrap_or(false)
            {
                continue;
            }
            let library = library_entry.file_name().to_string_lossy().to_string();
            for version_entry in fs::read_dir(library_entry.path())
                .with_context(|| format!("failed to read {}", library_entry.path().display()))?
                .filter_map(|entry| entry.ok())
            {
                if !version_entry
                    .file_type()
                    .map(|kind| kind.is_dir())
                    .unwrap_or(false)
                {
                    continue;
                }
                let version = version_entry.file_name().to_string_lossy().to_string();
                libraries.push(read_catalog_entry(
                    project_root,
                    &fixtures,
                    &version_entry.path(),
                    &vendor,
                    &library,
                    &version,
                )?);
            }
        }
    }

    libraries.sort_by(|a, b| {
        (&a.vendor, &a.library, &a.version).cmp(&(&b.vendor, &b.library, &b.version))
    });
    Ok(RegistryCatalog {
        schema_version: 1,
        generated_at: Utc::now().to_rfc3339(),
        libraries,
    })
}

fn read_catalog_entry(
    project_root: &Path,
    fixtures_root: &Path,
    fixture: &Path,
    vendor: &str,
    library: &str,
    version: &str,
) -> Result<CatalogLibrary> {
    let meta_path = fixture.join("_meta.json");
    let meta = if meta_path.exists() {
        serde_json::from_str::<serde_json::Value>(&fs::read_to_string(&meta_path)?)
            .with_context(|| format!("failed to parse {}", meta_path.display()))?
    } else {
        serde_json::json!({})
    };
    let source_urls = meta
        .get("source_urls")
        .and_then(|value| value.as_array())
        .map(|values| {
            values
                .iter()
                .filter_map(|value| value.as_str().map(ToString::to_string))
                .collect::<Vec<_>>()
        })
        .unwrap_or_default();
    let ref_sha = meta
        .get("ref_sha")
        .and_then(|value| value.as_str())
        .unwrap_or("local-fixture")
        .to_string();
    let indexed_at = meta
        .get("indexed_at")
        .and_then(|value| value.as_str())
        .unwrap_or("")
        .to_string();

    let description = read_description(fixture, library)?;
    let keywords = collect_keywords(fixture, vendor, library, version)?;
    let pack_path = packs_root(project_root)
        .map(|root| {
            root.join(vendor)
                .join(library)
                .join(format!("{version}.ozpack"))
        })
        .filter(|path| path.exists())
        .map(|path| {
            repo_root(project_root)
                .map(|root| to_project_path(&root, &path))
                .unwrap_or_else(|| path.to_string_lossy().to_string())
        });
    let fixture_path = repo_root(project_root)
        .map(|root| to_project_path(&root, fixture))
        .unwrap_or_else(|| {
            fixture
                .strip_prefix(fixtures_root)
                .unwrap_or(fixture)
                .to_string_lossy()
                .to_string()
        });

    Ok(CatalogLibrary {
        vendor: vendor.to_string(),
        library: library.to_string(),
        version: version.to_string(),
        description,
        source_urls,
        keywords,
        fixture_path,
        pack_path,
        ref_sha,
        indexed_at,
    })
}

fn read_description(fixture: &Path, library: &str) -> Result<String> {
    let readme = fixture.join("README.md");
    if readme.exists() {
        for line in fs::read_to_string(&readme)?.lines() {
            let trimmed = line.trim();
            if !trimmed.is_empty() && !trimmed.starts_with('#') {
                return Ok(trimmed.chars().take(220).collect());
            }
        }
    }
    Ok(format!("{library} documentation"))
}

fn collect_keywords(
    fixture: &Path,
    vendor: &str,
    library: &str,
    version: &str,
) -> Result<Vec<String>> {
    let mut keywords = BTreeSet::new();
    keywords.insert(vendor.to_string());
    keywords.insert(library.to_string());
    keywords.insert(version.to_string());

    for entry in WalkDir::new(fixture).sort_by_file_name() {
        let entry = entry.with_context(|| format!("failed walking {}", fixture.display()))?;
        if !entry.file_type().is_file()
            || entry.path().extension().and_then(|value| value.to_str()) != Some("md")
        {
            continue;
        }
        let content = fs::read_to_string(entry.path())
            .with_context(|| format!("failed to read {}", entry.path().display()))?;
        for word in normalize_query(&content) {
            if word.len() >= 4 {
                keywords.insert(word);
            }
            if keywords.len() >= 80 {
                break;
            }
        }
    }
    Ok(keywords.into_iter().collect())
}

fn write_catalog(project_root: &Path, catalog: &RegistryCatalog) -> Result<()> {
    let path = catalog_path(project_root).context("could not locate registry/catalog.json")?;
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)
            .with_context(|| format!("failed to create {}", parent.display()))?;
    }
    fs::write(
        &path,
        format!("{}\n", serde_json::to_string_pretty(catalog)?),
    )
    .with_context(|| format!("failed to write {}", path.display()))
}

fn build_packs(project_root: &Path) -> Result<()> {
    let fixtures = fixtures_root(project_root)
        .context("could not find registry/fixtures from current project")?;
    let packs = packs_root(project_root).context("could not locate registry/packs")?;

    for entry in WalkDir::new(&fixtures)
        .min_depth(3)
        .max_depth(3)
        .sort_by_file_name()
    {
        let entry = entry.with_context(|| format!("failed walking {}", fixtures.display()))?;
        if !entry.file_type().is_dir() {
            continue;
        }
        let Some((vendor, library, version)) =
            fixture_identity(&fixtures, &entry.path().join("INDEX.md"))
        else {
            continue;
        };
        let destination = packs
            .join(&vendor)
            .join(&library)
            .join(format!("{version}.ozpack"));
        write_pack(entry.path(), &destination, &vendor, &library, &version)?;
    }
    Ok(())
}

fn latest_version(project_root: &Path, vendor: &str, library: &str) -> Result<Option<String>> {
    let catalog = load_or_build_catalog(project_root)?;
    let mut versions = catalog
        .libraries
        .into_iter()
        .filter(|entry| entry.vendor == vendor && entry.library == library)
        .map(|entry| entry.version)
        .collect::<Vec<_>>();
    versions.sort();
    Ok(versions.pop())
}

fn latest_version_for(
    project_root: &Path,
    config: &OzConfig,
    vendor: &str,
    library: &str,
) -> Result<Option<String>> {
    if configured_api_url(config).is_some() {
        let refs: RefResponse = api_get_json(config, &format!("/refs/{vendor}/{library}"))?;
        return Ok(Some(refs.version));
    }
    latest_version(project_root, vendor, library)
}

fn record_index_request(
    project_root: &Path,
    query: &str,
    requested_library: Option<&str>,
) -> Result<()> {
    let root = repo_root(project_root).unwrap_or_else(|| project_root.to_path_buf());
    let queue_path = root
        .join(REGISTRY_DIR)
        .join("admin")
        .join("index_requests.jsonl");
    if let Some(parent) = queue_path.parent() {
        fs::create_dir_all(parent)
            .with_context(|| format!("failed to create {}", parent.display()))?;
    }
    let event = serde_json::json!({
        "created_at": Utc::now().to_rfc3339(),
        "query_length": query.len(),
        "requested_library": requested_library,
    });
    append_jsonl(&queue_path, &event)
}

fn append_jsonl(path: &Path, value: &serde_json::Value) -> Result<()> {
    let mut file = fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(path)
        .with_context(|| format!("failed to open {}", path.display()))?;
    writeln!(file, "{}", serde_json::to_string(value)?)
        .with_context(|| format!("failed to write {}", path.display()))
}

fn config_path() -> Result<PathBuf> {
    Ok(dirs::home_dir()
        .context("failed to locate home directory")?
        .join(".codo")
        .join("config.json"))
}

fn read_config() -> Result<OzConfig> {
    let path = config_path()?;
    if !path.exists() {
        return Ok(OzConfig::default());
    }
    let content =
        fs::read_to_string(&path).with_context(|| format!("failed to read {}", path.display()))?;
    serde_json::from_str(&content).with_context(|| format!("failed to parse {}", path.display()))
}

fn write_config(config: &OzConfig) -> Result<()> {
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

fn auth_token(config: &OzConfig) -> Option<String> {
    if keychain_disabled() {
        return config.auth_token.clone();
    }
    read_keychain_token()
        .ok()
        .flatten()
        .or_else(|| config.auth_token.clone())
}

fn store_auth_token(config: &mut OzConfig, token: &str) {
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

fn keychain_disabled() -> bool {
    std::env::var("OZ_DISABLE_KEYCHAIN")
        .map(|value| matches!(value.as_str(), "1" | "true" | "yes" | "on"))
        .unwrap_or(false)
}

#[cfg(target_os = "macos")]
fn write_keychain_token(token: &str) -> Result<()> {
    let status = ProcessCommand::new("security")
        .args([
            "add-generic-password",
            "-a",
            KEYCHAIN_ACCOUNT,
            "-s",
            KEYCHAIN_SERVICE,
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
    let output = ProcessCommand::new("security")
        .args([
            "find-generic-password",
            "-a",
            KEYCHAIN_ACCOUNT,
            "-s",
            KEYCHAIN_SERVICE,
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
    let _ = ProcessCommand::new("security")
        .args([
            "delete-generic-password",
            "-a",
            KEYCHAIN_ACCOUNT,
            "-s",
            KEYCHAIN_SERVICE,
        ])
        .status();
    Ok(())
}

#[cfg(target_os = "linux")]
fn write_keychain_token(token: &str) -> Result<()> {
    let mut child = ProcessCommand::new("secret-tool")
        .args([
            "store",
            "--label=Oz CLI token",
            "service",
            KEYCHAIN_SERVICE,
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
    let output = ProcessCommand::new("secret-tool")
        .args([
            "lookup",
            "service",
            KEYCHAIN_SERVICE,
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
    let _ = ProcessCommand::new("secret-tool")
        .args([
            "clear",
            "service",
            KEYCHAIN_SERVICE,
            "account",
            KEYCHAIN_ACCOUNT,
        ])
        .status();
    Ok(())
}

#[cfg(target_os = "windows")]
fn write_keychain_token(token: &str) -> Result<()> {
    let status = ProcessCommand::new("cmdkey")
        .args([
            &format!("/generic:{KEYCHAIN_SERVICE}"),
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
fn delete_keychain_token() -> Result<()> {
    let _ = ProcessCommand::new("cmdkey")
        .arg(&format!("/delete:{KEYCHAIN_SERVICE}"))
        .status();
    Ok(())
}

#[cfg(not(any(target_os = "macos", target_os = "linux", target_os = "windows")))]
fn write_keychain_token(_token: &str) -> Result<()> {
    bail!("no OS keychain integration for this platform")
}

#[cfg(not(any(target_os = "macos", target_os = "linux", target_os = "windows")))]
fn read_keychain_token() -> Result<Option<String>> {
    Ok(None)
}

#[cfg(not(any(target_os = "macos", target_os = "linux", target_os = "windows")))]
fn delete_keychain_token() -> Result<()> {
    Ok(())
}

fn get_config_value(config: &OzConfig, key: &str) -> Option<String> {
    match key {
        "telemetry" => config.telemetry.map(|value| value.to_string()),
        "api_url" => config.api_url.clone(),
        "auth_token" => auth_token(config),
        "auto_update_skill" => config.auto_update_skill.map(|value| value.to_string()),
        _ => None,
    }
}

fn set_config_value(config: &mut OzConfig, key: &str, value: &str) -> Result<()> {
    match key {
        "telemetry" => config.telemetry = Some(parse_bool(value)?),
        "api_url" => config.api_url = Some(value.trim_end_matches('/').to_string()),
        "auth_token" => store_auth_token(config, value),
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

fn warn_stale_libraries(project_root: &Path) -> Result<()> {
    let lock = match read_lock(project_root) {
        Ok(lock) => lock,
        Err(_) => return Ok(()),
    };
    if lock.pulls.is_empty() {
        return Ok(());
    }
    let config = read_config().unwrap_or_default();
    if configured_api_url(&config).is_some() {
        let mut route = format!(
            "/refs?fingerprint={}",
            url_component(&lock.project_fingerprint)
        );
        for pull in &lock.pulls {
            route.push_str("&library=");
            route.push_str(&url_component(&format!(
                "{}/{}@{}",
                pull.vendor, pull.library, pull.version
            )));
        }
        if let Ok(response) = api_get_json::<BulkRefsResponse>(&config, &route) {
            for stale in response.stale_libraries {
                eprintln!(
                    "oz: {}/{}@{} is stale (newer: {}). Run 'oz update {}/{}'.",
                    stale.vendor,
                    stale.library,
                    stale.version,
                    stale.newer_version,
                    stale.vendor,
                    stale.library
                );
            }
            return Ok(());
        }
    }

    for pull in lock.pulls {
        if let Some(latest) = latest_version(project_root, &pull.vendor, &pull.library)
            .ok()
            .flatten()
        {
            if latest != pull.version {
                eprintln!(
                    "oz: {}/{}@{} is stale (newer: {}). Run 'oz update {}/{}'.",
                    pull.vendor, pull.library, pull.version, latest, pull.vendor, pull.library
                );
            }
        }
    }
    Ok(())
}

fn url_component(value: &str) -> String {
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

fn emit_telemetry(config: &OzConfig, event: &str, properties: serde_json::Value) {
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

fn configured_api_url(config: &OzConfig) -> Option<String> {
    config
        .api_url
        .as_ref()
        .map(|value| value.trim().trim_end_matches('/').to_string())
        .filter(|value| !value.is_empty())
}

fn api_get_json<T: DeserializeOwned>(config: &OzConfig, route: &str) -> Result<T> {
    let base_url = configured_api_url(config).context("api_url is not configured")?;
    let url = route_url(&base_url, route);
    let mut request = ureq::get(&url);
    if let Some(token) = auth_token(config) {
        request = request.set("Authorization", &format!("Bearer {token}"));
    }
    let response = request.call().map_err(format_ureq_error)?;
    response
        .into_json::<T>()
        .with_context(|| format!("failed to decode JSON response from {url}"))
}

fn api_get_bytes(config: &OzConfig, route: &str) -> Result<Vec<u8>> {
    let base_url = configured_api_url(config).context("api_url is not configured")?;
    let url = route_url(&base_url, route);
    let mut request = ureq::get(&url);
    if let Some(token) = auth_token(config) {
        request = request.set("Authorization", &format!("Bearer {token}"));
    }
    let response = request.call().map_err(format_ureq_error)?;
    let mut reader = response.into_reader();
    let mut bytes = Vec::new();
    reader
        .read_to_end(&mut bytes)
        .with_context(|| format!("failed reading response bytes from {url}"))?;
    Ok(bytes)
}

fn api_post_json<T: DeserializeOwned>(
    config: &OzConfig,
    route: &str,
    body: serde_json::Value,
) -> Result<T> {
    let base_url = configured_api_url(config).context("api_url is not configured")?;
    let url = route_url(&base_url, route);
    let mut request = ureq::post(&url).set("Content-Type", "application/json");
    if let Some(token) = auth_token(config) {
        request = request.set("Authorization", &format!("Bearer {token}"));
    }
    let response = request.send_json(body).map_err(format_ureq_error)?;
    response
        .into_json::<T>()
        .with_context(|| format!("failed to decode JSON response from {url}"))
}

fn api_post_json_without_auth<T: DeserializeOwned>(
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

fn format_ureq_error(error: ureq::Error) -> anyhow::Error {
    match error {
        ureq::Error::Status(code, response) => {
            let body = response.into_string().unwrap_or_default();
            anyhow::anyhow!("registry API returned HTTP {code}: {body}")
        }
        ureq::Error::Transport(error) => anyhow::anyhow!("registry API transport error: {error}"),
    }
}

fn global_objects_root() -> Result<PathBuf> {
    let home = dirs::home_dir().context("failed to locate home directory")?;
    Ok(home.join(".codo").join("objects"))
}

fn upsert_pull(lock: &mut ProjectLock, pull: PulledLibrary) {
    if let Some(existing) = lock
        .pulls
        .iter_mut()
        .find(|existing| existing.vendor == pull.vendor && existing.library == pull.library)
    {
        *existing = pull;
    } else {
        lock.pulls.push(pull);
    }
    lock.pulls
        .sort_by(|a, b| (&a.vendor, &a.library).cmp(&(&b.vendor, &b.library)));
}

fn normalize_query(query: &str) -> Vec<String> {
    query
        .split(|ch: char| !ch.is_alphanumeric() && ch != '_')
        .filter(|term| !term.is_empty())
        .map(|term| term.to_ascii_lowercase())
        .collect()
}

fn path_matches_scope(path: &Path, scope: &Option<(String, String)>) -> bool {
    let Some((vendor, library)) = scope else {
        return true;
    };

    let components = path
        .components()
        .map(|component| component.as_os_str().to_string_lossy().to_string())
        .collect::<Vec<_>>();

    components
        .windows(2)
        .any(|window| window[0] == *vendor && window[1].starts_with(&format!("{library}@")))
}

fn collect_file_hits(path: &Path, terms: &[String], hits: &mut Vec<SearchHit>) -> Result<()> {
    let content =
        fs::read_to_string(path).with_context(|| format!("failed to read {}", path.display()))?;
    for (idx, line) in content.lines().enumerate() {
        let normalized = line.to_ascii_lowercase();
        let score = terms
            .iter()
            .filter(|term| normalized.contains(term.as_str()))
            .count();
        if score > 0 {
            hits.push(SearchHit {
                path: path.to_path_buf(),
                line: idx + 1,
                score,
                preview: line.trim().chars().take(160).collect(),
            });
        }
    }
    Ok(())
}

fn check(label: &str, ok: bool, failed: &mut bool) {
    if ok {
        println!("ok   {label}");
    } else {
        println!("fail {label}");
        *failed = true;
    }
}

fn to_project_path(project_root: &Path, path: &Path) -> String {
    let relative = path.strip_prefix(project_root).unwrap_or(path);
    relative.to_string_lossy().replace('\\', "/")
}

fn oz_skill() -> &'static str {
    r#"# Oz: Live documentation for external libraries

When this project uses an external library (anything from package.json,
requirements.txt, go.mod, Cargo.toml, or any SDK/framework you're integrating),
use Oz to get version-accurate docs before writing code.

DO NOT consult the web or your training memory for external library APIs
before trying Oz. Pull first, then read.

## Workflow

1. Identify the library you need. If unsure, run:
   `oz suggest "<one sentence describing what you're trying to do>"`
   This returns a ranked list of library names.

2. Pull the docs:
   `oz pull <library>`
   Docs land in `.codo/vendors/<library>@<version>/` as Markdown files.

3. Find the right files for your task. Two ways to search:

   **Semantic search (preferred when you don't know the file path):**
   `oz search "<query>" [<library>]`
   Returns a ranked list of local file paths under `.codo/vendors/...`.
   Auto-pulls any referenced libraries that aren't local yet.
   Example: `oz search "middleware jwt cookies" vercel/next.js`

   **Native file tools (preferred when you know roughly where to look):**
   Use your normal Glob, Grep, and Read tools on `.codo/vendors/...`, exactly
   as you would search source code in this repo:
   - Glob to discover structure: `.codo/vendors/<library>@<version>/**/*.md`
   - Grep for keywords, symbol names, error messages, concepts
   - Start with `INDEX.md` for an overview
   - Symbol lookup: `_symbols/` contains one file per public API,
     named by symbol (e.g. `_symbols/NextRequest.md`)

4. Read the files. After `oz search` returns paths, or after Glob/Grep
   locates files, use Read to load their contents. `oz search` only returns
   paths; content always comes from your Read tool.

5. If Oz prints "library X is stale" on stderr, run `oz update <library>`
   before continuing.

## Rules

- Pull before you guess. A 200ms pull beats a hallucinated API call.
- For unfamiliar libraries, start with `oz search` — it's a one-shot way to
  find the right files across multiple libraries at once.
- Version matters: Oz pins to this project's lockfile, your memory does not.
- If `oz suggest` returns nothing useful, tell the user the library isn't
  indexed yet (Oz has logged the request).
"#
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_vendor_library_version_specs() {
        let parsed = parse_library_spec("vercel/next.js@15").unwrap();
        assert_eq!(parsed.vendor, "vercel");
        assert_eq!(parsed.library, "next.js");
        assert_eq!(parsed.version.as_deref(), Some("15"));
    }

    #[test]
    fn parses_unscoped_specs_as_npm() {
        let parsed = parse_library_spec("react").unwrap();
        assert_eq!(parsed.vendor, "npm");
        assert_eq!(parsed.library, "react");
        assert_eq!(parsed.version, None);
    }

    #[test]
    fn normalizes_queries() {
        assert_eq!(
            normalize_query("middleware jwt cookies.get"),
            vec!["middleware", "jwt", "cookies", "get"]
        );
    }
}
