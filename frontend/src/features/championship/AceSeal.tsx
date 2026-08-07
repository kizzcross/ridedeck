import { Crown } from "lucide-react";
import { cn } from "@/lib/cn";

/** The premium "Ace" marker shown wherever a player's Ace deck appears (roster,
 *  pairings, draws, stats, history). Variant `corner` overlays a card; `chip` is
 *  an inline label. */
export function AceSeal({
  variant = "chip",
  label = "Ace",
  className,
}: {
  variant?: "corner" | "chip";
  label?: string;
  className?: string;
}) {
  if (variant === "corner") {
    return (
      <span
        className={cn(
          "pointer-events-none absolute right-1.5 top-1.5 grid h-7 w-7 place-items-center rounded-full",
          "border-2 border-[var(--color-accent)] bg-[#1a1400]/80 text-[var(--color-accent)]",
          "shadow-[0_0_14px_-2px_var(--color-accent)]",
          className,
        )}
        aria-label="Ace Deck"
        title="Ace Deck"
      >
        <Crown className="h-4 w-4 fill-current" />
      </span>
    );
  }
  return (
    <span
      className={cn(
        "font-display inline-flex items-center gap-1 rounded-[3px] border-2 px-1.5 py-0.5 text-[9px] uppercase tracking-wider",
        "border-[var(--color-accent)] bg-[var(--color-accent)]/15 text-[var(--color-accent)]",
        className,
      )}
    >
      <Crown className="h-3 w-3 fill-current" /> {label}
    </span>
  );
}
