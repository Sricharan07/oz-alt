import { runtimeConfig } from "./config.js";

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export function apiUrl(path) {
  const { apiBaseUrl } = runtimeConfig();
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${apiBaseUrl}${normalizedPath}`;
}

export async function fetchJson(path, options = {}) {
  const response = await fetch(apiUrl(path), {
    credentials: "include",
    headers: {
      Accept: "application/json",
      ...(options.headers || {})
    },
    ...options
  });
  const body = await safeJson(response);
  if (!response.ok) {
    const message = body?.message || body?.error || `Request failed with ${response.status}`;
    throw new ApiError(message, response.status);
  }
  return body;
}

export async function listLibraries() {
  const payload = await fetchJson("/libraries.json");
  return Array.isArray(payload.libraries) ? payload.libraries : [];
}

export async function getLibrary(vendor, library, version = "") {
  const query = version ? `?version=${encodeURIComponent(version)}` : "";
  return fetchJson(`/api/libraries/${encodePath(vendor)}/${encodeLibrary(library)}${query}`);
}

export async function getStatus() {
  return fetchJson("/status.json");
}

export async function safeJson(response) {
  const text = await response.text();
  if (!text) {
    return null;
  }
  try {
    return JSON.parse(text);
  } catch {
    return { raw: text };
  }
}

export function encodePath(value) {
  return encodeURIComponent(String(value || ""));
}

export function encodeLibrary(value) {
  return String(value || "")
    .split("/")
    .map((part) => encodeURIComponent(part))
    .join("/");
}
