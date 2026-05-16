use super::*;

#[derive(Debug, Clone)]
pub(crate) struct InstallTargets {
    pub(crate) codex: bool,
    pub(crate) claude_code: bool,
    pub(crate) cursor: bool,
    pub(crate) cline: bool,
    pub(crate) continue_agent: bool,
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

pub(crate) fn install_skill(project_root: &Path, targets: InstallTargets) -> Result<()> {
    let targets = targets.selected_or_detected(project_root);
    let mut installed = Vec::new();
    if targets.codex {
        write_markdown_skill(&project_root.join("AGENTS.md"))?;
        let skill_path = write_codex_skill()?;
        installed.push(format!("Codex ({})", skill_path.display()));
    }
    if targets.claude_code {
        write_markdown_skill(&project_root.join("CLAUDE.md"))?;
        let claude_skill = project_root.join(".claude").join("skills").join("oz.md");
        write_markdown_skill(&claude_skill)?;
        installed.push("Claude Code".to_string());
    }
    if targets.cursor {
        write_markdown_skill(&project_root.join(".cursorrules"))?;
        let cursor_rule = project_root.join(".cursor").join("rules").join("oz.mdc");
        write_markdown_skill(&cursor_rule)?;
        installed.push("Cursor".to_string());
    }
    if targets.cline {
        write_markdown_skill(&project_root.join(".clinerules"))?;
        installed.push("Cline".to_string());
    }
    if targets.continue_agent {
        write_continue_config(&project_root.join(".continuerc"))?;
        installed.push("Continue".to_string());
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

fn write_codex_skill() -> Result<PathBuf> {
    let path = codex_skill_path()?;
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)
            .with_context(|| format!("failed to create {}", parent.display()))?;
    }
    fs::write(&path, codex_skill_document())
        .with_context(|| format!("failed to write {}", path.display()))?;
    Ok(path)
}

fn codex_skill_path() -> Result<PathBuf> {
    let codex_home = std::env::var_os("CODEX_HOME")
        .map(PathBuf::from)
        .or_else(|| dirs::home_dir().map(|home| home.join(".codex")))
        .context("failed to locate Codex home directory")?;
    Ok(codex_home.join("skills").join("oz").join("SKILL.md"))
}

fn codex_skill_document() -> String {
    format!(
        r#"---
name: oz
description: Use when working with external libraries or SDKs in a codebase and you need version-accurate documentation before writing code. Pull docs with Oz first, then search the local .codo/vendors files with normal Read, Grep, and Glob tools.
---

{}
"#,
        oz_skill()
    )
}

pub(crate) fn sync_installed_skill(project_root: &Path) -> Result<()> {
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
    if codex_skill_path()
        .map(|path| path.exists())
        .unwrap_or(false)
    {
        write_codex_skill()?;
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
