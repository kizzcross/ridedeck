import type { ReactNode } from "react";
import { motion } from "framer-motion";
import { CheckCircle2, Layers, XCircle } from "lucide-react";
import { useReduceMotion } from "@/app/MotionProvider";
import { cn } from "@/lib/cn";
import { PowerBadge } from "./PowerBadge";
import { AceSeal } from "./AceSeal";

export interface DeckCardData {
  title: string;
  coverImage?: string | null;
  power?: number | null;
  suggestedPower?: number | null;
  rideLine?: string | null;
  isAce?: boolean;
  valid?: boolean;
  invalidReason?: string | null;
}

const SIZES = {
  sm: { w: "w-28", ratio: "aspect-[3/4]", title: "text-[11px]" },
  md: { w: "w-40", ratio: "aspect-[3/4]", title: "text-sm" },
  lg: { w: "w-full sm:w-52", ratio: "aspect-[3/4]", title: "text-base" },
  ceremony: { w: "w-64", ratio: "aspect-[3/4]", title: "text-lg" },
} as const;

/** The premium deck card used across the championship feature. Large art, name,
 *  ride line, power badge, Ace seal and validity — with tasteful hover depth
 *  (suppressed when motion is reduced). */
export function DeckCard({
  data,
  size = "md",
  selected = false,
  dimmed = false,
  onClick,
  footer,
  className,
}: {
  data: DeckCardData;
  size?: keyof typeof SIZES;
  selected?: boolean;
  dimmed?: boolean;
  onClick?: () => void;
  footer?: ReactNode;
  className?: string;
}) {
  const reduce = useReduceMotion();
  const s = SIZES[size];
  const interactive = !!onClick;
  const showValidity = data.valid !== undefined;

  return (
    <motion.div
      className={cn(s.w, "shrink-0", className)}
      initial={false}
      animate={{ opacity: dimmed ? 0.4 : 1, scale: selected && !reduce ? 1.03 : 1 }}
      whileHover={interactive && !reduce ? { y: -6 } : undefined}
      whileTap={interactive && !reduce ? { scale: 0.98 } : undefined}
      transition={{ type: "spring", stiffness: 260, damping: 22 }}
    >
      <button
        type="button"
        onClick={onClick}
        disabled={!interactive}
        className={cn(
          "group relative block w-full overflow-hidden rounded-[var(--radius-card)] border-2 text-left",
          "bg-[var(--color-surface-2)] transition-colors",
          selected
            ? "border-[var(--color-accent)] shadow-[0_0_0_2px_var(--color-accent),0_18px_36px_-16px_var(--color-accent)]"
            : "border-[var(--color-border)]",
          interactive && "cursor-pointer hover:border-[var(--color-accent)]/70",
        )}
      >
        {/* Art */}
        <div className={cn("relative w-full overflow-hidden bg-[var(--color-surface-3)]", s.ratio)}>
          {data.coverImage ? (
            <img src={data.coverImage} alt="" className="h-full w-full object-cover" loading="lazy" />
          ) : (
            <div className="grid h-full w-full place-items-center text-[var(--color-ink-subtle)]">
              <Layers className="h-8 w-8" />
            </div>
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/10 to-transparent" />
          {data.isAce && <AceSeal variant="corner" />}
          <div className="absolute left-1.5 top-1.5">
            <PowerBadge power={data.power} size={size === "sm" ? "sm" : "md"} />
          </div>

          {/* Title / ride line pinned to the bottom of the art */}
          <div className="absolute inset-x-0 bottom-0 p-2">
            <p className={cn("font-display truncate text-white drop-shadow", s.title)}>{data.title}</p>
            {data.rideLine && (
              <p className="truncate text-[10px] text-white/70">{data.rideLine}</p>
            )}
          </div>
        </div>

        {/* Validity strip */}
        {showValidity && (
          <div
            className={cn(
              "flex items-center gap-1.5 px-2 py-1 text-[10px]",
              data.valid ? "text-[var(--color-success)]" : "text-[var(--color-danger)]",
            )}
          >
            {data.valid ? (
              <>
                <CheckCircle2 className="h-3 w-3 shrink-0" /> Válido
              </>
            ) : (
              <>
                <XCircle className="h-3 w-3 shrink-0" />
                <span className="truncate">{data.invalidReason || "Inválido"}</span>
              </>
            )}
          </div>
        )}
      </button>
      {footer && <div className="mt-1.5">{footer}</div>}
    </motion.div>
  );
}
