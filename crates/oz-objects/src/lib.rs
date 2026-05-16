use anyhow::{bail, Context, Result};
use base64::Engine;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::fs;
use std::io::{Cursor, Write};
use std::path::{Path, PathBuf};
use walkdir::WalkDir;

const PACK_SCHEMA_VERSION: u32 = 1;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct BlobEntry {
    pub path: PathBuf,
    pub sha256: String,
    pub size: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct TreeManifest {
    pub vendor: String,
    pub library: String,
    pub version: String,
    pub blobs: Vec<BlobEntry>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct PackManifest {
    pub schema_version: u32,
    pub vendor: String,
    pub library: String,
    pub version: String,
    pub tree_sha256: String,
    pub blobs: Vec<BlobEntry>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
struct PackBlob {
    path: PathBuf,
    sha256: String,
    size: u64,
    content_base64: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
struct PackFile {
    manifest: PackManifest,
    blobs: Vec<PackBlob>,
}

impl TreeManifest {
    pub fn new(
        vendor: impl Into<String>,
        library: impl Into<String>,
        version: impl Into<String>,
    ) -> Self {
        Self {
            vendor: vendor.into(),
            library: library.into(),
            version: version.into(),
            blobs: Vec::new(),
        }
    }

    pub fn sort_blobs(&mut self) {
        self.blobs.sort_by(|a, b| a.path.cmp(&b.path));
    }
}

pub fn sha256_hex(bytes: &[u8]) -> String {
    hex::encode(Sha256::digest(bytes))
}

pub fn tree_sha256(manifest: &TreeManifest) -> Result<String> {
    let mut canonical = manifest.clone();
    canonical.sort_blobs();
    let bytes = serde_json::to_vec(&canonical)?;
    Ok(sha256_hex(&bytes))
}

pub fn object_path(objects_root: &Path, sha256: &str) -> PathBuf {
    let prefix = sha256.get(0..2).unwrap_or("00");
    objects_root.join("blobs").join(prefix).join(sha256)
}

pub fn store_blob(objects_root: &Path, bytes: &[u8]) -> Result<String> {
    let sha = sha256_hex(bytes);
    let destination = object_path(objects_root, &sha);
    if destination.exists() {
        return Ok(sha);
    }

    let parent = destination
        .parent()
        .context("object path should always have a parent directory")?;
    fs::create_dir_all(parent)
        .with_context(|| format!("failed to create object directory {}", parent.display()))?;

    let temp_path = destination.with_extension("tmp");
    {
        let mut file = fs::File::create(&temp_path).with_context(|| {
            format!("failed to create temporary object {}", temp_path.display())
        })?;
        file.write_all(bytes)
            .with_context(|| format!("failed to write temporary object {}", temp_path.display()))?;
        file.sync_all()
            .with_context(|| format!("failed to fsync temporary object {}", temp_path.display()))?;
    }

    fs::rename(&temp_path, &destination).with_context(|| {
        format!(
            "failed to finalize object {} -> {}",
            temp_path.display(),
            destination.display()
        )
    })?;
    Ok(sha)
}

pub fn ingest_directory(
    objects_root: &Path,
    source_root: &Path,
    vendor: &str,
    library: &str,
    version: &str,
) -> Result<TreeManifest> {
    let mut manifest = TreeManifest::new(vendor, library, version);

    for entry in WalkDir::new(source_root).sort_by_file_name() {
        let entry = entry.with_context(|| format!("failed walking {}", source_root.display()))?;
        if !entry.file_type().is_file() {
            continue;
        }

        let absolute_path = entry.path();
        let relative_path = absolute_path.strip_prefix(source_root).with_context(|| {
            format!(
                "failed to make {} relative to {}",
                absolute_path.display(),
                source_root.display()
            )
        })?;
        let bytes = fs::read(absolute_path)
            .with_context(|| format!("failed to read source blob {}", absolute_path.display()))?;
        let sha = store_blob(objects_root, &bytes)?;
        manifest.blobs.push(BlobEntry {
            path: relative_path.to_path_buf(),
            sha256: sha,
            size: bytes.len() as u64,
        });
    }

    manifest.sort_blobs();
    Ok(manifest)
}

pub fn write_pack(
    source_root: &Path,
    destination: &Path,
    vendor: &str,
    library: &str,
    version: &str,
) -> Result<PackManifest> {
    let mut manifest = TreeManifest::new(vendor, library, version);
    let mut blobs = Vec::new();

    for entry in WalkDir::new(source_root).sort_by_file_name() {
        let entry = entry.with_context(|| format!("failed walking {}", source_root.display()))?;
        if !entry.file_type().is_file() {
            continue;
        }

        let absolute_path = entry.path();
        let relative_path = absolute_path.strip_prefix(source_root).with_context(|| {
            format!(
                "failed to make {} relative to {}",
                absolute_path.display(),
                source_root.display()
            )
        })?;
        let bytes = fs::read(absolute_path)
            .with_context(|| format!("failed to read source blob {}", absolute_path.display()))?;
        let sha = sha256_hex(&bytes);
        let size = bytes.len() as u64;
        manifest.blobs.push(BlobEntry {
            path: relative_path.to_path_buf(),
            sha256: sha.clone(),
            size,
        });
        blobs.push(PackBlob {
            path: relative_path.to_path_buf(),
            sha256: sha,
            size,
            content_base64: base64::engine::general_purpose::STANDARD.encode(bytes),
        });
    }

    manifest.sort_blobs();
    blobs.sort_by(|a, b| a.path.cmp(&b.path));
    let pack_manifest = PackManifest {
        schema_version: PACK_SCHEMA_VERSION,
        vendor: vendor.to_string(),
        library: library.to_string(),
        version: version.to_string(),
        tree_sha256: tree_sha256(&manifest)?,
        blobs: manifest.blobs,
    };
    let pack = PackFile {
        manifest: pack_manifest.clone(),
        blobs,
    };
    let encoded = serde_json::to_vec(&pack)?;
    let compressed = zstd::stream::encode_all(Cursor::new(encoded), 3)?;

    if let Some(parent) = destination.parent() {
        fs::create_dir_all(parent)
            .with_context(|| format!("failed to create pack directory {}", parent.display()))?;
    }
    fs::write(destination, compressed)
        .with_context(|| format!("failed to write pack {}", destination.display()))?;
    Ok(pack_manifest)
}

pub fn read_pack(path: &Path) -> Result<PackManifest> {
    let pack = read_pack_file(path)?;
    Ok(pack.manifest)
}

pub fn ingest_pack(objects_root: &Path, pack_path: &Path) -> Result<TreeManifest> {
    let pack = read_pack_file(pack_path)?;
    ingest_pack_file(objects_root, pack, &pack_path.display().to_string())
}

pub fn ingest_pack_bytes(
    objects_root: &Path,
    compressed: &[u8],
    label: &str,
) -> Result<TreeManifest> {
    let pack = parse_pack_bytes(compressed, label)?;
    ingest_pack_file(objects_root, pack, label)
}

fn ingest_pack_file(objects_root: &Path, pack: PackFile, label: &str) -> Result<TreeManifest> {
    if pack.manifest.schema_version != PACK_SCHEMA_VERSION {
        bail!(
            "unsupported pack schema version {} in {}",
            pack.manifest.schema_version,
            label
        );
    }

    for blob in &pack.blobs {
        let bytes = base64::engine::general_purpose::STANDARD
            .decode(&blob.content_base64)
            .with_context(|| format!("failed to decode pack blob {}", blob.path.display()))?;
        let actual_sha = sha256_hex(&bytes);
        if actual_sha != blob.sha256 {
            bail!(
                "pack blob {} failed sha verification: expected {}, got {}",
                blob.path.display(),
                blob.sha256,
                actual_sha
            );
        }
        store_blob(objects_root, &bytes)?;
    }

    let tree = TreeManifest {
        vendor: pack.manifest.vendor,
        library: pack.manifest.library,
        version: pack.manifest.version,
        blobs: pack.manifest.blobs,
    };
    let actual_tree_sha = tree_sha256(&tree)?;
    if actual_tree_sha != pack.manifest.tree_sha256 {
        bail!(
            "pack {} failed tree verification: expected {}, got {}",
            label,
            pack.manifest.tree_sha256,
            actual_tree_sha
        );
    }
    Ok(tree)
}

fn read_pack_file(path: &Path) -> Result<PackFile> {
    let compressed =
        fs::read(path).with_context(|| format!("failed to read pack {}", path.display()))?;
    parse_pack_bytes(&compressed, &path.display().to_string())
}

fn parse_pack_bytes(compressed: &[u8], label: &str) -> Result<PackFile> {
    let decoded = zstd::stream::decode_all(Cursor::new(compressed))
        .with_context(|| format!("failed to decompress pack {label}"))?;
    serde_json::from_slice(&decoded).with_context(|| format!("failed to parse pack {label}"))
}

pub fn materialize_tree(
    objects_root: &Path,
    target_root: &Path,
    manifest: &TreeManifest,
) -> Result<()> {
    let temp_root = target_root.with_extension("tmp");
    if temp_root.exists() {
        fs::remove_dir_all(&temp_root)
            .with_context(|| format!("failed to remove stale temp tree {}", temp_root.display()))?;
    }
    fs::create_dir_all(&temp_root)
        .with_context(|| format!("failed to create temp tree {}", temp_root.display()))?;

    for blob in &manifest.blobs {
        let source = object_path(objects_root, &blob.sha256);
        let destination = temp_root.join(&blob.path);
        let parent = destination
            .parent()
            .context("materialized blob path should have a parent")?;
        fs::create_dir_all(parent).with_context(|| {
            format!(
                "failed to create materialized directory {}",
                parent.display()
            )
        })?;
        link_or_copy(&source, &destination)?;
    }

    if target_root.exists() {
        fs::remove_dir_all(target_root)
            .with_context(|| format!("failed to remove old tree {}", target_root.display()))?;
    }
    fs::rename(&temp_root, target_root).with_context(|| {
        format!(
            "failed to move materialized tree {} -> {}",
            temp_root.display(),
            target_root.display()
        )
    })?;
    Ok(())
}

fn link_or_copy(source: &Path, destination: &Path) -> Result<()> {
    match fs::hard_link(source, destination) {
        Ok(()) => Ok(()),
        Err(_) => {
            fs::copy(source, destination).with_context(|| {
                format!(
                    "failed to copy object {} to {} after hardlink failed",
                    source.display(),
                    destination.display()
                )
            })?;
            Ok(())
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn stores_and_materializes_a_directory() {
        let temp = tempfile::tempdir().unwrap();
        let source = temp.path().join("source");
        let objects = temp.path().join("objects");
        let target = temp.path().join("target");
        fs::create_dir_all(source.join("_symbols")).unwrap();
        fs::write(source.join("INDEX.md"), "# Index\n").unwrap();
        fs::write(source.join("_symbols").join("Thing.md"), "# Thing\n").unwrap();

        let manifest = ingest_directory(&objects, &source, "demo", "lib", "1").unwrap();
        assert_eq!(manifest.blobs.len(), 2);

        materialize_tree(&objects, &target, &manifest).unwrap();
        assert_eq!(
            fs::read_to_string(target.join("INDEX.md")).unwrap(),
            "# Index\n"
        );
        assert_eq!(
            fs::read_to_string(target.join("_symbols").join("Thing.md")).unwrap(),
            "# Thing\n"
        );
    }

    #[test]
    fn writes_and_ingests_a_pack() {
        let temp = tempfile::tempdir().unwrap();
        let source = temp.path().join("source");
        let objects = temp.path().join("objects");
        let target = temp.path().join("target");
        let pack = temp.path().join("demo.ozpack");
        fs::create_dir_all(source.join("guides")).unwrap();
        fs::write(source.join("INDEX.md"), "# Index\n").unwrap();
        fs::write(source.join("guides").join("start.md"), "# Start\n").unwrap();

        let manifest = write_pack(&source, &pack, "demo", "lib", "1").unwrap();
        assert_eq!(manifest.blobs.len(), 2);

        let tree = ingest_pack(&objects, &pack).unwrap();
        materialize_tree(&objects, &target, &tree).unwrap();

        assert_eq!(
            fs::read_to_string(target.join("INDEX.md")).unwrap(),
            "# Index\n"
        );
        assert_eq!(
            fs::read_to_string(target.join("guides").join("start.md")).unwrap(),
            "# Start\n"
        );

        let target_from_bytes = temp.path().join("target-bytes");
        let pack_bytes = fs::read(&pack).unwrap();
        let tree = ingest_pack_bytes(&objects, &pack_bytes, "test-pack").unwrap();
        materialize_tree(&objects, &target_from_bytes, &tree).unwrap();
        assert_eq!(
            fs::read_to_string(target_from_bytes.join("INDEX.md")).unwrap(),
            "# Index\n"
        );
    }
}
