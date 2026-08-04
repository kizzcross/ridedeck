import type { HTMLAttributes } from "react";
import { cn } from "@/lib/cn";

export function Panel({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rd-panel-lift rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface)]",
        "shadow-[var(--shadow-hard)]",
        className,
      )}
      {...props}
    />
  );
}

export function PanelHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "font-display flex items-center justify-between gap-3 border-b-2 border-[var(--color-border)] px-4 py-3 text-sm uppercase tracking-wide",
        className,
      )}
      {...props}
    />
  );
}

export function PanelBody({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("p-4", className)} {...props} />;
}
