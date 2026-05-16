#!/usr/bin/env node

const { spawnSync } = require("node:child_process");
const { existsSync, statSync } = require("node:fs");
const { join } = require("node:path");

const platform = process.platform;
const arch = process.arch;
const binaryName = platform === "win32" ? "oz.exe" : "oz";
const candidates = [
  process.env.OZ_BIN,
  join(__dirname, "..", "vendor", `${platform}-${arch}`, binaryName),
  join(__dirname, "..", "..", "..", "target", "release", binaryName),
  join(__dirname, "..", "..", "..", "target", "debug", binaryName)
].filter(Boolean);

const binary = candidates.find((candidate) => {
  try {
    return existsSync(candidate) && statSync(candidate).size > 0;
  } catch {
    return false;
  }
});
if (!binary) {
  console.error("oz binary is not installed. Install from GitHub Releases, Homebrew, or run scripts/install.sh.");
  process.exit(127);
}

const result = spawnSync(binary, process.argv.slice(2), { stdio: "inherit" });
process.exit(result.status ?? 1);
