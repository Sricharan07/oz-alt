#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

max_pages="${OZ_SEED_MAX_PAGES:-24}"
validation_flag=()
if [[ "${OZ_FAIL_ON_VALIDATION:-1}" == "1" ]]; then
  validation_flag=(--fail-on-validation)
fi

python3 - <<'PY' | while IFS=$'\t' read -r vendor library version source_url; do
import json
from pathlib import Path

for item in json.loads(Path("registry/seed_libraries.json").read_text(encoding="utf-8")):
    print("\t".join([item["vendor"], item["library"], item["version"], item["source_url"]]))
PY
  echo "crawling ${vendor}/${library}@${version}"
  PYTHONPATH=packages/oz-crawler/src python3 -m oz_crawler.cli crawl \
    "$source_url" \
    --vendor "$vendor" \
    --library "$library" \
    --version "$version" \
    --out registry/fixtures \
    --max-pages "$max_pages" \
    --require-profile \
    ${validation_flag+"${validation_flag[@]}"}
done

cargo run -p oz -- dev registry build-packs
