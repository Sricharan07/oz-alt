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
use std::time::{Duration, Instant};
use walkdir::WalkDir;

mod api;
mod commands;
mod freshness;
mod install;
mod project;
mod registry;
mod search;
mod settings;

use api::*;
use commands::*;
use freshness::*;
use install::*;
use project::*;
use registry::*;
use search::*;
use settings::*;

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
    expires_in: Option<u64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct TokenResponse {
    access_token: String,
    token_type: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct SuggestResponse {
    results: Vec<SuggestResult>,
    stale_libraries: Vec<StaleLibrary>,
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
    stale_libraries: Vec<StaleLibrary>,
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

fn normalize_query(query: &str) -> Vec<String> {
    query
        .split(|ch: char| !ch.is_alphanumeric() && ch != '_')
        .filter(|term| !term.is_empty())
        .map(|term| term.to_ascii_lowercase())
        .collect()
}

fn to_project_path(project_root: &Path, path: &Path) -> String {
    let relative = path.strip_prefix(project_root).unwrap_or(path);
    relative.to_string_lossy().replace('\\', "/")
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
