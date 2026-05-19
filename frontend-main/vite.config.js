import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

const backendPaths = [
  "/auth",
  "/account",
  "/api",
  "/catalog",
  "/health",
  "/invite",
  "/libraries.json",
  "/login",
  "/logout",
  "/pack",
  "/privacy",
  "/refs",
  "/reset-password",
  "/search",
  "/signup",
  "/status.json",
  "/suggest",
  "/telemetry",
  "/terms"
];

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ".", "");
  const apiUrl = env.VITE_API_URL || "http://localhost:8765";
  const devPort = Number(env.FRONTEND_PORT || env.VITE_DEV_PORT || 5297);
  const previewPort = Number(env.FRONTEND_PREVIEW_PORT || env.VITE_PREVIEW_PORT || 5298);
  const proxy = Object.fromEntries(
    backendPaths.map((path) => [
      path,
      {
        target: apiUrl,
        changeOrigin: true,
        secure: false
      }
    ])
  );

  return {
    plugins: [react()],
    server: {
      host: "0.0.0.0",
      port: devPort,
      strictPort: true,
      allowedHosts: true,
      proxy
    },
    preview: {
      host: "0.0.0.0",
      port: previewPort,
      strictPort: true,
      allowedHosts: true
    },
    test: {
      environment: "jsdom",
      setupFiles: "./src/test/setupTests.js",
      globals: true,
      css: true
    }
  };
});
