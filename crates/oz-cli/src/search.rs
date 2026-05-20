use super::*;
use search_local::{context_snippets, local_context_hits, local_search_response};

pub(crate) fn search_docs(
    project_root: &Path,
    query: &str,
    library_scope: Option<&str>,
    max_results: usize,
    content_type: Option<&str>,
    json: bool,
    compact_json: bool,
) -> Result<()> {
    ensure_project(project_root)?;

    let terms = normalize_query(query);
    if terms.is_empty() {
        bail!("search query must contain at least one alphanumeric term");
    }

    let config = read_config()?;
    if configured_api_url(&config).is_some() {
        return search_docs_remote(
            project_root,
            &config,
            query,
            library_scope,
            max_results,
            content_type,
            json,
            compact_json,
        );
    }

    let response = local_search_response(
        project_root,
        &terms,
        library_scope,
        max_results,
        content_type,
    )?;

    if compact_json {
        println!(
            "{}",
            serde_json::to_string(&compact_search_response(&response, None))?
        );
    } else if json {
        println!("{}", serde_json::to_string_pretty(&response)?);
    } else {
        for hit in &response.results {
            println!(
                "{}",
                format_search_location(&hit.path, hit.line, hit.end_line)
            );
        }
    }
    emit_telemetry(
        &config,
        "search_query",
        serde_json::json!({
            "query_length": query.len(),
            "result_count": response.results.len(),
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
    max_results: usize,
    content_type: Option<&str>,
    json: bool,
) -> Result<()> {
    ensure_project(project_root)?;
    let terms = normalize_query(query);
    if terms.is_empty() {
        bail!("context query must contain at least one alphanumeric term");
    }
    let config = read_config()?;
    if configured_api_url(&config).is_some() {
        return context_docs_remote(
            project_root,
            &config,
            query,
            library_scope,
            max_tokens,
            max_results,
            content_type,
            json,
        );
    }
    let hits = local_context_hits(
        project_root,
        &terms,
        library_scope,
        max_results,
        content_type,
    )?;
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

pub(crate) fn search_docs_response(
    project_root: &Path,
    query: &str,
    library_scope: Option<&str>,
    max_results: usize,
    content_type: Option<&str>,
) -> Result<SearchResponse> {
    ensure_project(project_root)?;
    let terms = normalize_query(query);
    if terms.is_empty() {
        bail!("search query must contain at least one alphanumeric term");
    }
    let config = read_config()?;
    if configured_api_url(&config).is_some() {
        return search_docs_remote_response(
            project_root,
            &config,
            query,
            library_scope,
            max_results,
            content_type,
        );
    }
    local_search_response(
        project_root,
        &terms,
        library_scope,
        max_results,
        content_type,
    )
}

pub(crate) fn context_docs_response(
    project_root: &Path,
    query: &str,
    library_scope: Option<&str>,
    max_tokens: usize,
    max_results: usize,
    content_type: Option<&str>,
) -> Result<ContextResponse> {
    ensure_project(project_root)?;
    let terms = normalize_query(query);
    if terms.is_empty() {
        bail!("context query must contain at least one alphanumeric term");
    }
    let config = read_config()?;
    if configured_api_url(&config).is_some() {
        let response = remote_context_response(
            project_root,
            &config,
            query,
            library_scope,
            max_tokens,
            max_results,
            content_type,
        )?;
        warn_stale_response(&response.stale_libraries);
        return Ok(response);
    }
    let hits = local_context_hits(
        project_root,
        &terms,
        library_scope,
        max_results,
        content_type,
    )?;
    let snippets = context_snippets(project_root, &hits, max_tokens)?;
    let results = snippets
        .into_iter()
        .map(|snippet| ContextResult {
            path: snippet["path"].as_str().unwrap_or_default().to_string(),
            line: snippet["line"].as_u64().map(|value| value as usize),
            score: serde_json::Value::Null,
            library: String::new(),
            version: String::new(),
            matched_path: None,
            source_anchor: None,
            content_type: None,
            heading_path: Vec::new(),
            symbols: Vec::new(),
            token_count: snippet["token_count"].as_u64().unwrap_or_default() as usize,
            snippet: snippet["snippet"].as_str().unwrap_or_default().to_string(),
            retrieval_mode: Some("local_grep".to_string()),
            degraded: false,
        })
        .collect();
    Ok(ContextResponse {
        results,
        libraries_to_pull: Vec::new(),
        stale_libraries: Vec::new(),
        retrieval_mode: Some("local_grep".to_string()),
        degraded: false,
    })
}

fn search_docs_remote(
    project_root: &Path,
    config: &OzConfig,
    query: &str,
    library_scope: Option<&str>,
    max_results: usize,
    content_type: Option<&str>,
    json: bool,
    compact_json: bool,
) -> Result<()> {
    let max_results = clamp_max_results(max_results, 1, 50);
    let mut selected_library = None;
    let mut response = if library_scope.is_none() {
        let suggestions = remote_suggestions(project_root, config, query, 5)?;
        if let Some(suggestion) = auto_select_suggestion(&suggestions) {
            let scope = format!("{}/{}", suggestion.vendor, suggestion.library);
            let spec = format!("{scope}@{}", suggestion.version);
            pull_library_impl(project_root, &spec, true)?;
            selected_library = Some(scope.clone());
            remote_search_with_pulls(
                project_root,
                config,
                query,
                Some(&scope),
                max_results,
                content_type,
            )?
        } else if !suggestions.is_empty() {
            let fallback = remote_search_with_pulls(
                project_root,
                config,
                query,
                None,
                max_results,
                content_type,
            )?;
            if fallback.results.is_empty() {
                if compact_json {
                    println!(
                        "{}",
                        serde_json::to_string(&serde_json::json!({
                            "results": [],
                            "suggestions": actionable_suggestions(query, &suggestions),
                        }))?
                    );
                } else if json {
                    println!(
                        "{}",
                        serde_json::to_string_pretty(&serde_json::json!({
                            "results": [],
                            "suggestions": actionable_suggestions(query, &suggestions),
                        }))?
                    );
                } else {
                    eprintln!("oz: choose a library and rerun search:");
                    print_actionable_suggestions(query, &suggestions);
                }
                return Ok(());
            }
            fallback
        } else {
            remote_search_with_pulls(project_root, config, query, None, max_results, content_type)?
        }
    } else {
        remote_search_with_pulls(
            project_root,
            config,
            query,
            library_scope,
            max_results,
            content_type,
        )?
    };

    if response.results.is_empty() && library_scope.is_some() {
        let scope = library_scope.expect("checked is_some");
        if let Some(resolved_scope) = pull_scope_or_suggest(project_root, config, query, scope)? {
            if resolved_scope != scope {
                selected_library = Some(resolved_scope.clone());
            }
            response = remote_search_with_pulls(
                project_root,
                config,
                query,
                Some(&resolved_scope),
                max_results,
                content_type,
            )?;
        }
    }

    warn_stale_response(&response.stale_libraries);
    warn_degraded_response(&response);
    if compact_json {
        println!(
            "{}",
            serde_json::to_string(&compact_search_response(
                &response,
                selected_library.as_deref()
            ))?
        );
    } else if json {
        let mut value = serde_json::to_value(&response)?;
        if let Some(scope) = selected_library {
            value["selected_library"] = serde_json::Value::String(scope);
        }
        println!("{}", serde_json::to_string_pretty(&value)?);
    } else {
        if let Some(scope) = selected_library {
            eprintln!("oz: selected {scope} from suggestions");
        }
        for result in &response.results {
            println!(
                "{}",
                format_search_location(&result.path, result.line, result.end_line)
            );
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

fn search_docs_remote_response(
    project_root: &Path,
    config: &OzConfig,
    query: &str,
    library_scope: Option<&str>,
    max_results: usize,
    content_type: Option<&str>,
) -> Result<SearchResponse> {
    let max_results = clamp_max_results(max_results, 1, 50);
    let mut response = if library_scope.is_none() {
        let suggestions = remote_suggestions(project_root, config, query, 5)?;
        if let Some(suggestion) = auto_select_suggestion(&suggestions) {
            let scope = format!("{}/{}", suggestion.vendor, suggestion.library);
            let spec = format!("{scope}@{}", suggestion.version);
            pull_library_impl(project_root, &spec, true)?;
            remote_search_with_pulls(
                project_root,
                config,
                query,
                Some(&scope),
                max_results,
                content_type,
            )?
        } else {
            remote_search_with_pulls(project_root, config, query, None, max_results, content_type)?
        }
    } else {
        remote_search_with_pulls(
            project_root,
            config,
            query,
            library_scope,
            max_results,
            content_type,
        )?
    };

    if response.results.is_empty() && library_scope.is_some() {
        let scope = library_scope.expect("checked is_some");
        if let Some(resolved_scope) = pull_scope_or_suggest(project_root, config, query, scope)? {
            response = remote_search_with_pulls(
                project_root,
                config,
                query,
                Some(&resolved_scope),
                max_results,
                content_type,
            )?;
        }
    }
    warn_stale_response(&response.stale_libraries);
    warn_degraded_response(&response);
    Ok(response)
}

fn compact_search_response(
    response: &SearchResponse,
    selected_library: Option<&str>,
) -> serde_json::Value {
    let results = response
        .results
        .iter()
        .map(|result| {
            let mut item = serde_json::json!({
                "path": result.path.clone(),
            });
            if let Some(line) = result.line {
                item["line"] = serde_json::json!(line);
            }
            if let Some(end_line) = result.end_line {
                if result.line.map(|line| end_line > line).unwrap_or(true) {
                    item["end_line"] = serde_json::json!(end_line);
                }
            }
            if let Some(kind) = &result.content_type {
                item["type"] = serde_json::json!(kind);
            }
            if !result.library.is_empty() {
                item["library"] = serde_json::json!(result.library.clone());
            }
            if !result.version.is_empty() {
                item["version"] = serde_json::json!(result.version.clone());
            }
            item
        })
        .collect::<Vec<_>>();
    let mut value = serde_json::json!({ "results": results });
    if let Some(scope) = selected_library {
        value["selected_library"] = serde_json::json!(scope);
    }
    if let Some(mode) = &response.retrieval_mode {
        value["retrieval_mode"] = serde_json::json!(mode);
    }
    if response.degraded {
        value["degraded"] = serde_json::json!(true);
    }
    if !response.stale_libraries.is_empty() {
        value["stale_libraries"] = serde_json::json!(response.stale_libraries);
    }
    if !response.libraries_to_pull.is_empty() {
        value["libraries_to_pull"] = serde_json::json!(response.libraries_to_pull);
    }
    value
}

pub(crate) fn format_search_location(
    path: &str,
    line: Option<usize>,
    end_line: Option<usize>,
) -> String {
    match line {
        Some(line) => match end_line.filter(|end_line| *end_line > line) {
            Some(end_line) => format!("{path}:{line}-{end_line}"),
            None => format!("{path}:{line}"),
        },
        None => path.to_string(),
    }
}

fn context_docs_remote(
    project_root: &Path,
    config: &OzConfig,
    query: &str,
    library_scope: Option<&str>,
    max_tokens: usize,
    max_results: usize,
    content_type: Option<&str>,
    json: bool,
) -> Result<()> {
    let response = remote_context_response(
        project_root,
        config,
        query,
        library_scope,
        max_tokens,
        max_results,
        content_type,
    )?;
    warn_stale_response(&response.stale_libraries);
    if response.degraded {
        eprintln!(
            "oz: retrieval degraded ({})",
            response.retrieval_mode.as_deref().unwrap_or("unknown")
        );
    }
    if json {
        println!("{}", serde_json::to_string_pretty(&response)?);
    } else {
        for snippet in &response.results {
            println!(
                "{}:{}{}\n{}\n",
                snippet.path,
                snippet.line.unwrap_or(1),
                snippet
                    .content_type
                    .as_deref()
                    .map(|kind| format!(" [{kind}]"))
                    .unwrap_or_default(),
                snippet.snippet
            );
        }
    }
    emit_telemetry(
        config,
        "context_query",
        serde_json::json!({
            "query_length": query.len(),
            "result_count": response.results.len(),
            "library_scope": library_scope,
        }),
    );
    Ok(())
}

fn remote_context_response(
    project_root: &Path,
    config: &OzConfig,
    query: &str,
    library_scope: Option<&str>,
    max_tokens: usize,
    max_results: usize,
    content_type: Option<&str>,
) -> Result<ContextResponse> {
    let lock = read_lock(project_root)?;
    let response: ContextResponse = api_post_json(
        config,
        "/context",
        serde_json::json!({
            "query": query,
            "project_fingerprint": lock.project_fingerprint,
            "library_scope": library_scope,
            "max_tokens": max_tokens,
            "max_results": clamp_max_results(max_results, 1, 20),
            "content_types": content_type.map(|value| vec![value.to_string()]),
            "installed_libraries": installed_libraries_payload(&lock),
        }),
    )?;
    for library in &response.libraries_to_pull {
        let spec = format!("{}/{}@{}", library.vendor, library.library, library.version);
        pull_library_impl(project_root, &spec, true)?;
    }
    Ok(response)
}

pub(crate) fn remote_search_with_pulls(
    project_root: &Path,
    config: &OzConfig,
    query: &str,
    library_scope: Option<&str>,
    max_results: usize,
    content_type: Option<&str>,
) -> Result<SearchResponse> {
    let lock = read_lock(project_root)?;
    let mut response: SearchResponse = api_post_json(
        config,
        "/search",
        serde_json::json!({
            "query": query,
            "project_fingerprint": lock.project_fingerprint,
            "installed_libraries": installed_libraries_payload(&lock),
            "library_scope": library_scope,
            "max_results": clamp_max_results(max_results, 1, 50),
            "content_types": content_type.map(|value| vec![value.to_string()]),
        }),
    )?;
    for library in &response.libraries_to_pull {
        let spec = format!("{}/{}@{}", library.vendor, library.library, library.version);
        pull_library_impl(project_root, &spec, true)?;
    }
    let mut remaining_stale = Vec::new();
    for stale in &response.stale_libraries {
        if stale.breaking_changes_likely {
            remaining_stale.push(stale.clone());
            continue;
        }
        let spec = format!("{}/{}@{}", stale.vendor, stale.library, stale.newer_version);
        pull_library_impl(project_root, &spec, true)?;
    }
    response.stale_libraries = remaining_stale;
    Ok(response)
}

pub(crate) fn remote_suggestions(
    project_root: &Path,
    config: &OzConfig,
    query: &str,
    max_results: usize,
) -> Result<Vec<SuggestResult>> {
    let lock = read_lock(project_root)?;
    let response: SuggestResponse = api_post_json(
        config,
        "/suggest",
        serde_json::json!({
            "query": query,
            "project_fingerprint": lock.project_fingerprint,
            "installed_libraries": installed_libraries_payload(&lock),
            "max_results": max_results,
        }),
    )?;
    warn_stale_response(&response.stale_libraries);
    Ok(response.results)
}

fn auto_select_suggestion(suggestions: &[SuggestResult]) -> Option<&SuggestResult> {
    let first = suggestions.first()?;
    let first_score = score_as_f64(&first.score);
    let minimum_score = if first_score <= 1.0 { 0.78 } else { 8.0 };
    if suggestions.len() == 1 {
        return (first_score >= minimum_score).then_some(first);
    }
    let second_score = suggestions
        .get(1)
        .map(|suggestion| score_as_f64(&suggestion.score))
        .unwrap_or(0.0);
    let normalized_confident =
        first_score <= 1.0 && first_score >= minimum_score && first_score >= second_score + 0.12;
    let clearly_separated = first_score >= minimum_score && first_score >= second_score * 1.35;
    if normalized_confident || clearly_separated {
        Some(first)
    } else {
        None
    }
}

fn score_as_f64(value: &serde_json::Value) -> f64 {
    value
        .as_f64()
        .or_else(|| value.as_i64().map(|item| item as f64))
        .or_else(|| value.as_u64().map(|item| item as f64))
        .unwrap_or(0.0)
}

pub(crate) fn clamp_max_results(value: usize, min: usize, max: usize) -> usize {
    value.clamp(min, max)
}

pub(crate) fn content_type_matches(actual: &str, requested: Option<&str>) -> bool {
    requested
        .map(|requested| actual == requested)
        .unwrap_or(true)
}

fn warn_degraded_response(response: &SearchResponse) {
    if response.degraded {
        eprintln!(
            "oz: retrieval degraded ({})",
            response.retrieval_mode.as_deref().unwrap_or("unknown")
        );
    }
}

fn actionable_suggestions(query: &str, suggestions: &[SuggestResult]) -> Vec<serde_json::Value> {
    suggestions
        .iter()
        .take(3)
        .map(|suggestion| {
            let scope = format!("{}/{}", suggestion.vendor, suggestion.library);
            serde_json::json!({
                "vendor": suggestion.vendor,
                "library": suggestion.library,
                "version": suggestion.version,
                "score": suggestion.score,
                "reason": suggestion.reason,
                "pull_command": format!("oz pull {scope}"),
                "search_command": format!("oz search {:?} {scope}", query),
            })
        })
        .collect()
}

fn print_actionable_suggestions(query: &str, suggestions: &[SuggestResult]) {
    for suggestion in suggestions.iter().take(3) {
        let scope = format!("{}/{}", suggestion.vendor, suggestion.library);
        println!(
            "{scope}@{}  score={}  {}",
            suggestion.version, suggestion.score, suggestion.reason
        );
        println!("  pull:   oz pull {scope}");
        println!("  search: oz search {:?} {scope}", query);
    }
}

fn pull_scope_or_suggest(
    project_root: &Path,
    config: &OzConfig,
    query: &str,
    scope: &str,
) -> Result<Option<String>> {
    match pull_library_impl(project_root, scope, true) {
        Ok(()) => Ok(Some(scope.to_string())),
        Err(original_error) => {
            let suggested_query = format!("{query} {scope}");
            let suggestions =
                remote_suggestions(project_root, config, &suggested_query, 5).unwrap_or_default();
            if let Some(suggestion) = auto_select_suggestion(&suggestions) {
                let resolved_scope = format!("{}/{}", suggestion.vendor, suggestion.library);
                let spec = format!("{resolved_scope}@{}", suggestion.version);
                pull_library_impl(project_root, &spec, true)?;
                Ok(Some(resolved_scope))
            } else if suggestions.is_empty() {
                Err(original_error)
            } else {
                Ok(None)
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn suggestion(library: &str, score: serde_json::Value) -> SuggestResult {
        SuggestResult {
            vendor: "vendor".to_string(),
            library: library.to_string(),
            version: "latest".to_string(),
            score,
            reason: "matched".to_string(),
        }
    }

    #[test]
    fn auto_selects_only_clear_suggestions() {
        let strong = vec![
            suggestion("react", serde_json::json!(10)),
            suggestion("next", serde_json::json!(5)),
        ];
        assert_eq!(
            auto_select_suggestion(&strong).map(|item| item.library.as_str()),
            Some("react")
        );

        let ambiguous = vec![
            suggestion("react", serde_json::json!(10)),
            suggestion("preact", serde_json::json!(9)),
        ];
        assert!(auto_select_suggestion(&ambiguous).is_none());
    }

    #[test]
    fn auto_selects_normalized_high_confidence_scores() {
        let suggestions = vec![
            suggestion("stripe", serde_json::json!(0.82)),
            suggestion("next", serde_json::json!(0.7)),
        ];
        assert_eq!(
            auto_select_suggestion(&suggestions).map(|item| item.library.as_str()),
            Some("stripe")
        );
    }
}
