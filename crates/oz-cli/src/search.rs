use super::*;
use std::sync::OnceLock;

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

    let mut seen_paths = HashSet::new();
    let output = hits
        .into_iter()
        .filter(|hit| seen_paths.insert(hit.path.clone()))
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

pub(crate) fn context_docs(
    project_root: &Path,
    query: &str,
    library_scope: Option<&str>,
    max_tokens: usize,
    json: bool,
) -> Result<()> {
    ensure_project(project_root)?;
    let terms = normalize_query(query);
    if terms.is_empty() {
        bail!("context query must contain at least one alphanumeric term");
    }
    let config = read_config()?;
    let hits = if configured_api_url(&config).is_some() {
        remote_context_hits(project_root, &config, query, library_scope)?
    } else {
        local_context_hits(project_root, &terms, library_scope)?
    };
    let snippets = context_snippets(project_root, &hits, max_tokens)?;
    if json {
        println!(
            "{}",
            serde_json::to_string_pretty(&serde_json::json!({ "results": snippets }))?
        );
    } else {
        for snippet in &snippets {
            println!(
                "{}:{}\n{}\n",
                snippet["path"].as_str().unwrap_or_default(),
                snippet["line"].as_u64().unwrap_or_default(),
                snippet["snippet"].as_str().unwrap_or_default()
            );
        }
    }
    emit_telemetry(
        &config,
        "context_query",
        serde_json::json!({
            "query_length": query.len(),
            "result_count": snippets.len(),
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

fn remote_context_hits(
    project_root: &Path,
    config: &OzConfig,
    query: &str,
    library_scope: Option<&str>,
) -> Result<Vec<(String, usize)>> {
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
    Ok(response
        .results
        .into_iter()
        .map(|row| (row.path, row.line.unwrap_or(1)))
        .collect())
}

fn local_context_hits(
    project_root: &Path,
    terms: &[String],
    library_scope: Option<&str>,
) -> Result<Vec<(String, usize)>> {
    let scope = library_scope.map(parse_scope).transpose()?;
    let mut hits =
        search_vendor_tree(project_root, &project_root.join(VENDORS_DIR), terms, &scope)?;
    if hits.is_empty() {
        if let Some(spec) = best_registry_match(project_root, terms, &scope)? {
            pull_library_impl(project_root, &spec, true)?;
            hits =
                search_vendor_tree(project_root, &project_root.join(VENDORS_DIR), terms, &scope)?;
        }
    }
    hits.sort_by(|a, b| {
        b.score
            .cmp(&a.score)
            .then_with(|| a.path.cmp(&b.path))
            .then(a.line.cmp(&b.line))
    });
    let mut seen = HashSet::new();
    Ok(hits
        .into_iter()
        .filter(|hit| seen.insert(hit.path.clone()))
        .take(20)
        .map(|hit| (to_project_path(project_root, &hit.path), hit.line))
        .collect())
}

fn context_snippets(
    project_root: &Path,
    hits: &[(String, usize)],
    max_tokens: usize,
) -> Result<Vec<serde_json::Value>> {
    let mut remaining = max_tokens.max(1);
    let mut output = Vec::new();
    for (path, line) in hits {
        if remaining == 0 {
            break;
        }
        let file_path = project_root.join(path);
        if !file_path.exists() {
            continue;
        }
        let snippet = snippet_at_line(&file_path, *line, remaining)?;
        let tokens = approximate_tokens(&snippet);
        if tokens == 0 {
            continue;
        }
        remaining = remaining.saturating_sub(tokens);
        output.push(serde_json::json!({
            "path": path,
            "line": line,
            "token_count": tokens,
            "snippet": snippet,
        }));
    }
    Ok(output)
}

fn snippet_at_line(path: &Path, line: usize, max_tokens: usize) -> Result<String> {
    let content =
        fs::read_to_string(path).with_context(|| format!("failed to read {}", path.display()))?;
    let lines = content.lines().collect::<Vec<_>>();
    if lines.is_empty() {
        return Ok(String::new());
    }
    let center = line.saturating_sub(1).min(lines.len() - 1);
    let start = center.saturating_sub(8);
    let mut selected = Vec::new();
    let mut tokens = 0;
    for item in lines.iter().skip(start) {
        let line_tokens = approximate_tokens(item);
        if tokens > 0 && tokens + line_tokens > max_tokens.min(420) {
            break;
        }
        selected.push(*item);
        tokens += line_tokens;
    }
    Ok(selected.join("\n").trim().to_string())
}

fn approximate_tokens(text: &str) -> usize {
    static ENCODING: OnceLock<tiktoken_rs::CoreBPE> = OnceLock::new();
    let encoding = ENCODING.get_or_init(|| {
        tiktoken_rs::cl100k_base().expect("cl100k_base tokenizer must be available")
    });
    encoding.encode_with_special_tokens(text).len().max(1)
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

    let chunk_indexes = WalkDir::new(root)
        .sort_by_file_name()
        .into_iter()
        .filter_map(|entry| entry.ok())
        .filter(|entry| entry.file_type().is_file() && entry.file_name() == "_chunks.jsonl")
        .map(|entry| entry.path().to_path_buf())
        .collect::<Vec<_>>();
    let chunked_roots = chunk_indexes
        .iter()
        .filter_map(|path| path.parent().map(Path::to_path_buf))
        .collect::<Vec<_>>();

    for chunk_index in &chunk_indexes {
        if path_matches_scope(chunk_index, scope) {
            collect_chunk_hits(chunk_index, terms, &mut hits)?;
            if let Some(library_root) = chunk_index.parent() {
                collect_symbol_hits(library_root, terms, &mut hits)?;
            }
        }
    }

    for entry in WalkDir::new(root).sort_by_file_name() {
        let entry = entry.with_context(|| format!("failed walking {}", root.display()))?;
        if !entry.file_type().is_file()
            || entry.path().extension().and_then(|s| s.to_str()) != Some("md")
        {
            continue;
        }
        if chunked_roots
            .iter()
            .any(|root| entry.path().starts_with(root))
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

fn collect_chunk_hits(path: &Path, terms: &[String], hits: &mut Vec<SearchHit>) -> Result<()> {
    let library_root = path
        .parent()
        .context("_chunks.jsonl should have a parent")?;
    let content =
        fs::read_to_string(path).with_context(|| format!("failed to read {}", path.display()))?;
    for line in content.lines().filter(|line| !line.trim().is_empty()) {
        let row = serde_json::from_str::<serde_json::Value>(line)
            .with_context(|| format!("failed to parse {}", path.display()))?;
        let score = chunk_score(&row, terms);
        if score == 0 {
            continue;
        }
        let relative_path = row
            .get("path")
            .and_then(|value| value.as_str())
            .unwrap_or("README.md");
        let line = row
            .get("start_line")
            .and_then(|value| value.as_u64())
            .unwrap_or(1) as usize;
        hits.push(SearchHit {
            path: library_root.join(relative_path),
            line,
            score,
            preview: row
                .get("text")
                .and_then(|value| value.as_str())
                .unwrap_or_default()
                .lines()
                .next()
                .unwrap_or_default()
                .trim()
                .chars()
                .take(160)
                .collect(),
        });
    }
    Ok(())
}

fn collect_symbol_hits(
    library_root: &Path,
    terms: &[String],
    hits: &mut Vec<SearchHit>,
) -> Result<()> {
    let symbols_dir = library_root.join("_symbols");
    if !symbols_dir.exists() {
        return Ok(());
    }
    for entry in WalkDir::new(&symbols_dir).sort_by_file_name() {
        let entry = entry.with_context(|| format!("failed walking {}", symbols_dir.display()))?;
        if !entry.file_type().is_file()
            || entry.path().extension().and_then(|s| s.to_str()) != Some("md")
        {
            continue;
        }
        let content = fs::read_to_string(entry.path())
            .with_context(|| format!("failed to read {}", entry.path().display()))?;
        let symbol = entry
            .path()
            .file_stem()
            .and_then(|value| value.to_str())
            .unwrap_or_default();
        let relative_path = entry
            .path()
            .strip_prefix(library_root)
            .unwrap_or(entry.path())
            .to_string_lossy()
            .to_string();
        let row = serde_json::json!({
            "path": relative_path,
            "text": content,
            "heading_path": [symbol],
            "symbols": [symbol],
            "content_type": "api_reference",
        });
        let score = chunk_score(&row, terms);
        if score == 0 {
            continue;
        }
        hits.push(SearchHit {
            path: entry.path().to_path_buf(),
            line: 1,
            score,
            preview: content
                .lines()
                .next()
                .unwrap_or_default()
                .trim()
                .chars()
                .take(160)
                .collect(),
        });
    }
    Ok(())
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

fn chunk_score(row: &serde_json::Value, terms: &[String]) -> usize {
    let text = json_string(row, "text").to_ascii_lowercase();
    let path = json_string(row, "path").to_ascii_lowercase();
    let headings = json_string_array(row, "heading_path")
        .join(" ")
        .to_ascii_lowercase();
    let symbols = json_string_array(row, "symbols")
        .join(" ")
        .to_ascii_lowercase();
    let compact_path = compact(&path);
    let compact_symbols = compact(&symbols);

    let text_hits = terms
        .iter()
        .map(|term| text.matches(term.as_str()).count())
        .sum::<usize>();
    let distinct_text_hits = terms
        .iter()
        .filter(|term| text.contains(term.as_str()))
        .count();
    let path_hits = terms
        .iter()
        .filter(|term| path.contains(term.as_str()) || compact_path.contains(&compact(term)))
        .count();
    let heading_hits = terms
        .iter()
        .filter(|term| headings.contains(term.as_str()))
        .count();
    let symbol_hits = terms
        .iter()
        .filter(|term| symbols.contains(term.as_str()) || compact_symbols.contains(&compact(term)))
        .count();
    if text_hits == 0 && path_hits == 0 && heading_hits == 0 && symbol_hits == 0 {
        return 0;
    }

    let coverage_bonus = if terms.is_empty() {
        0
    } else {
        (distinct_text_hits * 40) / terms.len()
    };
    let path_penalty = if path.contains("changelog")
        || path.contains("release-notes")
        || path.contains("releases")
        || path.contains("migration-guide")
    {
        60
    } else {
        0
    };
    let content_type = json_string(row, "content_type");
    let type_bonus = match content_type.as_str() {
        "api_reference" => 5,
        "code_example" => 3,
        "config" => 3,
        "cli" => 3,
        "error_ref" => 2,
        "types" => 4,
        "example" => 2,
        "index" => 0,
        _ => 0,
    };
    let score = (text_hits.min(80))
        + (distinct_text_hits * 18)
        + coverage_bonus
        + (path_hits * 10)
        + (heading_hits * 16)
        + (symbol_hits * 35)
        + type_bonus;
    score.saturating_sub(path_penalty)
}

fn json_string(row: &serde_json::Value, key: &str) -> String {
    row.get(key)
        .and_then(|value| value.as_str())
        .unwrap_or_default()
        .to_string()
}

fn json_string_array(row: &serde_json::Value, key: &str) -> Vec<String> {
    row.get(key)
        .and_then(|value| value.as_array())
        .map(|values| {
            values
                .iter()
                .filter_map(|value| value.as_str().map(ToString::to_string))
                .collect()
        })
        .unwrap_or_default()
}

fn compact(value: &str) -> String {
    value
        .chars()
        .filter(|ch| ch.is_ascii_alphanumeric())
        .flat_map(|ch| ch.to_lowercase())
        .collect()
}
