import { Sparkle, Sparkles } from "lucide-react";
import { useMotionPref } from "@/app/MotionProvider";
import { cn } from "@/lib/cn";

/** Lets the user turn the fancy animations down. Cycles system → reduced and
 *  back, so anyone bothered by motion can calm the interface instantly. */
export function ReduceMotionToggle({ className }: { className?: string }) {
  const { pref, setPref, reduceMotion } = useMotionPref();
  const reduced = pref === "reduce";
  return (
    <button
      onClick={() => setPref(reduced ? "system" : "reduce")}
      aria-pressed={reduced}
      title={reduced ? "Animações reduzidas — tocar para ativar" : "Reduzir animações"}
      aria-label={reduced ? "Ativar animações" : "Reduzir animações"}
      className={cn(
        "grid h-10 w-10 place-items-center rounded-[var(--radius-card)] border-2 transition-colors",
        reduceMotion
          ? "border-[var(--color-border)] bg-[var(--color-surface-2)] text-[var(--color-ink-subtle)]"
          : "border-[var(--color-border)] text-[var(--color-ink-muted)] hover:text-[var(--color-ink)]",
        className,
      )}
    >
      {reduced ? <Sparkle className="h-5 w-5" /> : <Sparkles className="h-5 w-5" />}
    </button>
  );
}
