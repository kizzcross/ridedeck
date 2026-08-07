import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowLeft, Check, Crown, Dices, Info, Plus, ShieldCheck, Trash2 } from "lucide-react";
import { tournamentsApi, type Roster, type RosterDeck } from "@/api/tournaments";
import { decksApi } from "@/api/decks";
import { Badge, Button, Panel, Skeleton, useToast } from "@/components/ui";
import { DeckCard, type DeckCardData } from "@/features/championship/DeckCard";
import { CapMeter } from "@/features/championship/CapMeter";
import { AceCeremony } from "@/features/championship/AceCeremony";
import { ExplainerCallout } from "@/features/championship/Explainer";
import {
  ACE_INTRO,
  ACE_RULE_HELP,
  HOW_IT_WORKS_STEPS,
  POWER_HELP,
  ROSTER_HELP,
  SELECTION_MODE_HELP,
  SELECTION_MODE_LABEL,
} from "@/features/championship/copy";
import { apiErrorMessage } from "@/lib/api";
import { useReduceMotion } from "@/app/MotionProvider";
import { cn } from "@/lib/cn";

function invalidReason(rd: RosterDeck): string | null {
  if (rd.is_valid) return null;
  if (!rd.banlist_valid) return "Não permitido pelas regras";
  if (rd.power == null) return "Aguardando nota de força";
  return "Fora das regras de força";
}

function toCard(rd: RosterDeck): DeckCardData {
  return {
    title: rd.label, coverImage: rd.cover_image, power: rd.power, suggestedPower: rd.suggested_power,
    isAce: rd.is_ace, valid: rd.is_valid, invalidReason: invalidReason(rd),
  };
}

export function RosterBuilderPage() {
  const { uuid = "" } = useParams();
  const toast = useToast();
  const qc = useQueryClient();
  const reduce = useReduceMotion();
  const [aceOpen, setAceOpen] = useState(false);

  const { data: t } = useQuery({ queryKey: ["tournament", uuid], queryFn: () => tournamentsApi.detail(uuid) });
  const { data: rosterData, isLoading } = useQuery({
    queryKey: ["my-roster", uuid], queryFn: () => tournamentsApi.myRoster(uuid),
  });
  const { data: myDecks } = useQuery({ queryKey: ["my-decks"], queryFn: decksApi.myDecks });

  const roster = (rosterData && "uuid" in rosterData ? rosterData : null) as Roster | null;
  const refresh = (updated?: Roster) => {
    if (updated) qc.setQueryData(["my-roster", uuid], updated);
    else qc.invalidateQueries({ queryKey: ["my-roster", uuid] });
  };

  const addDeck = useMutation({ mutationFn: (d: string) => tournamentsApi.addRosterDeck(uuid, d), onSuccess: refresh, onError: (e) => toast.error("Não foi possível adicionar", apiErrorMessage(e)) });
  const removeDeck = useMutation({ mutationFn: (rd: string) => tournamentsApi.removeRosterDeck(uuid, rd), onSuccess: refresh, onError: (e) => toast.error("Erro", apiErrorMessage(e)) });
  const setAce = useMutation({ mutationFn: (rd: string | null) => tournamentsApi.setAce(uuid, rd), onSuccess: (r) => { refresh(r); setAceOpen(false); toast.success("Ace escolhido!"); }, onError: (e) => toast.error("Erro", apiErrorMessage(e)) });
  const confirm = useMutation({ mutationFn: () => tournamentsApi.confirmRoster(uuid), onSuccess: (r) => { refresh(r); toast.success("Time confirmado!"); }, onError: (e) => toast.error("Não foi possível confirmar", apiErrorMessage(e)) });

  const usedDeckUuids = useMemo(() => new Set((roster?.decks ?? []).map((d) => d.deck_uuid).filter(Boolean)), [roster]);
  const available = useMemo(
    () => (myDecks?.results ?? []).filter((d) => t && d.format_code === t.format_code && !usedDeckUuids.has(d.uuid)),
    [myDecks, t, usedDeckUuids],
  );

  if (isLoading || !t) return <Skeleton className="h-[70vh] w-full" />;
  if (!roster) {
    return (
      <Panel className="p-8 text-center">
        <p className="text-[var(--color-ink-muted)]">Entre no campeonato para montar o seu time de decks.</p>
        <Link to={`/app/tournaments/${uuid}`} className="mt-3 inline-block">
          <Button variant="secondary"><ArrowLeft className="h-4 w-4" /> Voltar</Button>
        </Link>
      </Panel>
    );
  }

  const slots = Array.from({ length: t.decks_per_player });
  const locked = roster.status === "locked";
  const canAddMore = roster.decks.length < t.decks_per_player && !locked;
  const hasAce = roster.decks.some((d) => d.is_ace);

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-wrap items-center gap-3">
        <Link to={`/app/tournaments/${uuid}`}><Button size="sm" variant="ghost"><ArrowLeft className="h-4 w-4" /></Button></Link>
        <div className="min-w-0 flex-1">
          <h1 className="font-display truncate text-2xl"><span className="text-gradient">Seu time de decks</span></h1>
          <p className="truncate text-sm text-[var(--color-ink-muted)]">{t.name}</p>
        </div>
        <StatusPill status={roster.status} />
      </div>

      {/* First-time explanation of the whole thing */}
      <ExplainerCallout id="championship-intro" title="Como este campeonato funciona" icon={<Info className="h-4 w-4" />}>
        <ol className="space-y-1.5">
          {HOW_IT_WORKS_STEPS.map((s, i) => (
            <li key={i} className="flex gap-2">
              <span className="font-display text-[var(--color-violet)]">{i + 1}.</span>
              <span><strong className="text-[var(--color-ink)]">{s.title}.</strong> {s.body}</span>
            </li>
          ))}
        </ol>
      </ExplainerCallout>

      <div className="grid gap-5 lg:grid-cols-[320px_1fr]">
        {/* Left rail */}
        <div className="space-y-4 lg:sticky lg:top-20 lg:self-start">
          <CapMeter used={roster.power_used} cap={roster.power_cap} />

          <Panel className="space-y-2.5 p-4 text-xs">
            <h3 className="font-display mb-1 text-[10px] uppercase tracking-wide text-[var(--color-ink-muted)]">Regras deste campeonato</h3>
            <Row icon={<Info className="h-3.5 w-3.5" />} label="Decks no time" value={`${t.decks_per_player}`} />
            <Row icon={<Dices className="h-3.5 w-3.5" />} label="Deck de cada partida" value={SELECTION_MODE_LABEL[t.deck_selection_mode] ?? t.deck_selection_mode} />
            <Row icon={<ShieldCheck className="h-3.5 w-3.5" />} label="Cartas proibidas" value={t.banlist_uuid ? "Sim, há uma lista" : "Nenhuma"} />
            {t.ace_enabled && <Row icon={<Crown className="h-3.5 w-3.5 text-[var(--color-accent)]" />} label="Deck Ace" value={t.ace_required ? "Obrigatório" : "Opcional"} />}
            <p className="!mt-2 border-t border-[var(--color-border)] pt-2 leading-relaxed text-[var(--color-ink-subtle)]">
              {SELECTION_MODE_HELP[t.deck_selection_mode]}
            </p>
          </Panel>

          {/* Ace call-to-action + explanation */}
          {t.ace_enabled && (
            <Panel className="space-y-3 border-[var(--color-accent)]/40 p-4">
              <div className="flex items-center gap-2">
                <Crown className="h-4 w-4 text-[var(--color-accent)]" />
                <h3 className="font-display text-sm">Seu Ace</h3>
                {hasAce && <Badge tone="accent" className="ml-auto">definido</Badge>}
              </div>
              <p className="text-[13px] leading-relaxed text-[var(--color-ink-muted)]">{ACE_INTRO}</p>
              {ACE_RULE_HELP[t.ace_rule] && (
                <p className="text-[12px] leading-relaxed text-[var(--color-accent)]/90">{ACE_RULE_HELP[t.ace_rule]}</p>
              )}
              <Button className="w-full" variant={hasAce ? "secondary" : "primary"} disabled={locked || roster.decks.length === 0} onClick={() => setAceOpen(true)}>
                <Crown className="h-4 w-4" /> {hasAce ? "Trocar meu Ace" : "Escolher meu Ace"}
              </Button>
              {roster.decks.length === 0 && <p className="text-center text-[11px] text-[var(--color-ink-subtle)]">Adicione decks primeiro.</p>}
            </Panel>
          )}

          <Button className="w-full" disabled={roster.status !== "valid" || locked} loading={confirm.isPending} onClick={() => confirm.mutate()}>
            <Check className="h-4 w-4" /> {roster.status === "confirmed" ? "Time confirmado" : "Confirmar meu time"}
          </Button>
          {roster.status === "invalid" && (
            <p className="text-center text-[11px] text-[var(--color-danger)]">Ajuste os avisos acima para confirmar.</p>
          )}
        </div>

        {/* Main */}
        <div className="space-y-6">
          <section>
            <div className="mb-2 flex items-center justify-between">
              <h2 className="font-display text-sm uppercase tracking-wide text-[var(--color-ink-muted)]">
                Seu time · {roster.decks.length}/{t.decks_per_player}
              </h2>
            </div>
            <ExplainerCallout id="roster-help" title="O que é este time?" className="mb-3">
              <p>{ROSTER_HELP}</p>
              <p>{POWER_HELP}</p>
            </ExplainerCallout>

            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-4">
              <AnimatePresence mode="popLayout">
                {roster.decks.map((rd) => (
                  <motion.div key={rd.uuid} layout={!reduce}
                    initial={reduce ? false : { opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={reduce ? undefined : { opacity: 0, scale: 0.9 }}>
                    <DeckCard data={toCard(rd)} size="lg"
                      footer={!locked && (
                        <Button size="sm" variant="ghost" className="w-full" aria-label="Remover deck" loading={removeDeck.isPending} onClick={() => removeDeck.mutate(rd.uuid)}>
                          <Trash2 className="h-3.5 w-3.5" /> Remover
                        </Button>
                      )} />
                  </motion.div>
                ))}
              </AnimatePresence>

              {slots.slice(roster.decks.length).map((_, i) => (
                <div key={`slot-${i}`} className="grid aspect-[3/4] w-full place-items-center rounded-[var(--radius-card)] border-2 border-dashed border-[var(--color-border)] bg-[var(--color-surface-2)]/40 text-[var(--color-ink-subtle)]">
                  <div className="text-center">
                    <Plus className="mx-auto h-6 w-6" />
                    <span className="font-display text-[10px] uppercase">Vaga livre</span>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section>
            <h2 className="font-display mb-3 text-sm uppercase tracking-wide text-[var(--color-ink-muted)]">
              Seus decks disponíveis
            </h2>
            {available.length === 0 ? (
              <Panel className="p-6 text-center text-sm text-[var(--color-ink-subtle)]">
                {canAddMore ? "Você não tem mais decks para adicionar neste formato." : "Seu time está completo."}
              </Panel>
            ) : (
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-4">
                {available.map((d) => (
                  <DeckCard key={d.uuid} size="lg" dimmed={!canAddMore}
                    onClick={canAddMore ? () => addDeck.mutate(d.uuid) : undefined}
                    data={{ title: d.title, coverImage: d.cover_image, power: d.power_stars, suggestedPower: d.power_stars }}
                    footer={
                      <Button size="sm" variant="secondary" className="w-full" disabled={!canAddMore} loading={addDeck.isPending} onClick={() => canAddMore && addDeck.mutate(d.uuid)}>
                        <Plus className="h-3.5 w-3.5" /> Adicionar ao time
                      </Button>
                    } />
                ))}
              </div>
            )}
          </section>
        </div>
      </div>

      {t.ace_enabled && (
        <AceCeremony
          open={aceOpen}
          decks={roster.decks}
          ruleHelp={ACE_RULE_HELP[t.ace_rule]}
          busy={setAce.isPending}
          onConfirm={(u) => setAce.mutate(u)}
          onClose={() => setAceOpen(false)}
        />
      )}
    </div>
  );
}

const STATUS_COPY: Record<string, { label: string; tone: "neutral" | "success" | "danger" | "accent" }> = {
  draft: { label: "Montando", tone: "neutral" },
  valid: { label: "Pronto para confirmar", tone: "accent" },
  invalid: { label: "Precisa de ajustes", tone: "danger" },
  confirmed: { label: "Confirmado", tone: "success" },
  locked: { label: "Travado", tone: "neutral" },
};

function StatusPill({ status }: { status: string }) {
  const s = STATUS_COPY[status] ?? { label: status, tone: "neutral" as const };
  return <Badge tone={s.tone}>{s.label}</Badge>;
}

function Row({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-[var(--color-ink-subtle)]">{icon}</span>
      <span className="flex-1 text-[var(--color-ink-muted)]">{label}</span>
      <span className={cn("font-display text-right text-[var(--color-ink)]")}>{value}</span>
    </div>
  );
}
