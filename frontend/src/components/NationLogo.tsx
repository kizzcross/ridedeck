import { useState } from "react";
import { NATION_COLORS, nationLabel } from "@/lib/cardMeta";
import { CLAN_ICON_URLS, NATION_ICON_URLS } from "@/lib/vanguardIcons";
import { cn } from "@/lib/cn";

/**
 * Pixel-art nation emblems. Each glyph is a 9×9 bitmap ('#', '.') rendered as
 * crisp SVG squares — so it scales to any size while keeping the arcade look.
 * Documented in docs/design-system.md.
 */
export const NATION_GLYPHS: Record<string, string[]> = {
  dragon_empire: [
    "....#....",
    "...##....",
    "...###...",
    "..####...",
    ".#####...",
    ".######..",
    ".##.###..",
    ".##..##..",
    "..####...",
  ],
  dark_states: [
    "..####...",
    ".###.....",
    ".##......",
    ".##......",
    ".##......",
    ".##......",
    ".###.....",
    "..####...",
    ".........",
  ],
  brandt_gate: [
    "...#.#...",
    ".#######.",
    ".##...##.",
    "##..#..##",
    "##.###.##",
    "##..#..##",
    ".##...##.",
    ".#######.",
    "...#.#...",
  ],
  keter_sanctuary: [
    "....#....",
    "...###...",
    "..#####..",
    ".#######.",
    "#########",
    ".#######.",
    "..#####..",
    "...###...",
    "....#....",
  ],
  stoicheia: [
    ".......##",
    ".....###.",
    "...####..",
    "..####...",
    ".####.#..",
    "####..#..",
    ".###..#..",
    "..#...#..",
    "......#..",
  ],
  lyrical_monasterio: [
    ".##...##.",
    "#########",
    "#########",
    "#########",
    ".#######.",
    "..#####..",
    "...###...",
    "....#....",
    ".........",
  ],
  united_sanctuary: [
    "#...#...#",
    "#.#.#.#.#",
    "#.#.#.#.#",
    "#.#.#.#.#",
    "#########",
    ".#######.",
    ".#.#.#.#.",
    ".#######.",
    ".........",
  ],
  dark_zone: [
    ".........",
    "##.....##",
    "####.####",
    "#########",
    "#########",
    ".#######.",
    "..##.##..",
    "...#.#...",
    ".........",
  ],
  magallanica: [
    ".........",
    ".##...##.",
    "####.####",
    "##.###.##",
    ".........",
    ".##...##.",
    "####.####",
    "##.###.##",
    ".........",
  ],
  zoo: [
    ".#.#.#.#.",
    "##.#.#.##",
    ".........",
    "..#####..",
    ".#######.",
    ".#######.",
    ".#######.",
    "..#####..",
    ".........",
  ],
  star_gate: [
    "....#....",
    "...###...",
    "...###...",
    "#########",
    ".#######.",
    "#########",
    "...###...",
    "...###...",
    "....#....",
  ],
};

/** The pixel-glyph fallback (used if the real emblem image fails to load). */
function GlyphFallback({ nation, size, className }: { nation: string; size: number; className?: string }) {
  const glyph = NATION_GLYPHS[nation];
  const color = NATION_COLORS[nation] ?? "var(--color-ink-muted)";
  if (!glyph) return null;
  const rects: React.ReactNode[] = [];
  glyph.forEach((row, y) => {
    for (let x = 0; x < row.length; x++) {
      if (row[x] === "#") rects.push(<rect key={`${x}-${y}`} x={x} y={y} width={1} height={1} />);
    }
  });
  return (
    <svg width={size} height={size} viewBox="0 0 9 9" role="img" aria-hidden
      className={cn("shrink-0", className)}
      style={{ shapeRendering: "crispEdges", fill: color }}>
      {rects}
    </svg>
  );
}

/**
 * Nation emblem. Renders the **official** nation icon (referenced from the
 * community wiki, like card art), falling back to the pixel glyph if the image
 * fails to load.
 */
export function NationLogo({
  nation,
  size = 18,
  className,
  title,
}: {
  nation: string;
  size?: number;
  className?: string;
  title?: string;
}) {
  const [failed, setFailed] = useState(false);
  const url = NATION_ICON_URLS[nation];
  if (!url || failed) return <GlyphFallback nation={nation} size={size} className={className} />;
  return (
    <img
      src={url}
      width={size}
      height={size}
      loading="lazy"
      alt={title ?? `Nation: ${nationLabel(nation)}`}
      onError={() => setFailed(true)}
      className={cn("shrink-0 object-contain", className)}
      style={{ width: size, height: size }}
    />
  );
}

/** Official clan emblem (G-era). Returns null if the clan has no known icon. */
export function ClanIcon({ clan, size = 16, className }: { clan: string; size?: number; className?: string }) {
  const [failed, setFailed] = useState(false);
  const url = CLAN_ICON_URLS[clan];
  if (!url || failed) return null;
  return (
    <img
      src={url}
      width={size}
      height={size}
      loading="lazy"
      alt={`Clan: ${clan}`}
      onError={() => setFailed(true)}
      className={cn("shrink-0 object-contain", className)}
      style={{ width: size, height: size }}
    />
  );
}

/** A rounded pixel "coin" version: glyph on a colored tile — used as a compact
 *  nation marker in card corners and lists. */
export function NationCoin({ nation, size = 22 }: { nation: string; size?: number }) {
  const color = NATION_COLORS[nation] ?? "var(--color-border-strong)";
  if (!NATION_GLYPHS[nation]) return null;
  return (
    <span
      className="grid place-items-center rounded-[3px] border border-[var(--color-border)]"
      style={{ width: size, height: size, background: `${color}22` }}
      title={nationLabel(nation)}
    >
      <NationLogo nation={nation} size={size - 8} />
    </span>
  );
}
