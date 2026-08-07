import { Zap } from "lucide-react";
import { cn } from "@/lib/cn";

/** Compact power indicator used on deck cards and roster rows. `undefined`/null
 *  power renders a muted "—" so an unassigned deck is legible without relying on
 *  colour alone. */
export function PowerBadge({
  power,
  size = "md",
  className,
}: {
  power: number | null | undefined;
  size?: "sm" | "md" | "lg";
  className?: string;
}) {
  const dims = {
    sm: "h-5 min-w-5 px-1 text-[10px]",
    md: "h-7 min-w-7 px-1.5 text-xs",
    lg: "h-9 min-w-9 px-2 text-sm",
  }[size];
  const set = power != null;
  return (
    <span
      className={cn(
        "font-display inline-flex items-center justify-center gap-0.5 rounded-[4px] border-2 tabular-nums",
        set
          ? "border-[var(--color-accent)] bg-[var(--color-accent)]/15 text-[var(--color-accent)]"
          : "border-dashed border-[var(--color-border)] bg-[var(--color-surface-2)] text-[var(--color-ink-subtle)]",
        dims,
        className,
      )}
      title={set ? `Poder ${power}` : "Poder não definido"}
      aria-label={set ? `Poder ${power}` : "Poder não definido"}
    >
      <Zap className={cn(size === "sm" ? "h-2.5 w-2.5" : "h-3 w-3", set ? "fill-current" : "")} />
      {set ? power : "—"}
    </span>
  );
}
