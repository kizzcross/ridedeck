const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "") + "/api/v1";

/**
 * Re-route a card image through our same-origin proxy so its pixels are
 * readable off a canvas (the CDN sends no CORS header). Used when capturing a
 * deck to an image. Non-http inputs (or already-proxied URLs) pass through.
 */
export function proxiedImage(url?: string | null): string | undefined {
  if (!url || !/^https?:\/\//.test(url)) return url ?? undefined;
  return `${API_BASE}/cards/img/?u=${encodeURIComponent(url)}`;
}
