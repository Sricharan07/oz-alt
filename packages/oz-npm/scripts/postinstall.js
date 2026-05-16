#!/usr/bin/env node

const {
  chmodSync,
  existsSync,
  mkdirSync,
  createWriteStream,
  renameSync,
  rmSync,
  statSync
} = require("node:fs");
const { get } = require("node:https");
const { join } = require("node:path");

const version = require("../package.json").version;
const platform = process.platform;
const arch = process.arch;
const binaryName = platform === "win32" ? "oz.exe" : "oz";
const vendorDir = join(__dirname, "..", "vendor", `${platform}-${arch}`);
const destination = join(vendorDir, binaryName);
const downloadPath = `${destination}.download`;
const repo = process.env.OZ_REPO || "Sricharan07/oz";

if (process.env.OZ_NPM_SKIP_DOWNLOAD === "1") {
  process.exit(0);
}

if (existsSync(destination) && statSync(destination).size > 0) {
  process.exit(0);
}

const asset = `oz-${platform}-${arch}${platform === "win32" ? ".exe" : ""}`;
const url = `https://github.com/${repo}/releases/download/v${version}/${asset}`;

mkdirSync(vendorDir, { recursive: true });

function cleanup() {
  rmSync(downloadPath, { force: true });
  if (existsSync(destination) && statSync(destination).size === 0) {
    rmSync(destination, { force: true });
  }
}

function download(downloadUrl, redirects = 0) {
  get(downloadUrl, (response) => {
    if (
      response.statusCode >= 300 &&
      response.statusCode < 400 &&
      response.headers.location
    ) {
      response.resume();
      if (redirects >= 5) {
        console.warn(`oz: too many redirects while downloading ${url}`);
        cleanup();
        process.exit(0);
      }
      download(
        new URL(response.headers.location, downloadUrl).toString(),
        redirects + 1
      );
      return;
    }

    if (response.statusCode !== 200) {
      console.warn(`oz: no prebuilt binary found at ${url}`);
      response.resume();
      cleanup();
      process.exit(0);
    }

    const file = createWriteStream(downloadPath, { mode: 0o755 });
    response.pipe(file);
    file.on("finish", () => {
      file.close((error) => {
        if (error || !existsSync(downloadPath) || statSync(downloadPath).size === 0) {
          cleanup();
          process.exit(0);
        }

        if (platform !== "win32") {
          chmodSync(downloadPath, 0o755);
        }

        renameSync(downloadPath, destination);
        process.exit(0);
      });
    });
    file.on("error", () => {
      cleanup();
      process.exit(0);
    });
  }).on("error", () => {
    cleanup();
    process.exit(0);
  });
}

download(url);
