/** Presentation metadata for card attributes — labels + token colors. */

export const GRADE_COLORS: Record<number, string> = {
  0: "var(--color-grade-0)",
  1: "var(--color-grade-1)",
  2: "var(--color-grade-2)",
  3: "var(--color-grade-3)",
  4: "var(--color-grade-4)",
};

export const NATION_LABELS: Record<string, string> = {
  dragon_empire: "Dragon Empire",
  dark_states: "Dark States",
  brandt_gate: "Brandt Gate",
  keter_sanctuary: "Keter Sanctuary",
  stoicheia: "Stoicheia",
  lyrical_monasterio: "Lyrical Monasterio",
  united_sanctuary: "United Sanctuary",
  dark_zone: "Dark Zone",
  magallanica: "Magallanica",
  zoo: "Zoo",
  star_gate: "Star Gate",
};

export const NATION_COLORS: Record<string, string> = {
  dragon_empire: "#ff6b6b",
  dark_states: "#b07bff",
  brandt_gate: "#ffcf4a",
  keter_sanctuary: "#56d7e6",
  stoicheia: "#66e08a",
  lyrical_monasterio: "#ff9ecb",
  united_sanctuary: "#ffd25c",
  dark_zone: "#8a90b8",
  magallanica: "#56d7e6",
  zoo: "#66e08a",
  star_gate: "#b07bff",
};

export const CARD_TYPE_LABELS: Record<string, string> = {
  normal_unit: "Normal Unit",
  trigger_unit: "Trigger Unit",
  g_unit: "G Unit",
  order: "Order",
  set_order: "Set Order",
  blitz_order: "Blitz Order",
  token: "Token",
};

export const TRIGGER_LABELS: Record<string, string> = {
  critical: "Critical",
  draw: "Draw",
  front: "Front",
  heal: "Heal",
  stand: "Stand",
  over: "Over",
};

export const TRIGGER_COLORS: Record<string, string> = {
  critical: "var(--color-danger)",
  draw: "var(--color-info)",
  front: "var(--color-warning)",
  heal: "var(--color-success)",
  stand: "var(--color-brand-400)",
  over: "var(--color-violet)",
};

export function nationLabel(v: string): string {
  return NATION_LABELS[v] ?? "—";
}
export function cardTypeLabel(v: string): string {
  return CARD_TYPE_LABELS[v] ?? v;
}
