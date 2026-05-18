use super::*;

pub(crate) fn parse_library_spec(input: &str) -> Result<LibrarySpec> {
    let cleaned = input.trim().trim_start_matches('/');
    let (mut name, mut version) = match cleaned.rfind('@') {
        Some(idx) if idx > 0 => (&cleaned[..idx], Some(cleaned[idx + 1..].to_string())),
        _ => (cleaned, None),
    };
    let path_parts = name.split('/').collect::<Vec<_>>();
    if version.is_none() && path_parts.len() >= 3 && looks_like_version(path_parts[path_parts.len() - 1]) {
        version = Some(path_parts[path_parts.len() - 1].to_string());
        name = &name[..name.rfind('/').expect("path has slash")];
    }
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

pub(crate) fn parse_library_scope(input: &str) -> Result<LibrarySpec> {
    parse_library_spec(input.trim_start_matches('/'))
}

pub(crate) fn resolve_registry_source(
    project_root: &Path,
    spec: &mut LibrarySpec,
) -> Result<RegistrySource> {
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
                    .map(|version| version_matches(&entry.version, version))
                    .unwrap_or(true)
        })
        .collect::<Vec<_>>();
    matches.sort_by(|a, b| compare_versions(&a.version, &b.version));
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
        let candidate = LibrarySpec {
            vendor: spec.vendor.clone(),
            library: spec.library.clone(),
            version: Some(version_hint),
        };
        if let Some(entry) = best_catalog_entry(catalog, &candidate) {
            spec.version = Some(entry.version.clone());
            return;
        }
    }
}

pub(crate) fn lockfile_version_hint(project_root: &Path, spec: &LibrarySpec) -> Option<String> {
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

    if let Some(version) = spec.version.clone() {
        let exact = library_root.join(&version);
        if exact.exists() {
            return Ok(exact);
        }
        let mut matches = fs::read_dir(&library_root)?
            .filter_map(|entry| entry.ok())
            .filter(|entry| entry.file_type().map(|kind| kind.is_dir()).unwrap_or(false))
            .map(|entry| entry.file_name().to_string_lossy().to_string())
            .filter(|candidate| version_matches(candidate, &version))
            .collect::<Vec<_>>();
        matches.sort_by(|a, b| compare_versions(a, b));
        if let Some(resolved) = matches.pop() {
            spec.version = Some(resolved.clone());
            return Ok(library_root.join(resolved));
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
    versions.sort_by(|a, b| compare_versions(a, b));
    let version = versions
        .pop()
        .with_context(|| format!("no versions found under {}", library_root.display()))?;
    spec.version = Some(version.clone());
    Ok(library_root.join(version))
}

pub(crate) fn best_registry_match(
    project_root: &Path,
    terms: &[String],
    scope: &Option<LibrarySpec>,
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
            .map(|scope| {
                vendor == scope.vendor
                    && library == scope.library
                    && scope
                        .version
                        .as_ref()
                        .map(|requested| version_matches(&version, requested))
                        .unwrap_or(true)
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

pub(crate) fn compare_versions(left: &str, right: &str) -> std::cmp::Ordering {
    version_sort_key(left).cmp(&version_sort_key(right))
}

pub(crate) fn version_matches(candidate: &str, requested: &str) -> bool {
    let candidate_norm = normalize_version(candidate);
    let requested_norm = normalize_version(requested);
    if candidate_norm == requested_norm {
        return true;
    }
    let candidate_parts = numeric_parts(&candidate_norm);
    let requested_parts = numeric_parts(&requested_norm);
    if candidate_parts.is_empty() || requested_parts.is_empty() || requested_parts.len() > candidate_parts.len() {
        return false;
    }
    candidate_parts[..requested_parts.len()] == requested_parts[..]
}

fn version_sort_key(version: &str) -> (u8, [u64; 4], String) {
    let normalized = normalize_version(version);
    let parts = numeric_parts(&normalized);
    if parts.is_empty() {
        let rank = if matches!(normalized.as_str(), "latest" | "stable" | "current" | "default") {
            1
        } else {
            0
        };
        return (rank, [0, 0, 0, 0], normalized);
    }
    let mut padded = [0, 0, 0, 0];
    for (index, value) in parts.into_iter().take(4).enumerate() {
        padded[index] = value;
    }
    (2, padded, normalized)
}

fn normalize_version(version: &str) -> String {
    version.trim().trim_start_matches('v').trim_start_matches('V').to_ascii_lowercase()
}

fn looks_like_version(value: &str) -> bool {
    let normalized = normalize_version(value);
    matches!(normalized.as_str(), "latest" | "stable" | "current" | "default")
        || numeric_parts(&normalized).len() >= 2
        || value.starts_with('v')
        || value.starts_with('V')
}

fn numeric_parts(version: &str) -> Vec<u64> {
    let core = version
        .split(|ch| ch == '-' || ch == '+')
        .next()
        .unwrap_or(version);
    let mut parts = Vec::new();
    for part in core.split('.') {
        if part.is_empty() || !part.chars().all(|ch| ch.is_ascii_digit()) {
            return Vec::new();
        }
        match part.parse::<u64>() {
            Ok(value) => parts.push(value),
            Err(_) => return Vec::new(),
        }
    }
    parts
}

fn fixture_identity(fixtures_root: &Path, file_path: &Path) -> Option<(String, String, String)> {
    let relative = file_path.strip_prefix(fixtures_root).ok()?;
    let mut components = relative.components();
    let vendor = components.next()?.as_os_str().to_string_lossy().to_string();
    let library = components.next()?.as_os_str().to_string_lossy().to_string();
    let version = components.next()?.as_os_str().to_string_lossy().to_string();
    Some((vendor, library, version))
}

pub(crate) fn fixtures_root(project_root: &Path) -> Option<PathBuf> {
    repo_root(project_root).map(|root| root.join(FIXTURES_DIR))
}

pub(crate) fn packs_root(project_root: &Path) -> Option<PathBuf> {
    repo_root(project_root).map(|root| root.join(PACKS_DIR))
}

pub(crate) fn catalog_path(project_root: &Path) -> Option<PathBuf> {
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

pub(crate) fn load_or_build_catalog(project_root: &Path) -> Result<RegistryCatalog> {
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

pub(crate) fn build_catalog(project_root: &Path) -> Result<RegistryCatalog> {
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
        (&a.vendor, &a.library)
            .cmp(&(&b.vendor, &b.library))
            .then_with(|| compare_versions(&a.version, &b.version))
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

pub(crate) fn write_catalog(project_root: &Path, catalog: &RegistryCatalog) -> Result<()> {
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

pub(crate) fn build_packs(project_root: &Path) -> Result<()> {
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
        ensure_fixture_quality_passed(entry.path()).with_context(|| {
            format!(
                "fixture {} did not pass quality gates",
                entry.path().display()
            )
        })?;
        let destination = packs
            .join(&vendor)
            .join(&library)
            .join(format!("{version}.ozpack"));
        write_pack(entry.path(), &destination, &vendor, &library, &version)?;
    }
    Ok(())
}

fn ensure_fixture_quality_passed(fixture: &Path) -> Result<()> {
    let quality_path = fixture.join("_quality.json");
    if !quality_path.exists() {
        return Ok(());
    }
    let quality = serde_json::from_str::<serde_json::Value>(&fs::read_to_string(&quality_path)?)
        .with_context(|| format!("failed to parse {}", quality_path.display()))?;
    if quality
        .get("passed")
        .and_then(|value| value.as_bool())
        .unwrap_or(false)
    {
        return Ok(());
    }
    let errors = quality
        .get("errors")
        .and_then(|value| value.as_array())
        .map(|values| {
            values
                .iter()
                .filter_map(|value| value.as_str())
                .collect::<Vec<_>>()
                .join("; ")
        })
        .unwrap_or_else(|| "unknown quality failure".to_string());
    bail!("{}", errors)
}

pub(crate) fn latest_version(
    project_root: &Path,
    vendor: &str,
    library: &str,
) -> Result<Option<String>> {
    let catalog = load_or_build_catalog(project_root)?;
    let mut versions = catalog
        .libraries
        .into_iter()
        .filter(|entry| entry.vendor == vendor && entry.library == library)
        .map(|entry| entry.version)
        .collect::<Vec<_>>();
    versions.sort_by(|a, b| compare_versions(a, b));
    Ok(versions.pop())
}

pub(crate) fn latest_version_for(
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

pub(crate) fn record_index_request(
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
