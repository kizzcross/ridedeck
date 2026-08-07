import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Crown, Sparkles, X } from "lucide-react";
import type { RosterDeck } from "@/api/tournaments";
import { Button } from "@/components/ui";
import { useReduceMotion } from "@/app/MotionProvider";
import { DeckCard, type DeckCardData } from "./DeckCard";
import { ACE_INTRO } from "./copy";
import { cn } from "@/lib/cn";

function toCard(rd: RosterDeck): DeckCardData {
  return { title: rd.label, coverImage: rd.cover_image, power: rd.power, isAce: rd.is_ace };
}

/** A short, celebratory flourish behind the chosen Ace card. */
function Glow({ reduce }: { reduce: boolean }) {
  return (
    <>
      <motion.div
        className="pointer-events-none absolute -inset-8 rounded-full"
        style={{ background: "radial-gradient(circle, var(--color-accent) 0%, transparent 70%)", opacity: 0.35 }}
        initial={reduce ? false : { scale: 0.6, opacity: 0 }}
        animate={reduce ? { opacity: 0.3 } : { scale: [0.6, 1.1, 1], opacity: [0, 0.45, 0.3] }}
        transition={{ duration: 0.7 }}
      />
      {!reduce &&
        Array.from({ length: 10 }).map((_, i) => (
          <motion.span
            key={i}
            className="pointer-events-none absolute left-1/2 top-1/2 h-1.5 w-1.5 rounded-full bg-[var(--color-accent)]"
            initial={{ x: 0, y: 0, opacity: 0 }}
            animate={{
              x: Math.cos((i / 10) * Math.PI * 2) * 120,
              y: Math.sin((i / 10) * Math.PI * 2) * 120,
              opacity: [0, 1, 0],
            }}
            transition={{ duration: 0.9, delay: 0.1 + (i % 5) * 0.03 }}
          />
        ))}
    </>
  );
}

export function AceCeremony({
  open,
  decks,
  ruleHelp,
  onConfirm,
  onClose,
  busy,
}: {
  open: boolean;
  decks: RosterDeck[];
  ruleHelp?: string;
  onConfirm: (rosterDeckUuid: string) => void;
  onClose: () => void;
  busy?: boolean;
}) {
  const reduce = useReduceMotion();
  const currentAce = decks.find((d) => d.is_ace) ?? null;
  const [selected, setSelected] = useState<string | null>(currentAce?.uuid ?? null);

  useEffect(() => {
    if (open) setSelected(currentAce?.uuid ?? null);
  }, [open, currentAce?.uuid]);

  const selectedDeck = decks.find((d) => d.uuid === selected) ?? null;

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 flex flex-col overflow-y-auto bg-black/80 backdrop-blur-sm"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <div className="mx-auto w-full max-w-4xl px-4 py-8" onClick={(e) => e.stopPropagation()}>
            {/* Header */}
            <div className="relative mb-6 text-center">
              <button onClick={onClose} aria-label="Fechar" className="absolute right-0 top-0 text-white/60 hover:text-white">
                <X className="h-6 w-6" />
              </button>
              <span className="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-full border-2 border-[var(--color-accent)] text-[var(--color-accent)] shadow-[0_0_24px_-4px_var(--color-accent)]">
                <Crown className="h-6 w-6 fill-current" />
              </span>
              <h2 className="font-display text-2xl text-white">Escolha o seu Ace</h2>
              <p className="mx-auto mt-2 max-w-xl text-sm leading-relaxed text-white/70">{ACE_INTRO}</p>
              {ruleHelp && (
                <p className="mx-auto mt-2 max-w-xl text-[13px] leading-relaxed text-[var(--color-accent)]/90">
                  <Sparkles className="mr-1 inline h-3.5 w-3.5" />
                  {ruleHelp}
                </p>
              )}
            </div>

            {/* Deck grid */}
            <div className="flex flex-wrap items-start justify-center gap-4">
              {decks.map((rd) => {
                const isSel = selected === rd.uuid;
                return (
                  <div key={rd.uuid} className="relative">
                    {isSel && <Glow reduce={reduce} />}
                    <motion.div layout={!reduce} animate={{ scale: isSel && !reduce ? 1.06 : 1 }}>
                      <DeckCard
                        data={{ ...toCard(rd), isAce: isSel }}
                        size="ceremony"
                        selected={isSel}
                        dimmed={!!selected && !isSel}
                        onClick={() => setSelected(rd.uuid)}
                      />
                    </motion.div>
                  </div>
                );
              })}
            </div>

            {/* Confirm bar */}
            <div className="mt-8 flex flex-col items-center gap-3">
              <AnimatePresence mode="wait">
                {selectedDeck && (
                  <motion.p
                    key={selectedDeck.uuid}
                    initial={reduce ? false : { opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={reduce ? undefined : { opacity: 0, y: -8 }}
                    className="font-display text-center text-lg text-white"
                  >
                    Este será o seu Ace: <span className="text-[var(--color-accent)]">{selectedDeck.label}</span>
                  </motion.p>
                )}
              </AnimatePresence>
              <div className="flex gap-2">
                <Button
                  size="lg"
                  disabled={!selected}
                  loading={busy}
                  onClick={() => selected && onConfirm(selected)}
                >
                  <Crown className="h-4 w-4" /> Confirmar Ace
                </Button>
                <Button size="lg" variant="ghost" className={cn("text-white")} onClick={onClose}>
                  Agora não
                </Button>
              </div>
              <p className="text-center text-xs text-white/50">Você pode trocar o seu Ace até as inscrições fecharem.</p>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
