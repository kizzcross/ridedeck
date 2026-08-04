import { NATION_LABELS, CARD_TYPE_LABELS, TRIGGER_LABELS } from "@/lib/cardMeta";
import { cn } from "@/lib/cn";

export interface Filters {
  grade: string;
  nation: string;
  clan: string;
  card_type: string;
  trigger: string;
  set_code: string;
  format_code: string;
}

export const EMPTY_FILTERS: Filters = {
  grade: "",
  nation: "",
  clan: "",
  card_type: "",
  trigger: "",
  set_code: "",
  format_code: "",
};

function Select({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: [string, string][];
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium text-[var(--color-ink-muted)]">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-9 w-full rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-2 text-sm text-[var(--color-ink)] focus:border-[var(--color-accent)]"
      >
        <option value="">Todos</option>
        {options.map(([v, l]) => (
          <option key={v} value={v}>
            {l}
          </option>
        ))}
      </select>
    </label>
  );
}

const GRADES: [string, string][] = [
  ["0", "Grade 0"],
  ["1", "Grade 1"],
  ["2", "Grade 2"],
  ["3", "Grade 3"],
  ["4", "Grade 4"],
];

export function CatalogFilters({
  filters,
  onChange,
  sets,
  className,
}: {
  filters: Filters;
  onChange: (f: Filters) => void;
  sets: [string, string][];
  className?: string;
}) {
  const set =
    (key: keyof Filters) =>
    (v: string): void =>
      onChange({ ...filters, [key]: v });
  const active = Object.values(filters).some(Boolean);

  return (
    <div className={cn("space-y-3", className)}>
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-[var(--color-ink-subtle)]">
          Filtros
        </h3>
        {active && (
          <button
            onClick={() => onChange(EMPTY_FILTERS)}
            className="text-xs font-medium text-[var(--color-accent)] hover:underline"
          >
            Limpar
          </button>
        )}
      </div>
      <Select label="Grade" value={filters.grade} onChange={set("grade")} options={GRADES} />
      <Select
        label="Nation"
        value={filters.nation}
        onChange={set("nation")}
        options={Object.entries(NATION_LABELS)}
      />
      <label className="block">
        <span className="mb-1 block text-xs font-medium text-[var(--color-ink-muted)]">Clan</span>
        <input
          value={filters.clan}
          onChange={(e) => onChange({ ...filters, clan: e.target.value })}
          placeholder="Ex: Royal Paladin"
          className="h-9 w-full rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-2 text-sm text-[var(--color-ink)] focus:border-[var(--color-accent)]"
        />
      </label>
      <Select
        label="Tipo"
        value={filters.card_type}
        onChange={set("card_type")}
        options={Object.entries(CARD_TYPE_LABELS)}
      />
      <Select
        label="Trigger"
        value={filters.trigger}
        onChange={set("trigger")}
        options={Object.entries(TRIGGER_LABELS)}
      />
      <Select label="Set" value={filters.set_code} onChange={set("set_code")} options={sets} />
      <Select
        label="Formato"
        value={filters.format_code}
        onChange={set("format_code")}
        options={[
          ["standard", "Standard"],
          ["v_premium", "V Premium"],
          ["premium", "Premium"],
        ]}
      />
    </div>
  );
}
