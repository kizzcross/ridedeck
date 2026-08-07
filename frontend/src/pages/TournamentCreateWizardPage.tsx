import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowLeft, ArrowRight, Check, Crown, Dices, Layers, ListChecks, Shield, Sparkles, Trophy, Users,
} from "lucide-react";
import { tournamentsApi } from "@/api/tournaments";
import { banlistsApi } from "@/api/banlists";
import { Button, Panel, useToast } from "@/components/ui";
import { CapMeter } from "@/features/championship/CapMeter";
import { ACE_INTRO, ACE_RULE_HELP, SELECTION_MODE_HELP, SELECTION_MODE_LABEL } from "@/features/championship/copy";
import { apiErrorMessage } from "@/lib/api";
import { useReduceMotion } from "@/app/MotionProvider";
import { cn } from "@/lib/cn";

type Config = Record<string, unknown>;

const DEFAULTS: Config = {
  kind: "roster", name: "", description: "", image: "", max_participants: 16,
  format_code: "standard", format_kind: "points", bracket_type: "swiss",
  decks_per_player: 4, power_cap: 15, min_deck_power: null, max_deck_power: null,
  deck_selection_mode: "random_rotation", random_options_count: 2,
  ace_enabled: false, ace_rule: "visual_only", ace_required: false,
  roster_visibility: "partial", banlist_uuid: null,
};

const FORMAT_KINDS = [
  { v: "points", icon: ListChecks, label: "Só pontos", help: "Todos jogam várias rodadas e quem somar mais pontos vence. Sem mata-mata." },
  { v: "bracket", icon: Trophy, label: "Só mata-mata", help: "Chaveamento direto: quem perde é eliminado até sobrar o campeão." },
  { v: "hybrid", icon: Sparkles, label: "Pontos e depois mata-mata", help: "Primeiro rodadas por pontos, depois os melhores disputam um mata-mata final." },
];

const SELECTION_MODES = ["random_rotation", "random_free", "random_no_consecutive", "predetermined_order", "choose_from_random", "manual"];

const ACE_RULES = [
  { v: "visual_only", label: "Só destaque visual" },
  { v: "manual_once", label: "Jogar o Ace uma vez" },
  { v: "replace_draw", label: "Trocar um sorteio pelo Ace" },
  { v: "weighted_random", label: "Ace aparece mais nos sorteios" },
  { v: "extra_in_rotation", label: "Ace aparece uma vez extra" },
  { v: "tiebreak_wins", label: "Vitórias com Ace desempatam" },
];

const VISIBILITY = [
  { v: "open", label: "Abertos", help: "Todos veem os decks e a força de cada time." },
  { v: "partial", label: "Parciais", help: "Veem os nomes e a força, mas não a lista completa de cartas." },
  { v: "closed", label: "Fechados", help: "O time do adversário só aparece quando o deck é usado." },
];

export function TournamentCreateWizardPage() {
  const navigate = useNavigate();
  const toast = useToast();
  const reduce = useReduceMotion();
  const [step, setStep] = useState(0);
  const [cfg, setCfg] = useState<Config>(DEFAULTS);
  const set = (patch: Config) => setCfg((c) => ({ ...c, ...patch }));

  const { data: presets } = useQuery({ queryKey: ["t-presets"], queryFn: () => tournamentsApi.presets() });
  const { data: banlists } = useQuery({ queryKey: ["banlists"], queryFn: () => banlistsApi.list() });

  const create = useMutation({
    mutationFn: () => tournamentsApi.create(cfg),
    onSuccess: (t) => { toast.success("Campeonato criado!"); navigate(`/app/tournaments/${t.uuid}`); },
    onError: (e) => toast.error("Erro ao criar", apiErrorMessage(e)),
  });

  const steps = ["Início", "Formato", "Time & Força", "Decks nas partidas", "Ace", "Times & Cartas", "Revisão"];

  const num = (k: string) => Number(cfg[k] ?? 0);
  const str = (k: string) => String(cfg[k] ?? "");

  const stepValid = useMemo(() => {
    if (step === 0) return str("name").trim().length > 0;
    if (step === 2) return num("decks_per_player") >= 1 && num("power_cap") >= 1;
    return true;
  }, [step, cfg]); // eslint-disable-line

  const next = () => setStep((s) => Math.min(steps.length - 1, s + 1));
  const back = () => setStep((s) => Math.max(0, s - 1));

  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <div className="flex items-center gap-3">
        <Button size="sm" variant="ghost" onClick={() => navigate("/app/tournaments")}><ArrowLeft className="h-4 w-4" /></Button>
        <h1 className="font-display text-2xl"><span className="text-gradient">Novo campeonato</span></h1>
      </div>

      {/* Stepper */}
      <div className="flex flex-wrap gap-1.5">
        {steps.map((s, i) => (
          <button key={s} onClick={() => i <= step && setStep(i)}
            className={cn("font-display rounded-[6px] border-2 px-2.5 py-1 text-[10px] uppercase tracking-wide transition-colors",
              i === step ? "border-[var(--color-accent)] bg-[var(--color-accent)] text-[#1a1400]"
                : i < step ? "border-[var(--color-border)] bg-[var(--color-surface-2)] text-[var(--color-ink)]"
                  : "border-[var(--color-border)] bg-[var(--color-surface-2)] text-[var(--color-ink-subtle)]")}>
            {i + 1}. {s}
          </button>
        ))}
      </div>

      <div className="grid gap-5 lg:grid-cols-[1fr_300px]">
        <Panel className="p-5">
          <AnimatePresence mode="wait">
            <motion.div key={step}
              initial={reduce ? false : { opacity: 0, x: 12 }} animate={{ opacity: 1, x: 0 }}
              exit={reduce ? undefined : { opacity: 0, x: -12 }} transition={{ duration: 0.2 }}
              className="space-y-4">

              {step === 0 && (
                <>
                  <StepTitle icon={Layers} title="Comece por um modelo (opcional)" help="Escolha um modelo pronto e ajuste o que quiser depois. Ou pule e configure do zero." />
                  <div className="grid gap-2 sm:grid-cols-2">
                    {(presets ?? []).map((p) => (
                      <button key={p.code} onClick={() => set({ ...p.config, name: str("name") || p.name })}
                        className="rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface-2)] p-3 text-left transition-colors hover:border-[var(--color-accent)]">
                        <p className="font-display text-sm">{p.name}</p>
                        <p className="mt-0.5 text-[11px] leading-snug text-[var(--color-ink-muted)]">{p.description}</p>
                      </button>
                    ))}
                  </div>
                  <Field label="Nome do campeonato">
                    <input value={str("name")} onChange={(e) => set({ name: e.target.value })} autoFocus
                      placeholder="Copa de Verão…" className={inputCls} />
                  </Field>
                  <Field label="Descrição (opcional)">
                    <textarea value={str("description")} onChange={(e) => set({ description: e.target.value })}
                      rows={2} placeholder="Regras, premiação, horários…" className={inputCls} />
                  </Field>
                  <Field label="Banner / imagem (link, opcional)">
                    <input value={str("image")} onChange={(e) => set({ image: e.target.value })}
                      placeholder="https://…" className={inputCls} />
                  </Field>
                </>
              )}

              {step === 1 && (
                <>
                  <StepTitle icon={Trophy} title="Como o campeão é decidido" help="Escolha o formato da competição." />
                  <div className="grid gap-2">
                    {FORMAT_KINDS.map((f) => (
                      <OptionCard key={f.v} active={str("format_kind") === f.v} onClick={() => set({ format_kind: f.v })}
                        icon={<f.icon className="h-4 w-4" />} label={f.label} help={f.help} />
                    ))}
                  </div>

                  {str("format_kind") === "points" && (
                    <div className="grid gap-2 sm:grid-cols-2">
                      <OptionCard active={str("bracket_type") === "swiss"} onClick={() => set({ bracket_type: "swiss" })} icon={<ListChecks className="h-4 w-4" />} label="Suíço" help="Cada rodada junta quem tem pontuação parecida. Ideal para muitos jogadores." />
                      <OptionCard active={str("bracket_type") === "round_robin"} onClick={() => set({ bracket_type: "round_robin" })} icon={<ListChecks className="h-4 w-4" />} label="Todos contra todos" help="Cada um joga contra todos os outros. Bom para grupos pequenos." />
                    </div>
                  )}
                  {str("format_kind") === "bracket" && (
                    <div className="grid gap-2 sm:grid-cols-2">
                      <OptionCard active={str("bracket_type") === "single_elimination"} onClick={() => set({ bracket_type: "single_elimination" })} icon={<Trophy className="h-4 w-4" />} label="Eliminação simples" help="Quem perde está fora." />
                      <OptionCard active={str("bracket_type") === "double_elimination"} onClick={() => set({ bracket_type: "double_elimination" })} icon={<Trophy className="h-4 w-4" />} label="Eliminação dupla" help="Só sai depois de perder duas vezes." />
                    </div>
                  )}
                  {str("format_kind") === "hybrid" && (
                    <Field label="Quantos jogadores avançam para o mata-mata">
                      <input type="number" min={2} value={num("hybrid_advance_count") || 8} onChange={(e) => set({ hybrid_advance_count: +e.target.value })} className={inputCls} />
                    </Field>
                  )}
                  {(str("format_kind") === "points" || str("format_kind") === "hybrid") && str("bracket_type") !== "round_robin" && (
                    <Field label="Número de rodadas (deixe vazio para automático)">
                      <input type="number" min={1} value={cfg.rounds_count == null ? "" : num("rounds_count")} onChange={(e) => set({ rounds_count: e.target.value === "" ? null : +e.target.value })} className={inputCls} />
                    </Field>
                  )}
                  {(str("format_kind") === "bracket" || str("format_kind") === "hybrid") && (
                    <Field label="Como montar o chaveamento">
                      <select value={str("seed_source") || "random"} onChange={(e) => set({ seed_source: e.target.value })} className={inputCls}>
                        <option value="random">Sorteado</option>
                        <option value="manual">Definido pelo organizador</option>
                        <option value="platform_ranking">Pelo ranking da plataforma</option>
                      </select>
                    </Field>
                  )}

                  <Field label="Máximo de jogadores">
                    <input type="number" min={2} value={num("max_participants")} onChange={(e) => set({ max_participants: +e.target.value })} className={inputCls} />
                  </Field>
                </>
              )}

              {step === 2 && (
                <>
                  <StepTitle icon={Users} title="O time de cada jogador" help="Quantos decks cada pessoa traz e o limite de força somada do time. A força de cada deck você define depois, com o time inscrito." />
                  <div className="grid grid-cols-2 gap-3">
                    <Field label="Decks por jogador"><input type="number" min={1} max={12} value={num("decks_per_player")} onChange={(e) => set({ decks_per_player: +e.target.value })} className={inputCls} /></Field>
                    <Field label="Limite de força do time"><input type="number" min={1} value={num("power_cap")} onChange={(e) => set({ power_cap: +e.target.value })} className={inputCls} /></Field>
                    <Field label="Força mínima por deck (opcional)"><input type="number" min={0} value={cfg.min_deck_power == null ? "" : num("min_deck_power")} onChange={(e) => set({ min_deck_power: e.target.value === "" ? null : +e.target.value })} className={inputCls} /></Field>
                    <Field label="Força máxima por deck (opcional)"><input type="number" min={0} value={cfg.max_deck_power == null ? "" : num("max_deck_power")} onChange={(e) => set({ max_deck_power: e.target.value === "" ? null : +e.target.value })} className={inputCls} /></Field>
                  </div>
                </>
              )}

              {step === 3 && (
                <>
                  <StepTitle icon={Dices} title="Qual deck em cada partida" help="Cada partida usa só um deck do time. Escolha como esse deck é decidido a cada rodada." />
                  <div className="grid gap-2">
                    {SELECTION_MODES.map((m) => (
                      <OptionCard key={m} active={str("deck_selection_mode") === m} onClick={() => set({ deck_selection_mode: m })}
                        icon={<Dices className="h-4 w-4" />} label={SELECTION_MODE_LABEL[m]} help={SELECTION_MODE_HELP[m]} />
                    ))}
                  </div>
                  {str("deck_selection_mode") === "choose_from_random" && (
                    <Field label="Quantos decks sortear para o jogador escolher">
                      <input type="number" min={2} max={4} value={num("random_options_count")} onChange={(e) => set({ random_options_count: +e.target.value })} className={inputCls} />
                    </Field>
                  )}
                </>
              )}

              {step === 4 && (
                <>
                  <StepTitle icon={Crown} title="Deck Ace" help={ACE_INTRO} />
                  <div className="grid gap-2 sm:grid-cols-2">
                    <OptionCard active={!cfg.ace_enabled} onClick={() => set({ ace_enabled: false })} icon={<Crown className="h-4 w-4" />} label="Sem Ace" help="Ninguém escolhe um deck de destaque." />
                    <OptionCard active={!!cfg.ace_enabled} onClick={() => set({ ace_enabled: true })} icon={<Crown className="h-4 w-4" />} label="Com Ace" help="Cada jogador marca um deck como Ace." />
                  </div>
                  {!!cfg.ace_enabled && (
                    <>
                      <p className="font-display text-[10px] uppercase tracking-wide text-[var(--color-ink-muted)]">O que o Ace faz</p>
                      <div className="grid gap-2">
                        {ACE_RULES.map((r) => (
                          <OptionCard key={r.v} active={str("ace_rule") === r.v} onClick={() => set({ ace_rule: r.v })}
                            icon={<Crown className="h-4 w-4" />} label={r.label} help={ACE_RULE_HELP[r.v]} />
                        ))}
                      </div>
                      <label className="flex cursor-pointer items-center gap-2 text-sm text-[var(--color-ink-muted)]">
                        <input type="checkbox" checked={!!cfg.ace_required} onChange={(e) => set({ ace_required: e.target.checked })} className="accent-[var(--color-accent)]" />
                        Escolher um Ace é obrigatório
                      </label>
                    </>
                  )}
                </>
              )}

              {step === 5 && (
                <>
                  <StepTitle icon={Shield} title="Times & cartas" help="Quem enxerga o time dos outros, e se alguma lista de cartas proibidas será usada." />
                  <p className="font-display text-[10px] uppercase tracking-wide text-[var(--color-ink-muted)]">Quem vê os times</p>
                  <div className="grid gap-2">
                    {VISIBILITY.map((v) => (
                      <OptionCard key={v.v} active={str("roster_visibility") === v.v} onClick={() => set({ roster_visibility: v.v })}
                        icon={<Users className="h-4 w-4" />} label={v.label} help={v.help} />
                    ))}
                  </div>
                  <Field label="Cartas proibidas (banlist)">
                    <select value={cfg.banlist_uuid == null ? "" : str("banlist_uuid")} onChange={(e) => set({ banlist_uuid: e.target.value || null })} className={inputCls}>
                      <option value="">Nenhuma — vale tudo</option>
                      {(banlists?.results ?? []).map((b) => <option key={b.uuid} value={b.uuid}>{b.name}</option>)}
                    </select>
                  </Field>
                </>
              )}

              {step === 6 && (
                <>
                  <StepTitle icon={Check} title="Tudo certo?" help="Confira o resumo e crie o campeonato. Você ainda pode ajustar tudo antes de abrir as inscrições." />
                  <div className="grid gap-1.5 text-sm">
                    <Summary label="Nome" value={str("name") || "—"} />
                    <Summary label="Formato" value={FORMAT_KINDS.find((f) => f.v === cfg.format_kind)?.label ?? ""} />
                    <Summary label="Time" value={`${num("decks_per_player")} decks · limite de força ${num("power_cap")}`} />
                    <Summary label="Deck na partida" value={SELECTION_MODE_LABEL[str("deck_selection_mode")]} />
                    <Summary label="Ace" value={cfg.ace_enabled ? (ACE_RULES.find((r) => r.v === cfg.ace_rule)?.label ?? "Sim") : "Sem Ace"} />
                    <Summary label="Times visíveis" value={VISIBILITY.find((v) => v.v === cfg.roster_visibility)?.label ?? ""} />
                  </div>
                </>
              )}
            </motion.div>
          </AnimatePresence>

          {/* Nav */}
          <div className="mt-6 flex items-center justify-between border-t-2 border-[var(--color-border)] pt-4">
            <Button variant="ghost" disabled={step === 0} onClick={back}><ArrowLeft className="h-4 w-4" /> Voltar</Button>
            {step < steps.length - 1 ? (
              <Button disabled={!stepValid} onClick={next}>Continuar <ArrowRight className="h-4 w-4" /></Button>
            ) : (
              <Button loading={create.isPending} onClick={() => create.mutate()}><Check className="h-4 w-4" /> Criar campeonato</Button>
            )}
          </div>
        </Panel>

        {/* Live preview */}
        <div className="hidden lg:block">
          <div className="sticky top-20 space-y-3">
            <Panel className="overflow-hidden p-0">
              <div className="relative aspect-[16/9] bg-[var(--color-surface-3)]">
                {str("image") ? <img src={str("image")} alt="" className="h-full w-full object-cover" /> : (
                  <div className="grid h-full w-full place-items-center text-[var(--color-ink-subtle)]"><Trophy className="h-8 w-8" /></div>
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent" />
                <p className="absolute inset-x-0 bottom-0 truncate p-3 font-display text-lg text-white">{str("name") || "Seu campeonato"}</p>
              </div>
              <div className="p-3 text-[11px] text-[var(--color-ink-muted)]">
                {num("decks_per_player")} decks por jogador · {SELECTION_MODE_LABEL[str("deck_selection_mode")]}
                {cfg.ace_enabled ? " · com Ace" : ""}
              </div>
            </Panel>
            <CapMeter used={0} cap={num("power_cap")} />
          </div>
        </div>
      </div>
    </div>
  );
}

const inputCls = "w-full rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="font-display mb-1 block text-[10px] uppercase tracking-wide text-[var(--color-ink-muted)]">{label}</span>
      {children}
    </label>
  );
}

function StepTitle({ icon: Icon, title, help }: { icon: typeof Trophy; title: string; help: string }) {
  return (
    <div>
      <h2 className="font-display flex items-center gap-2 text-lg"><Icon className="h-5 w-5 text-[var(--color-accent)]" /> {title}</h2>
      <p className="mt-1 text-[13px] leading-relaxed text-[var(--color-ink-muted)]">{help}</p>
    </div>
  );
}

function OptionCard({ active, onClick, icon, label, help }: { active: boolean; onClick: () => void; icon: React.ReactNode; label: string; help: string }) {
  return (
    <button onClick={onClick}
      className={cn("flex items-start gap-3 rounded-[var(--radius-card)] border-2 p-3 text-left transition-colors",
        active ? "border-[var(--color-accent)] bg-[var(--color-accent)]/10" : "border-[var(--color-border)] bg-[var(--color-surface-2)] hover:border-[var(--color-accent)]/60")}>
      <span className={cn("mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-full", active ? "bg-[var(--color-accent)]/20 text-[var(--color-accent)]" : "bg-[var(--color-surface-3)] text-[var(--color-ink-muted)]")}>{icon}</span>
      <span className="min-w-0">
        <span className="font-display block text-sm">{label}</span>
        <span className="block text-[12px] leading-snug text-[var(--color-ink-muted)]">{help}</span>
      </span>
      {active && <Check className="ml-auto h-4 w-4 shrink-0 text-[var(--color-accent)]" />}
    </button>
  );
}

function Summary({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-3 rounded-[6px] bg-[var(--color-surface-2)] px-3 py-1.5">
      <span className="text-[var(--color-ink-muted)]">{label}</span>
      <span className="font-display text-right">{value}</span>
    </div>
  );
}
