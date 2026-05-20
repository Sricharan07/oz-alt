use super::*;

pub(crate) fn local_search_response(
    project_root: &Path,
    terms: &[String],
    library_scope: Option<&str>,
    max_results: usize,
    content_type: Option<&str>,
) -> Result<SearchResponse> {
    let scope = library_scope.map(parse_library_scope).transpose()?;
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
    let mut seen_paths = HashSet::new();
    let results = hits
        .into_iter()
        .filter(|hit| content_type_matches(&hit.content_type, content_type))
        .filter(|hit| seen_paths.insert(hit.path.clone()))
        .take(clamp_max_results(max_results, 1, 50))
        .map(|hit| {
            let (library, version) = library_from_path(project_root, &hit.path);
            SearchResult {
                path: to_project_path(project_root, &hit.path),
                line: Some(hit.line),
                end_line: hit.end_line,
                score: serde_json::json!(hit.score),
                library,
                version,
                vendor: None,
                matched_path: None,
                source_anchor: None,
                content_type: Some(hit.content_type),
                heading_path: Vec::new(),
                symbols: Vec::new(),
                token_count: None,
                retrieval_mode: Some("local_grep".to_string()),
                degraded: false,
            }
        })
        .collect();
    Ok(SearchResponse {
        results,
        libraries_to_pull: Vec::new(),
        stale_libraries: Vec::new(),
        retrieval_mode: Some("local_grep".to_string()),
        degraded: false,
    })
}

fn library_from_path(project_root: &Path, path: &Path) -> (String, String) {
    let relative = path
        .strip_prefix(project_root.join(VENDORS_DIR))
        .unwrap_or(path);
    let parts = relative
        .components()
        .map(|part| part.as_os_str().to_string_lossy().to_string())
        .collect::<Vec<_>>();
    if parts.len() >= 2 {
        if let Some((library, version)) = parts[1].rsplit_once('@') {
            return (format!("{}/{}", parts[0], library), version.to_string());
        }
    }
    (String::new(), String::new())
}

fn search_vendor_tree(
    project_root: &Path,
    root: &Path,
    terms: &[String],
    scope: &Option<LibrarySpec>,
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
            end_line: row
                .get("end_line")
                .and_then(|value| value.as_u64())
                .map(|value| value as usize)
                .filter(|end_line| *end_line >= line),
            score,
            content_type: row
                .get("content_type")
                .and_then(|value| value.as_str())
                .unwrap_or("guide")
                .to_string(),
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
            end_line: Some(content.lines().count().max(1)),
            score,
            content_type: "api_reference".to_string(),
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

fn path_matches_scope(path: &Path, scope: &Option<LibrarySpec>) -> bool {
    let Some(scope) = scope else {
        return true;
    };

    let components = path
        .components()
        .map(|component| component.as_os_str().to_string_lossy().to_string())
        .collect::<Vec<_>>();

    components.windows(2).any(|window| {
        if window[0] != scope.vendor {
            return false;
        }
        let prefix = format!("{}@", scope.library);
        if !window[1].starts_with(&prefix) {
            return false;
        }
        scope
            .version
            .as_ref()
            .map(|requested| version_matches(window[1].trim_start_matches(&prefix), requested))
            .unwrap_or(true)
    })
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
                end_line: Some(idx + 1),
                score,
                content_type: "guide".to_string(),
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
    let compact_query = compact(&terms.join(" "));

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

    let total_distinct_hits = terms
        .iter()
        .filter(|term| {
            text.contains(term.as_str())
                || path.contains(term.as_str())
                || headings.contains(term.as_str())
                || symbols.contains(term.as_str())
                || compact_path.contains(&compact(term))
                || compact_symbols.contains(&compact(term))
        })
        .count();
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
    let pair_bonus = adjacent_pair_bonus(terms, &text, &path, &headings, &symbols);
    let practical_task_bonus = practical_task_bonus(terms, &path, &text, &content_type);
    let source_priority_bonus = source_priority_bonus(row);
    let exact_symbol_query = !symbols.is_empty()
        && !compact_query.is_empty()
        && (compact_symbols == compact_query || compact_symbols.contains(&compact_query));
    let generated_penalty =
        generated_artifact_penalty(terms, &path, &symbols, row, exact_symbol_query);
    let specific_query = terms.len() >= 3;
    let overview_penalty = if specific_query && shallow_overview_path(&path) {
        28
    } else {
        0
    };
    let low_coverage_penalty = if specific_query && total_distinct_hits <= 1 && !exact_symbol_query
    {
        80
    } else if specific_query && total_distinct_hits <= 2 && generated_penalty > 0 {
        35
    } else {
        0
    };
    let score = (text_hits.min(80))
        + (distinct_text_hits * 18)
        + coverage_bonus
        + (path_hits * 25)
        + (heading_hits * 16)
        + (symbol_hits * 70)
        + type_bonus
        + pair_bonus
        + practical_task_bonus
        + source_priority_bonus;
    score.saturating_sub(path_penalty + overview_penalty + low_coverage_penalty + generated_penalty)
}

fn adjacent_pair_bonus(
    terms: &[String],
    text: &str,
    path: &str,
    headings: &str,
    symbols: &str,
) -> usize {
    let mut bonus = 0;
    for pair in terms.windows(2) {
        let phrase = format!("{} {}", pair[0], pair[1]);
        let compact_phrase = compact(&phrase);
        if text.contains(&phrase) || headings.contains(&phrase) {
            bonus += 28;
        }
        if path.contains(&phrase) || compact(path).contains(&compact_phrase) {
            bonus += 36;
        }
        if symbols.contains(&phrase) || compact(symbols).contains(&compact_phrase) {
            bonus += 32;
        }
    }
    bonus.min(140)
}

fn practical_task_bonus(terms: &[String], path: &str, text: &str, content_type: &str) -> usize {
    let tasky = has_any(
        terms,
        &[
            "install",
            "initialize",
            "configure",
            "environment",
            "example",
            "build",
            "create",
            "stream",
            "websocket",
            "audio",
            "fastapi",
            "tool",
            "python",
            "save",
        ],
    );
    if !tasky {
        return 0;
    }
    let mut bonus = 0;
    if content_type == "code_example" {
        bonus += 30;
    }
    if path.contains("readme") || path.contains("/examples/") || path.contains("-examples-") {
        bonus += 55;
    }
    if path.contains("quickstart")
        || path.contains("get-started")
        || path.contains("getting-started")
    {
        bonus += 45;
    }
    if has_all(terms, &["api", "key"])
        && (text.contains("api key") || text.contains("smallest_api_key"))
    {
        bonus += 70;
    }
    if has_all(terms, &["environment"])
        && (text.contains("environment variable") || text.contains("env var"))
    {
        bonus += 55;
    }
    if has_all(terms, &["websocket", "audio"])
        && text.contains("websocket")
        && text.contains("audio")
    {
        bonus += 65;
    }
    if has_all(terms, &["fastapi"]) && text.contains("fastapi") {
        bonus += 70;
    }
    bonus
}

fn source_priority_bonus(row: &serde_json::Value) -> usize {
    row.get("source_priority")
        .and_then(|value| value.as_u64())
        .map(|priority| 30usize.saturating_sub(priority as usize).min(24))
        .unwrap_or(0)
}

fn generated_artifact_penalty(
    terms: &[String],
    path: &str,
    symbols: &str,
    row: &serde_json::Value,
    exact_symbol_query: bool,
) -> usize {
    if exact_symbol_query || has_any(terms, &["response", "request", "model", "schema", "class"]) {
        return 0;
    }
    let metadata = row.get("metadata_json").and_then(|value| value.as_object());
    let source_type = metadata
        .and_then(|metadata| {
            metadata
                .get("source_type")
                .or_else(|| metadata.get("source_kind"))
        })
        .and_then(|value| value.as_str())
        .unwrap_or("");
    let compact_symbols = compact(symbols);
    let generated_name = compact_symbols.contains("response")
        || compact_symbols.contains("request")
        || compact_symbols.contains("dto")
        || compact_symbols.contains("schema")
        || compact_symbols.contains("apiresponse");
    let generated_path = path.contains("/models/")
        || path.contains("_symbols/")
        || path.contains("api-reference/source/")
        || path.contains("response")
        || path.contains("request");
    if source_type == "source_code" && generated_name {
        return 110;
    }
    if generated_path && generated_name {
        return 90;
    }
    0
}

fn has_any(terms: &[String], needles: &[&str]) -> bool {
    needles
        .iter()
        .any(|needle| terms.iter().any(|term| term == needle))
}

fn has_all(terms: &[String], needles: &[&str]) -> bool {
    needles
        .iter()
        .all(|needle| terms.iter().any(|term| term == needle))
}

fn shallow_overview_path(path: &str) -> bool {
    let segments = path.split('/').filter(|part| !part.is_empty()).count();
    (path.starts_with("guides/") || path.starts_with("api-reference/")) && segments <= 2
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
