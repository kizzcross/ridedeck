import { useCallback, useState, type ReactNode } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Check, HelpCircle, X } from "lucide-react";
import { useReduceMotion } from "@/app/MotionProvider";
import { cn } from "@/lib/cn";

const PREFIX = "rd-explain-";

/** Remembers whether the user has dismissed a given explanation, so plain-language
 *  help shows the first time(s) and then stays out of the way. */
export function useSeen(key: string): [boolean, () => void, () => void] {
  const storageKey = PREFIX + key;
  const [seen, setSeen] = useState(() => {
    try { return localStorage.getItem(storageKey) === "1"; } catch { return false; }
  });
  const markSeen = useCallback(() => {
    try { localStorage.setItem(storageKey, "1"); } catch { /* ignore */ }
    setSeen(true);
  }, [storageKey]);
  const reset = useCallback(() => {
    try { localStorage.removeItem(storageKey); } catch { /* ignore */ }
    setSeen(false);
  }, [storageKey]);
  return [seen, markSeen, reset];
}

/** A friendly, dismissible explanation written in plain language. Stays until the
 *  user taps "Entendi" (then never nags again for that key). */
export function ExplainerCallout({
  id,
  title,
  children,
  icon,
  className,
}: {
  id: string;
  title: string;
  children: ReactNode;
  icon?: ReactNode;
  className?: string;
}) {
  const [seen, markSeen] = useSeen(id);
  const reduce = useReduceMotion();
  return (
    <AnimatePresence initial={false}>
      {!seen && (
        <motion.div
          initial={reduce ? false : { opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={reduce ? { opacity: 0 } : { opacity: 0, height: 0 }}
          className={cn("overflow-hidden", className)}
        >
          <div className="relative rounded-[var(--radius-card)] border-2 border-[var(--color-violet)]/50 bg-[var(--color-violet)]/10 p-4">
            <div className="flex items-start gap-3">
              <span className="mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-full bg-[var(--color-violet)]/20 text-[var(--color-violet)]">
                {icon ?? <HelpCircle className="h-4 w-4" />}
              </span>
              <div className="min-w-0 flex-1">
                <h4 className="font-display mb-1 text-sm text-[var(--color-ink)]">{title}</h4>
                <div className="space-y-2 text-[13px] leading-relaxed text-[var(--color-ink-muted)]">{children}</div>
                <button
                  onClick={markSeen}
                  className="font-display mt-3 inline-flex items-center gap-1.5 rounded-[6px] border-2 border-[var(--color-violet)]/60 bg-[var(--color-violet)]/15 px-3 py-1.5 text-[11px] uppercase tracking-wide text-[var(--color-violet)] transition-colors hover:bg-[var(--color-violet)]/25"
                >
                  <Check className="h-3.5 w-3.5" /> Entendi, não mostrar de novo
                </button>
              </div>
              <button onClick={markSeen} aria-label="Fechar" className="text-[var(--color-ink-subtle)] hover:text-[var(--color-ink)]">
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

/** A small always-available "?" that re-opens an explanation the user dismissed. */
export function HelpDot({ onClick, label = "O que é isto?" }: { onClick: () => void; label?: string }) {
  return (
    <button
      onClick={onClick}
      aria-label={label}
      title={label}
      className="inline-grid h-5 w-5 place-items-center rounded-full border border-[var(--color-border)] text-[var(--color-ink-subtle)] transition-colors hover:border-[var(--color-violet)] hover:text-[var(--color-violet)]"
    >
      <HelpCircle className="h-3 w-3" />
    </button>
  );
}
