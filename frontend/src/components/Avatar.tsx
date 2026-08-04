import { NationLogo } from "./NationLogo";
import { NATION_COLORS } from "@/lib/cardMeta";
import { cn } from "@/lib/cn";

/** Renders a user avatar from an `avatar_key` like "nation:dragon_empire".
 *  Falls back to a monogram of the username. */
export function Avatar({
  avatarKey,
  username,
  size = 40,
  className,
}: {
  avatarKey?: string | null;
  username?: string;
  size?: number;
  className?: string;
}) {
  const nation = avatarKey?.startsWith("nation:") ? avatarKey.slice(7) : "";
  const color = NATION_COLORS[nation];

  return (
    <span
      className={cn(
        "grid shrink-0 place-items-center overflow-hidden rounded-[6px] border-2 border-[var(--color-border)]",
        className,
      )}
      style={{
        width: size,
        height: size,
        background: color ? `${color}22` : "var(--color-surface-3)",
      }}
      aria-hidden
    >
      {nation ? (
        <NationLogo nation={nation} size={Math.round(size * 0.62)} />
      ) : (
        <span
          className="font-display uppercase text-[var(--color-ink-muted)]"
          style={{ fontSize: size * 0.4 }}
        >
          {(username ?? "?").slice(0, 1)}
        </span>
      )}
    </span>
  );
}
