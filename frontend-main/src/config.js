export function runtimeConfig() {
  const runtime = typeof window !== "undefined" ? window.__OZ_CONFIG__ || {} : {};
  return {
    apiBaseUrl: normalizeBase(runtime.apiBaseUrl ?? import.meta.env.VITE_API_URL ?? ""),
    docsUrl: runtime.docsUrl || import.meta.env.VITE_DOCS_URL || "https://tryoz.dev",
    adminUrl: runtime.adminUrl || import.meta.env.VITE_ADMIN_URL || "https://admin.tryoz.dev/admin"
  };
}

function normalizeBase(value) {
  return String(value || "").replace(/\/+$/, "");
}
