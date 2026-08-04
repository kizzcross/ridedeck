import type { HTMLAttributes } from "react";
import { cn } from "@/lib/cn";

type Tone = "neutral" | "brand" | "accent" | "success" | "warning" | "danger" | "official" | "community";

const tones: Record<Tone, string> = {
  neutral: "bg-[var(--color-surface-3)] text-[var(--color-ink-muted)] border-[var(--color-border)]",
  brand: "bg-brand-400/20 text-brand-200 border-brand-400/50",
  accent: "bg-[var(--color-accent)]/20 text-[var(--color-accent)] border-[var(--color-accent)]/50",
  success: "bg-[var(--color-success)]/20 text-[var(--color-success)] border-[var(--color-success)]/50",
  warning: "bg-[var(--color-warning)]/20 text-[var(--color-warning)] border-[var(--color-warning)]/50",
  danger: "bg-[var(--color-danger)]/20 text-[var(--color-danger)] border-[var(--color-danger)]/50",
  official: "bg-[var(--color-violet)]/20 text-[var(--color-violet)] border-[var(--color-violet)]/60",
  community: "bg-[var(--color-cyan)]/20 text-[var(--color-cyan)] border-[var(--color-cyan)]/50",
};

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: Tone;
}

export function Badge({ className, tone = "neutral", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "font-display inline-flex items-center gap-1 rounded-[3px] border px-1.5 py-0.5 text-[9px] uppercase tracking-wider",
        tones[tone],
        className,
      )}
      {...props}
    />
  );
}
