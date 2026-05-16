#!/usr/bin/env node

const { chmodSync, existsSync, mkdirSync, createWriteStream } = require("node:fs");
const { get } = require("node:https");
const { join } = require("node:path");

const version = require("../package.json").version;
const platform = process.platform;
const arch = process.arch;
const binaryName = platform === "win32" ? "oz.exe" : "oz";
const vendorDir = join(__dirname, "..", "vendor", `${platform}-${arch}`);
const destination = join(vendorDir, binaryName);

if (existsSync(destination) || process.env.OZ_NPM_SKIP_DOWNLOAD === "1") {
  process.exit(0);
}

const asset = `oz-${platform}-${arch}${platform === "win32" ? ".exe" : ""}`;
const url = `https://github.com/oz-docs/oz/releases/download/v${version}/${asset}`;

mkdirSync(vendorDir, { recursive: true });
const file = createWriteStream(destination, { mode: 0o755 });

get(url, (response) => {
  if (response.statusCode !== 200) {
    console.warn(`oz: no prebuilt binary found at ${url}`);
    process.exit(0);
  }
  response.pipe(file);
  file.on("finish", () => {
    file.close();
    if (platform !== "win32") {
      chmodSync(destination, 0o755);
    }
  });
}).on("error", () => {
  process.exit(0);
});
