/** The playable formats, in display order. Single source of truth for every
 *  format selector / filter across the app. */
export const FORMATS = [
  { code: "standard", label: "Standard" },
  { code: "v_premium", label: "V Premium" },
  { code: "premium", label: "Premium" },
  { code: "g", label: "G Era" },
] as const;

export type FormatCode = (typeof FORMATS)[number]["code"];

export const FORMAT_LABEL: Record<string, string> = Object.fromEntries(
  FORMATS.map((f) => [f.code, f.label]),
);

export function formatLabel(code: string): string {
  return FORMAT_LABEL[code] ?? code;
}
