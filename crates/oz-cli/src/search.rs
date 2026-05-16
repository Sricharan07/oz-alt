use super::*;

pub(crate) fn search_docs(
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
            "installed_libraries": installed_libraries_payload(&lock),
            "library_scope": library_scope,
            "max_results": 20,
        }),
    )?;

    for library in &response.libraries_to_pull {
        let spec = format!("{}/{}@{}", library.vendor, library.library, library.version);
        pull_library_impl(project_root, &spec, true)?;
    }

    warn_stale_response(&response.stale_libraries);
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
