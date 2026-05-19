use super::*;
use std::io::Write;

pub(crate) fn run_mcp_server(project_root: &Path) -> Result<()> {
    let project_root = std::env::var_os("OZ_MCP_PROJECT_ROOT")
        .map(PathBuf::from)
        .unwrap_or_else(|| project_root.to_path_buf());
    ensure_project(&project_root)?;
    let stdin = std::io::stdin();
    let stdout = std::io::stdout();
    let mut reader = std::io::BufReader::new(stdin.lock());
    let mut writer = stdout.lock();

    while let Some(message) = read_mcp_message(&mut reader)? {
        let Some(method) = message.get("method").and_then(|value| value.as_str()) else {
            continue;
        };
        let id = message.get("id").cloned();
        if id.is_none() {
            continue;
        }
        let response = match method {
            "initialize" => mcp_response(
                id,
                serde_json::json!({
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "oz", "version": env!("CARGO_PKG_VERSION")},
                }),
            ),
            "ping" => mcp_response(id, serde_json::json!({})),
            "tools/list" => mcp_response(id, serde_json::json!({ "tools": mcp_tools() })),
            "tools/call" => match call_mcp_tool(
                &project_root,
                message.get("params").cloned().unwrap_or_default(),
            ) {
                Ok(result) => mcp_response(id, result),
                Err(error) => mcp_error(id, -32000, &error.to_string()),
            },
            _ => mcp_error(id, -32601, &format!("unknown method `{method}`")),
        };
        write_mcp_message(&mut writer, &response)?;
    }
    Ok(())
}

fn read_mcp_message<R: std::io::BufRead>(reader: &mut R) -> Result<Option<serde_json::Value>> {
    let mut content_length = None;
    loop {
        let mut line = String::new();
        let bytes = reader.read_line(&mut line)?;
        if bytes == 0 {
            return Ok(None);
        }
        let trimmed = line.trim_end_matches(['\r', '\n']);
        if trimmed.is_empty() {
            break;
        }
        if let Some((name, value)) = trimmed.split_once(':') {
            if name.eq_ignore_ascii_case("content-length") {
                content_length = Some(
                    value
                        .trim()
                        .parse::<usize>()
                        .context("invalid MCP content length")?,
                );
            }
        }
    }
    let length = content_length.context("MCP message missing Content-Length header")?;
    let mut body = vec![0u8; length];
    reader.read_exact(&mut body)?;
    serde_json::from_slice(&body)
        .map(Some)
        .context("failed to parse MCP JSON")
}

fn write_mcp_message<W: Write>(writer: &mut W, message: &serde_json::Value) -> Result<()> {
    let body = serde_json::to_vec(message)?;
    writer.write_all(format!("Content-Length: {}\r\n\r\n", body.len()).as_bytes())?;
    writer.write_all(&body)?;
    writer.flush()?;
    Ok(())
}

fn mcp_response(id: Option<serde_json::Value>, result: serde_json::Value) -> serde_json::Value {
    serde_json::json!({"jsonrpc": "2.0", "id": id, "result": result})
}

fn mcp_error(id: Option<serde_json::Value>, code: i64, message: &str) -> serde_json::Value {
    serde_json::json!({
        "jsonrpc": "2.0",
        "id": id,
        "error": {"code": code, "message": message}
    })
}

fn mcp_tools() -> Vec<serde_json::Value> {
    vec![
        serde_json::json!({
            "name": "oz_search",
            "description": "Search version-pinned Oz docs first for external library APIs. Returns file paths and line numbers; read the files with normal file tools. Use other doc tools only when Oz has no indexed docs.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "library": {"type": "string", "description": "Optional vendor/library scope, for example vercel/next.js"},
                    "max_results": {"type": "integer", "minimum": 1, "maximum": 50},
                    "content_type": {"type": "string", "description": "Optional filter such as code_example or api_reference"}
                },
                "required": ["query"]
            }
        }),
        serde_json::json!({
            "name": "oz_context",
            "description": "Return capped inline Oz snippets only when the agent cannot efficiently read local files. Prefer oz_search first because it uses less context.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "library": {"type": "string", "description": "Optional vendor/library scope, for example vercel/next.js"},
                    "max_tokens": {"type": "integer", "minimum": 100, "maximum": 8000},
                    "max_results": {"type": "integer", "minimum": 1, "maximum": 20},
                    "content_type": {"type": "string", "description": "Optional filter such as code_example or api_reference"}
                },
                "required": ["query"]
            }
        }),
        serde_json::json!({
            "name": "oz_pull",
            "description": "Pull a documentation pack into .codo/vendors so the agent can use native grep/read tools before falling back to other documentation sources.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "library": {"type": "string", "description": "Library spec, for example vercel/next.js@15"}
                },
                "required": ["library"]
            }
        }),
        serde_json::json!({
            "name": "oz_status",
            "description": "List Oz documentation packs already pulled into this project.",
            "inputSchema": {"type": "object", "properties": {}}
        }),
    ]
}

fn call_mcp_tool(project_root: &Path, params: serde_json::Value) -> Result<serde_json::Value> {
    let name = params
        .get("name")
        .and_then(|value| value.as_str())
        .context("tools/call missing params.name")?;
    let arguments = params
        .get("arguments")
        .cloned()
        .unwrap_or_else(|| serde_json::json!({}));
    match name {
        "oz_search" => {
            let query = arguments
                .get("query")
                .and_then(|value| value.as_str())
                .context("oz_search requires query")?;
            let library = arguments.get("library").and_then(|value| value.as_str());
            let content_type = arguments
                .get("content_type")
                .and_then(|value| value.as_str());
            let max_results = arguments
                .get("max_results")
                .and_then(|value| value.as_u64())
                .unwrap_or(10)
                .clamp(1, 50) as usize;
            let response =
                search_docs_response(project_root, query, library, max_results, content_type)?;
            let mut lines = response
                .results
                .iter()
                .map(|result| match result.line {
                    Some(_) => format!(
                        "{}{}",
                        format_search_location(&result.path, result.line, result.end_line),
                        result
                            .content_type
                            .as_deref()
                            .map(|kind| format!(" [{kind}]"))
                            .unwrap_or_default()
                    ),
                    None => result.path.clone(),
                })
                .collect::<Vec<_>>();
            if lines.is_empty() {
                lines.push("no matching Oz docs found".to_string());
            }
            Ok(text_tool_result(lines.join("\n")))
        }
        "oz_context" => {
            let query = arguments
                .get("query")
                .and_then(|value| value.as_str())
                .context("oz_context requires query")?;
            let library = arguments.get("library").and_then(|value| value.as_str());
            let content_type = arguments
                .get("content_type")
                .and_then(|value| value.as_str());
            let max_tokens = arguments
                .get("max_tokens")
                .and_then(|value| value.as_u64())
                .unwrap_or(2000)
                .clamp(100, 8000) as usize;
            let max_results = arguments
                .get("max_results")
                .and_then(|value| value.as_u64())
                .unwrap_or(8)
                .clamp(1, 20) as usize;
            let response = context_docs_response(
                project_root,
                query,
                library,
                max_tokens,
                max_results,
                content_type,
            )?;
            let mut blocks = response
                .results
                .iter()
                .map(|snippet| {
                    format!(
                        "{}:{}{}\n{}",
                        snippet.path,
                        snippet.line.unwrap_or(1),
                        snippet
                            .content_type
                            .as_deref()
                            .map(|kind| format!(" [{kind}]"))
                            .unwrap_or_default(),
                        snippet.snippet
                    )
                })
                .collect::<Vec<_>>();
            if blocks.is_empty() {
                blocks.push("no matching Oz context found".to_string());
            }
            Ok(text_tool_result(blocks.join("\n\n")))
        }
        "oz_pull" => {
            let library = arguments
                .get("library")
                .and_then(|value| value.as_str())
                .context("oz_pull requires library")?;
            pull_library_impl(project_root, library, true)?;
            Ok(text_tool_result(format!("pulled {library}")))
        }
        "oz_status" => {
            let lock = read_lock(project_root)?;
            let text = if lock.pulls.is_empty() {
                "no libraries pulled".to_string()
            } else {
                lock.pulls
                    .iter()
                    .map(|pull| {
                        format!(
                            "{}/{}@{} {}",
                            pull.vendor, pull.library, pull.version, pull.path
                        )
                    })
                    .collect::<Vec<_>>()
                    .join("\n")
            };
            Ok(text_tool_result(text))
        }
        other => bail!("unknown Oz MCP tool `{other}`"),
    }
}

fn text_tool_result(text: String) -> serde_json::Value {
    serde_json::json!({
        "content": [{"type": "text", "text": text}],
        "isError": false
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn reads_header_framed_mcp_message() {
        let body = br#"{"jsonrpc":"2.0","id":1,"method":"ping"}"#;
        let frame = format!("Content-Length: {}\r\n\r\n", body.len());
        let mut bytes = frame.into_bytes();
        bytes.extend_from_slice(body);
        let mut reader = std::io::BufReader::new(bytes.as_slice());
        let message = read_mcp_message(&mut reader).unwrap().unwrap();
        assert_eq!(message["method"], "ping");
        assert_eq!(message["id"], 1);
    }

    #[test]
    fn lists_path_first_tools() {
        let names = mcp_tools()
            .into_iter()
            .filter_map(|tool| {
                tool.get("name")
                    .and_then(|name| name.as_str())
                    .map(str::to_string)
            })
            .collect::<Vec<_>>();
        assert_eq!(
            names,
            vec!["oz_search", "oz_context", "oz_pull", "oz_status"]
        );
    }
}
