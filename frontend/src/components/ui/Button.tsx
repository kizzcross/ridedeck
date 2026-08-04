import { forwardRef, type ButtonHTMLAttributes } from "react";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/cn";

type Variant = "primary" | "secondary" | "ghost" | "danger" | "outline";
type Size = "sm" | "md" | "lg" | "icon";

const variants: Record<Variant, string> = {
  primary:
    "bg-brand-400 text-[#2a1a00] hover:bg-brand-300 border-2 border-[var(--color-border)] shadow-[var(--shadow-hard-sm)] rd-press",
  secondary:
    "bg-[var(--color-surface-3)] text-[var(--color-ink)] border-2 border-[var(--color-border)] shadow-[var(--shadow-hard-sm)] rd-press hover:bg-[var(--color-border-strong)]",
  ghost:
    "bg-transparent text-[var(--color-ink-muted)] hover:bg-[var(--color-surface-2)] hover:text-[var(--color-ink)]",
  danger:
    "bg-[var(--color-danger)] text-[#2a0000] border-2 border-[var(--color-border)] shadow-[var(--shadow-hard-sm)] rd-press hover:brightness-110",
  outline:
    "border-2 border-[var(--color-border-strong)] bg-transparent text-[var(--color-ink)] hover:bg-[var(--color-surface-2)]",
};

const sizes: Record<Size, string> = {
  sm: "h-8 px-3 text-[11px] gap-1.5",
  md: "h-10 px-4 text-xs gap-2",
  lg: "h-12 px-6 text-sm gap-2.5",
  icon: "h-10 w-10 p-0",
};

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", loading, disabled, children, ...props }, ref) => (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={cn(
        "font-display inline-flex items-center justify-center rounded-[var(--radius-card)] uppercase tracking-wide",
        "disabled:opacity-50 disabled:pointer-events-none select-none",
        variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    >
      {loading && <Loader2 className="h-4 w-4 animate-spin" aria-hidden />}
      {children}
    </button>
  ),
);
Button.displayName = "Button";
