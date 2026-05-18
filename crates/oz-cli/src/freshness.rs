use super::*;

pub(crate) fn warn_stale_libraries(project_root: &Path) -> Result<()> {
    let lock = match read_lock(project_root) {
        Ok(lock) => lock,
        Err(_) => return Ok(()),
    };
    if lock.pulls.is_empty() {
        return Ok(());
    }
    let config = read_config().unwrap_or_default();
    if configured_api_url(&config).is_some() {
        let mut route = format!(
            "/refs?fingerprint={}",
            url_component(&lock.project_fingerprint)
        );
        for pull in &lock.pulls {
            route.push_str("&library=");
            route.push_str(&url_component(&format!(
                "{}/{}@{}",
                pull.vendor, pull.library, pull.version
            )));
        }
        if let Ok(response) = api_get_json::<BulkRefsResponse>(&config, &route) {
            for stale in response.stale_libraries {
                let action = if stale.breaking_changes_likely {
                    "major-version change; review your lockfile before running"
                } else {
                    "run"
                };
                eprintln!(
                    "oz: {}/{}@{} is stale (newer: {}). {action} 'oz update {}/{}'.",
                    stale.vendor,
                    stale.library,
                    stale.version,
                    stale.newer_version,
                    stale.vendor,
                    stale.library
                );
            }
            return Ok(());
        }
    }

    for pull in lock.pulls {
        if let Some(latest) = latest_version(project_root, &pull.vendor, &pull.library)
            .ok()
            .flatten()
        {
            if latest != pull.version {
                eprintln!(
                    "oz: {}/{}@{} is stale (newer: {}). Run 'oz update {}/{}'.",
                    pull.vendor, pull.library, pull.version, latest, pull.vendor, pull.library
                );
            }
        }
    }
    Ok(())
}

pub(crate) fn installed_libraries_payload(lock: &ProjectLock) -> Vec<serde_json::Value> {
    lock.pulls
        .iter()
        .map(|pull| {
            serde_json::json!({
                "vendor": pull.vendor,
                "library": pull.library,
                "version": pull.version,
            })
        })
        .collect()
}

pub(crate) fn warn_stale_response(stale_libraries: &[StaleLibrary]) {
    for stale in stale_libraries {
        eprintln!(
            "oz: {}/{}@{} is stale (newer: {}). Run 'oz update {}/{}'.",
            stale.vendor,
            stale.library,
            stale.version,
            stale.newer_version,
            stale.vendor,
            stale.library
        );
    }
}
