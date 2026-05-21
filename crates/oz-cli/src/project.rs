use super::*;

pub(crate) fn init_project(project_root: &Path) -> Result<()> {
    fs::create_dir_all(project_root.join(VENDORS_DIR)).with_context(|| {
        format!(
            "failed to create {}",
            project_root.join(VENDORS_DIR).display()
        )
    })?;
    ensure_global_objects_root()?;

    let existing = read_lock(project_root).unwrap_or_default();
    let (mut dependencies, mut workspaces) = detect_project_dependencies(project_root)?;
    dependencies.sort_by(|a, b| {
        (&a.ecosystem, &a.name, &a.requirement).cmp(&(&b.ecosystem, &b.name, &b.requirement))
    });
    dependencies.dedup_by(|left, right| {
        left.ecosystem == right.ecosystem
            && left.name == right.name
            && left.requirement == right.requirement
    });
    workspaces.sort_by(|a, b| a.path.cmp(&b.path));

    let lock = ProjectLock {
        schema_version: 1,
        generated_at: Utc::now().to_rfc3339(),
        project_fingerprint: fingerprint_dependencies(&dependencies)?,
        workspaces,
        dependencies,
        pulls: existing.pulls,
    };

    write_lock(project_root, &lock)?;
    update_gitignore(project_root)?;

    eprintln!(
        "initialized Oz project metadata at {}",
        project_root.join(LOCK_FILE).display()
    );
    Ok(())
}

pub(crate) fn gc(project_root: &Path) -> Result<()> {
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

pub(crate) fn prune_libraries(
    project_root: &Path,
    scope: Option<&str>,
    all: bool,
    stale: bool,
) -> Result<()> {
    let selector_count = usize::from(scope.is_some()) + usize::from(all) + usize::from(stale);
    if selector_count == 0 {
        bail!("specify a library, --stale, or --all");
    }
    if selector_count > 1 {
        bail!("use only one prune selector: library, --stale, or --all");
    }

    let parsed_scope = scope.map(parse_library_scope).transpose()?;
    let config = read_config().unwrap_or_default();
    let mut lock = read_lock(project_root)?;
    let original_pulls = lock.pulls.clone();
    let mut kept = Vec::new();
    let mut pruned = Vec::new();

    for pull in original_pulls {
        let matches_scope = parsed_scope
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
            .unwrap_or(false);
        let matches_stale = if stale {
            latest_version_for(project_root, &config, &pull.vendor, &pull.library)?
                .map(|latest| latest != pull.version)
                .unwrap_or(false)
        } else {
            false
        };
        let should_prune = all || matches_scope || matches_stale;
        if should_prune {
            remove_pull_tree(project_root, &pull)?;
            pruned.push(pull);
        } else {
            kept.push(pull);
        }
    }

    if pruned.is_empty() {
        bail!("no pulled libraries matched prune selector");
    }

    lock.pulls = kept;
    lock.generated_at = Utc::now().to_rfc3339();
    write_lock(project_root, &lock)?;
    gc(project_root)?;

    for pull in &pruned {
        println!("pruned {}/{}@{}", pull.vendor, pull.library, pull.version);
    }
    emit_telemetry(
        &config,
        "prune_run",
        serde_json::json!({
            "count": pruned.len(),
            "scope": scope,
            "all": all,
            "stale": stale,
        }),
    );
    Ok(())
}

fn remove_pull_tree(project_root: &Path, pull: &PulledLibrary) -> Result<()> {
    let path = project_root.join(&pull.path);
    let vendors_root = project_root.join(VENDORS_DIR);
    if !path.starts_with(&vendors_root) {
        bail!("refusing to prune non-vendor path {}", path.display());
    }
    if path.exists() {
        fs::remove_dir_all(&path)
            .with_context(|| format!("failed to remove {}", path.display()))?;
    }
    if let Some(parent) = path.parent() {
        if parent != vendors_root && parent.exists() && fs::read_dir(parent)?.next().is_none() {
            fs::remove_dir(parent)
                .with_context(|| format!("failed to remove {}", parent.display()))?;
        }
    }
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

pub(crate) fn ensure_project(project_root: &Path) -> Result<()> {
    if project_root.join(LOCK_FILE).exists() {
        return Ok(());
    }

    init_project(project_root)
}

pub(crate) fn read_lock(project_root: &Path) -> Result<ProjectLock> {
    let path = project_root.join(LOCK_FILE);
    let content =
        fs::read_to_string(&path).with_context(|| format!("failed to read {}", path.display()))?;
    serde_json::from_str(&content).with_context(|| format!("failed to parse {}", path.display()))
}

pub(crate) fn write_lock(project_root: &Path, lock: &ProjectLock) -> Result<()> {
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

fn detect_project_dependencies(
    project_root: &Path,
) -> Result<(Vec<Dependency>, Vec<WorkspaceDependencies>)> {
    let roots = workspace_roots(project_root)?;
    let mut all_dependencies = Vec::new();
    let mut workspaces = Vec::new();
    for root in roots {
        let mut dependencies = Vec::new();
        read_package_json(&root, &mut dependencies)?;
        read_requirements(&root, &mut dependencies)?;
        read_go_mod(&root, &mut dependencies)?;
        read_cargo_toml(&root, &mut dependencies)?;
        dependencies.sort_by(|a, b| {
            (&a.ecosystem, &a.name, &a.requirement).cmp(&(&b.ecosystem, &b.name, &b.requirement))
        });
        dependencies.dedup();
        if !dependencies.is_empty() {
            all_dependencies.extend(dependencies.clone());
        }
        workspaces.push(WorkspaceDependencies {
            path: workspace_path(project_root, &root),
            dependencies,
        });
    }
    Ok((all_dependencies, workspaces))
}

fn workspace_roots(project_root: &Path) -> Result<Vec<PathBuf>> {
    let mut roots = BTreeSet::new();
    roots.insert(project_root.to_path_buf());
    for pattern in package_json_workspace_patterns(project_root)? {
        roots.extend(expand_workspace_pattern(project_root, &pattern)?);
    }
    for pattern in pnpm_workspace_patterns(project_root)? {
        roots.extend(expand_workspace_pattern(project_root, &pattern)?);
    }
    for pattern in cargo_workspace_patterns(project_root)? {
        roots.extend(expand_workspace_pattern(project_root, &pattern)?);
    }
    for root in go_work_roots(project_root)? {
        roots.insert(root);
    }
    Ok(roots
        .into_iter()
        .filter(|path| !is_ignored_workspace_path(project_root, path))
        .collect())
}

fn package_json_workspace_patterns(project_root: &Path) -> Result<Vec<String>> {
    let path = project_root.join("package.json");
    if !path.exists() {
        return Ok(Vec::new());
    }
    let value: serde_json::Value = serde_json::from_str(&fs::read_to_string(&path)?)
        .with_context(|| format!("failed to parse {}", path.display()))?;
    let mut patterns = Vec::new();
    match value.get("workspaces") {
        Some(serde_json::Value::Array(items)) => {
            patterns.extend(
                items
                    .iter()
                    .filter_map(|item| item.as_str().map(ToString::to_string)),
            );
        }
        Some(serde_json::Value::Object(map)) => {
            if let Some(serde_json::Value::Array(items)) = map.get("packages") {
                patterns.extend(
                    items
                        .iter()
                        .filter_map(|item| item.as_str().map(ToString::to_string)),
                );
            }
        }
        _ => {}
    }
    Ok(patterns)
}

fn pnpm_workspace_patterns(project_root: &Path) -> Result<Vec<String>> {
    let path = project_root.join("pnpm-workspace.yaml");
    if !path.exists() {
        return Ok(Vec::new());
    }
    let mut patterns = Vec::new();
    let mut in_packages = false;
    for raw in fs::read_to_string(&path)?.lines() {
        let line = raw.trim();
        if line.starts_with("packages:") {
            in_packages = true;
            continue;
        }
        if in_packages && line.starts_with('-') {
            let value = line
                .trim_start_matches('-')
                .trim()
                .trim_matches('"')
                .trim_matches('\'');
            if !value.is_empty() && !value.starts_with('!') {
                patterns.push(value.to_string());
            }
            continue;
        }
        if in_packages && !line.is_empty() && !line.starts_with('#') {
            in_packages = false;
        }
    }
    Ok(patterns)
}

fn cargo_workspace_patterns(project_root: &Path) -> Result<Vec<String>> {
    let path = project_root.join("Cargo.toml");
    if !path.exists() {
        return Ok(Vec::new());
    }
    let content = fs::read_to_string(&path)?;
    if !content.contains("[workspace]") {
        return Ok(Vec::new());
    }
    let mut patterns = Vec::new();
    let mut in_workspace = false;
    let mut collecting_members = false;
    for raw in content.lines() {
        let line = raw.trim();
        if line.starts_with('[') {
            in_workspace = line == "[workspace]";
            collecting_members = false;
            continue;
        }
        if !in_workspace {
            continue;
        }
        if let Some(rest) = line.strip_prefix("members") {
            if let Some((_, value)) = rest.split_once('=') {
                patterns.extend(quoted_values(value));
                collecting_members = value.contains('[') && !value.contains(']');
            }
            continue;
        }
        if collecting_members {
            patterns.extend(quoted_values(line));
            if line.contains(']') {
                collecting_members = false;
            }
        }
    }
    Ok(patterns)
}

fn go_work_roots(project_root: &Path) -> Result<Vec<PathBuf>> {
    let path = project_root.join("go.work");
    if !path.exists() {
        return Ok(Vec::new());
    }
    let mut roots = Vec::new();
    let mut in_use_block = false;
    for raw in fs::read_to_string(&path)?.lines() {
        let line = raw.trim();
        if line == "use (" {
            in_use_block = true;
            continue;
        }
        if in_use_block && line == ")" {
            in_use_block = false;
            continue;
        }
        let candidate = if let Some(rest) = line.strip_prefix("use ") {
            rest.trim()
        } else if in_use_block {
            line
        } else {
            ""
        };
        let candidate = candidate.trim_matches('"');
        if candidate.starts_with('.') {
            let root = normalized_workspace_root(project_root, candidate);
            if root.exists() {
                roots.push(root);
            }
        }
    }
    Ok(roots)
}

fn expand_workspace_pattern(project_root: &Path, pattern: &str) -> Result<Vec<PathBuf>> {
    let cleaned = pattern
        .trim()
        .trim_matches('"')
        .trim_matches('\'')
        .trim_end_matches('/');
    if cleaned.is_empty() || cleaned.starts_with('!') {
        return Ok(Vec::new());
    }
    if !cleaned.contains('*') {
        let root = normalized_workspace_root(project_root, cleaned);
        return Ok(root.exists().then_some(root).into_iter().collect());
    }

    let wildcard = cleaned.find('*').unwrap_or(cleaned.len());
    let base_pattern = cleaned[..wildcard].trim_end_matches('/');
    let base = normalized_workspace_root(project_root, base_pattern);
    if !base.exists() {
        return Ok(Vec::new());
    }

    let recursive = cleaned.contains("**");
    let mut roots = Vec::new();
    if recursive {
        for entry in WalkDir::new(&base)
            .min_depth(1)
            .max_depth(5)
            .into_iter()
            .filter_map(|entry| entry.ok())
            .filter(|entry| entry.file_type().is_dir())
        {
            let path = entry.path();
            if has_dependency_manifest(path) {
                roots.push(path.to_path_buf());
            }
        }
    } else {
        for entry in
            fs::read_dir(&base).with_context(|| format!("failed to read {}", base.display()))?
        {
            let entry = entry?;
            if entry.file_type().map(|kind| kind.is_dir()).unwrap_or(false)
                && has_dependency_manifest(&entry.path())
            {
                roots.push(entry.path());
            }
        }
    }
    Ok(roots)
}

fn quoted_values(value: &str) -> Vec<String> {
    value
        .split(',')
        .filter_map(|part| {
            let cleaned = part
                .trim()
                .trim_start_matches('[')
                .trim_end_matches(']')
                .trim()
                .trim_matches('"')
                .trim_matches('\'');
            (!cleaned.is_empty()).then_some(cleaned.to_string())
        })
        .collect()
}

fn normalized_workspace_root(project_root: &Path, value: &str) -> PathBuf {
    let raw = Path::new(value);
    if raw.is_absolute() {
        raw.to_path_buf()
    } else {
        project_root.join(raw)
    }
}

fn has_dependency_manifest(path: &Path) -> bool {
    ["package.json", "requirements.txt", "go.mod", "Cargo.toml"]
        .iter()
        .any(|name| path.join(name).exists())
}

fn is_ignored_workspace_path(project_root: &Path, path: &Path) -> bool {
    let relative = path.strip_prefix(project_root).unwrap_or(path);
    relative.components().any(|component| {
        matches!(
            component.as_os_str().to_string_lossy().as_ref(),
            "node_modules" | ".git" | ".codo" | "target"
        )
    })
}

fn workspace_path(project_root: &Path, path: &Path) -> String {
    if path == project_root {
        return ".".to_string();
    }
    to_project_path(project_root, path)
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

pub(crate) fn global_objects_root() -> Result<PathBuf> {
    let home = dirs::home_dir().context("failed to locate home directory")?;
    Ok(home.join(".codo").join("objects"))
}

pub(crate) fn ensure_global_objects_root() -> Result<PathBuf> {
    let root = global_objects_root()?;
    fs::create_dir_all(&root).with_context(|| format!("failed to create {}", root.display()))?;
    Ok(root)
}

pub(crate) fn upsert_pull(lock: &mut ProjectLock, pull: PulledLibrary) {
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

#[cfg(test)]
mod tests {
    use super::*;

    fn temp_project(name: &str) -> PathBuf {
        let root = std::env::temp_dir().join(format!(
            "oz-cli-{name}-{}-{}",
            std::process::id(),
            Utc::now().timestamp_nanos_opt().unwrap_or_default()
        ));
        fs::create_dir_all(&root).unwrap();
        root
    }

    #[test]
    fn detects_package_json_workspaces() {
        let root = temp_project("npm-workspaces");
        fs::write(
            root.join("package.json"),
            r#"{"workspaces":["apps/*"],"dependencies":{"react":"^19.0.0"}}"#,
        )
        .unwrap();
        fs::create_dir_all(root.join("apps/web")).unwrap();
        fs::write(
            root.join("apps/web/package.json"),
            r#"{"dependencies":{"next":"^15.0.0"}}"#,
        )
        .unwrap();

        let (dependencies, workspaces) = detect_project_dependencies(&root).unwrap();
        assert!(dependencies.iter().any(|item| item.name == "react"));
        assert!(dependencies.iter().any(|item| item.name == "next"));
        assert!(workspaces.iter().any(|item| item.path == "."));
        assert!(workspaces.iter().any(|item| item.path == "apps/web"));

        fs::remove_dir_all(root).ok();
    }

    #[test]
    fn detects_pnpm_workspace_patterns() {
        let root = temp_project("pnpm-workspaces");
        fs::write(
            root.join("pnpm-workspace.yaml"),
            "packages:\n  - 'packages/*'\n",
        )
        .unwrap();
        fs::create_dir_all(root.join("packages/api")).unwrap();
        fs::write(
            root.join("packages/api/package.json"),
            r#"{"dependencies":{"@hiringbae/oz":"^0.1.0"}}"#,
        )
        .unwrap();

        let (dependencies, workspaces) = detect_project_dependencies(&root).unwrap();
        assert!(dependencies.iter().any(|item| item.name == "@hiringbae/oz"));
        assert!(workspaces.iter().any(|item| item.path == "packages/api"));

        fs::remove_dir_all(root).ok();
    }
}
