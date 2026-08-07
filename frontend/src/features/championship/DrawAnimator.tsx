import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Crown, Dices, Sparkles } from "lucide-react";
import { Button } from "@/components/ui";
import { useReduceMotion } from "@/app/MotionProvider";

/** The "sorteio" moment: card-backs shuffle, then the drawn deck flies to the
 *  centre and is revealed (with a special flourish for an Ace). Fast enough to
 *  not slow the event down; skipped to an instant reveal when motion is reduced. */
export function DrawAnimator({
  open,
  deckLabel,
  deckCover,
  isAce,
  poolSize = 4,
  onClose,
}: {
  open: boolean;
  deckLabel: string;
  deckCover?: string | null;
  isAce?: boolean;
  poolSize?: number;
  onClose: () => void;
}) {
  const reduce = useReduceMotion();
  const [phase, setPhase] = useState<"shuffle" | "reveal">(reduce ? "reveal" : "shuffle");

  useEffect(() => {
    if (!open) return;
    setPhase(reduce ? "reveal" : "shuffle");
    if (reduce) return;
    const id = setTimeout(() => setPhase("reveal"), 1100);
    return () => clearTimeout(id);
  }, [open, reduce]);

  const backs = Array.from({ length: Math.min(6, Math.max(3, poolSize)) });

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 grid place-items-center bg-black/80 backdrop-blur-sm"
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <div className="flex flex-col items-center gap-6" onClick={(e) => e.stopPropagation()}>
            <p className="font-display flex items-center gap-2 text-lg text-white">
              <Dices className="h-5 w-5 text-[var(--color-accent)]" />
              {phase === "shuffle" ? "Sorteando o seu deck…" : "Seu deck da rodada"}
            </p>

            <div className="relative h-56 w-44">
              <AnimatePresence>
                {phase === "shuffle" &&
                  backs.map((_, i) => (
                    <motion.div
                      key={i}
                      className="absolute inset-0 rounded-[var(--radius-card)] border-2 border-[var(--color-violet)] bg-[repeating-linear-gradient(45deg,var(--color-surface-3),var(--color-surface-3)_8px,var(--color-surface-2)_8px,var(--color-surface-2)_16px)]"
                      initial={{ x: 0, y: 0, rotate: 0 }}
                      animate={{
                        x: [0, (i % 2 ? 1 : -1) * (30 + i * 8), 0],
                        y: [0, (i % 3 - 1) * 16, 0],
                        rotate: [0, (i % 2 ? 1 : -1) * (8 + i * 2), 0],
                      }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.5, repeat: 1, delay: i * 0.04 }}
                    />
                  ))}
              </AnimatePresence>

              {phase === "reveal" && (
                <motion.div
                  className="absolute inset-0 overflow-hidden rounded-[var(--radius-card)] border-2 border-[var(--color-accent)] shadow-[0_0_30px_-4px_var(--color-accent)]"
                  initial={reduce ? false : { rotateY: 90, scale: 0.8 }}
                  animate={{ rotateY: 0, scale: 1 }}
                  transition={{ duration: 0.45 }}
                >
                  {deckCover ? (
                    <img src={deckCover} alt="" className="h-full w-full object-cover" />
                  ) : (
                    <div className="grid h-full w-full place-items-center bg-[var(--color-surface-3)] text-[var(--color-ink-subtle)]"><Dices className="h-8 w-8" /></div>
                  )}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/85 to-transparent" />
                  {isAce && (
                    <span className="absolute right-2 top-2 grid h-8 w-8 place-items-center rounded-full border-2 border-[var(--color-accent)] bg-[#1a1400]/80 text-[var(--color-accent)]">
                      <Crown className="h-4 w-4 fill-current" />
                    </span>
                  )}
                  <p className="absolute inset-x-0 bottom-0 p-2 text-center font-display text-white">{deckLabel}</p>
                </motion.div>
              )}
            </div>

            {phase === "reveal" && (
              <motion.div initial={reduce ? false : { opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col items-center gap-2">
                {isAce && <p className="font-display flex items-center gap-1.5 text-[var(--color-accent)]"><Sparkles className="h-4 w-4" /> Saiu o seu Ace!</p>}
                <Button onClick={onClose}>Continuar</Button>
              </motion.div>
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
