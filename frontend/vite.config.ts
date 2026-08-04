import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { VitePWA } from "vite-plugin-pwa";
import path from "node:path";

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: "autoUpdate",
      injectRegister: "auto",
      includeAssets: ["favicon.ico", "apple-touch-icon.png"],
      manifest: {
        name: "RideDeck — Cardfight!! Vanguard",
        short_name: "RideDeck",
        description:
          "Deck builder competitivo de Cardfight!! Vanguard: catálogo, coleção, banlists, power level e torneios.",
        lang: "pt-BR",
        theme_color: "#12122a",
        background_color: "#12122a",
        display: "standalone",
        orientation: "portrait",
        start_url: "/",
        scope: "/",
        icons: [
          { src: "/pwa-192x192.png", sizes: "192x192", type: "image/png" },
          { src: "/pwa-512x512.png", sizes: "512x512", type: "image/png" },
          {
            src: "/pwa-maskable-512x512.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "maskable",
          },
        ],
      },
      workbox: {
        globPatterns: ["**/*.{js,css,html,svg,png,ico,woff2}"],
        navigateFallback: "/index.html",
        navigateFallbackDenylist: [/^\/api/, /^\/admin/, /^\/static/, /^\/media/, /^\/healthz/],
        runtimeCaching: [
          {
            // Card art (TCGplayer CDN) — immutable, safe to cache aggressively.
            urlPattern: ({ url }) => url.hostname.includes("tcgplayer"),
            handler: "CacheFirst",
            options: {
              cacheName: "card-images",
              expiration: { maxEntries: 1500, maxAgeSeconds: 60 * 60 * 24 * 30 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
          {
            // Nation/clan emblems (community wiki CDN).
            urlPattern: ({ url }) => url.hostname.includes("nocookie"),
            handler: "CacheFirst",
            options: {
              cacheName: "nation-icons",
              expiration: { maxEntries: 100, maxAgeSeconds: 60 * 60 * 24 * 60 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
          {
            urlPattern: ({ url }) => url.hostname.includes("fonts.g"),
            handler: "CacheFirst",
            options: { cacheName: "google-fonts", expiration: { maxEntries: 30 } },
          },
          {
            // API reads — network-first with a short offline fallback window.
            urlPattern: ({ url }) => url.pathname.startsWith("/api/"),
            handler: "NetworkFirst",
            options: {
              cacheName: "api",
              networkTimeoutSeconds: 5,
              expiration: { maxEntries: 200, maxAgeSeconds: 60 * 30 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
        ],
      },
      devOptions: { enabled: false },
    }),
  ],
  resolve: {
    alias: { "@": path.resolve(__dirname, "./src") },
  },
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": { target: process.env.VITE_PROXY_TARGET || "http://localhost:8000", changeOrigin: true },
      "/media": { target: process.env.VITE_PROXY_TARGET || "http://localhost:8000", changeOrigin: true },
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
  },
} as any);
