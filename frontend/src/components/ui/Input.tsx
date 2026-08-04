import { forwardRef, type InputHTMLAttributes, useId } from "react";
import { cn } from "@/lib/cn";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, hint, id, ...props }, ref) => {
    const autoId = useId();
    const inputId = id ?? autoId;
    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label htmlFor={inputId} className="text-sm font-medium text-[var(--color-ink-muted)]">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          aria-invalid={!!error}
          aria-describedby={error ? `${inputId}-err` : hint ? `${inputId}-hint` : undefined}
          className={cn(
            "h-10 w-full rounded-[var(--radius-card)] bg-[var(--color-surface)] px-3 text-sm text-[var(--color-ink)]",
            "border-2 border-[var(--color-border)] placeholder:text-[var(--color-ink-subtle)]",
            "transition-colors focus:border-[var(--color-accent)]",
            error && "border-[var(--color-danger)] focus:border-[var(--color-danger)]",
            className,
          )}
          {...props}
        />
        {error ? (
          <p id={`${inputId}-err`} className="flex items-center gap-1 text-xs text-[var(--color-danger)]">
            <span aria-hidden>⚠</span> {error}
          </p>
        ) : hint ? (
          <p id={`${inputId}-hint`} className="text-xs text-[var(--color-ink-subtle)]">
            {hint}
          </p>
        ) : null}
      </div>
    );
  },
);
Input.displayName = "Input";
