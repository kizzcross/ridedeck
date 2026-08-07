import { AlertTriangle, CheckCircle2, Zap } from "lucide-react";
import { motion } from "framer-motion";
import { useReduceMotion } from "@/app/MotionProvider";
import { cn } from "@/lib/cn";

type State = "under" | "full" | "over";

function stateOf(used: number, cap: number): State {
  if (used > cap) return "over";
  if (used === cap) return "full";
  return "under";
}

const COPY: Record<State, { label: string; Icon: typeof Zap }> = {
  under: { label: "Dentro do limite", Icon: Zap },
  full: { label: "Roster completo", Icon: CheckCircle2 },
  over: { label: "Acima do limite", Icon: AlertTriangle },
};

/** The hero power-cap indicator. Communicates state with TEXT + ICON + bar —
 *  never colour alone — per the accessibility requirement. */
export function CapMeter({
  used,
  cap,
  className,
}: {
  used: number;
  cap: number;
  className?: string;
}) {
  const reduce = useReduceMotion();
  const state = stateOf(used, cap);
  const { label, Icon } = COPY[state];
  const pct = cap > 0 ? Math.min(100, (used / cap) * 100) : 0;
  const overPct = cap > 0 && used > cap ? Math.min(100, ((used - cap) / cap) * 100) : 0;

  const barColor =
    state === "over" ? "var(--color-danger)" : state === "full" ? "var(--color-success)" : "var(--color-accent)";

  return (
    <div
      className={cn(
        "rounded-[var(--radius-card)] border-2 bg-[var(--color-surface-2)] p-3",
        state === "over" ? "border-[var(--color-danger)]" : "border-[var(--color-border)]",
        className,
      )}
      role="status"
      aria-label={`Poder ${used} de ${cap}. ${label}.`}
    >
      <div className="mb-1.5 flex items-baseline justify-between">
        <span className="font-display flex items-center gap-1.5 text-[10px] uppercase tracking-wide text-[var(--color-ink-muted)]">
          <Zap className="h-3.5 w-3.5 text-[var(--color-accent)]" /> Poder do roster
        </span>
        <span className="font-display text-lg tabular-nums" style={{ color: barColor }}>
          {used}<span className="text-[var(--color-ink-subtle)]">/{cap}</span>
        </span>
      </div>

      <div className="relative h-3 overflow-hidden rounded-[3px] border-2 border-[var(--color-border)] bg-[var(--color-surface)]">
        <motion.div
          className="h-full"
          style={{ background: barColor }}
          initial={reduce ? false : { width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ type: "spring", stiffness: 180, damping: 24 }}
        />
        {overPct > 0 && (
          <div
            className="absolute inset-y-0 right-0 bg-[repeating-linear-gradient(45deg,var(--color-danger),var(--color-danger)_4px,transparent_4px,transparent_8px)]"
            style={{ width: `${Math.min(40, overPct)}%` }}
          />
        )}
      </div>

      <div
        className={cn(
          "mt-1.5 flex items-center gap-1.5 text-[11px]",
          state === "over"
            ? "text-[var(--color-danger)]"
            : state === "full"
              ? "text-[var(--color-success)]"
              : "text-[var(--color-ink-muted)]",
        )}
      >
        <Icon className="h-3.5 w-3.5 shrink-0" />
        <span>
          {label}
          {state === "over" && ` — remova ${used - cap} de poder para validar.`}
          {state === "under" && ` — ${cap - used} de poder disponível.`}
        </span>
      </div>
    </div>
  );
}
