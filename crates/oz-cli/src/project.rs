use super::*;

pub(crate) fn init_project(project_root: &Path) -> Result<()> {
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

pub(crate) fn global_objects_root() -> Result<PathBuf> {
    let home = dirs::home_dir().context("failed to locate home directory")?;
    Ok(home.join(".codo").join("objects"))
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
