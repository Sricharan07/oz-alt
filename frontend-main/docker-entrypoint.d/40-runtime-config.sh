#!/bin/sh
set -eu

cat > /usr/share/nginx/html/config.js <<EOF
window.__OZ_CONFIG__ = {
  apiBaseUrl: "${OZ_CONSOLE_API_BASE_URL:-}",
  docsUrl: "${OZ_DOCS_URL:-https://tryoz.dev}",
  adminUrl: "${OZ_ADMIN_URL:-https://admin.tryoz.dev/admin}"
};
EOF
