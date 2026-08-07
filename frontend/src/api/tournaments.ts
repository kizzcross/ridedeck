import { api } from "@/lib/api";
import type { Paginated } from "./types";

export type TournamentStatus =
  | "draft" | "registration" | "locked" | "check_in" | "running" | "finished" | "cancelled";

export interface UserMini {
  uuid: string;
  username: string;
  avatar_key: string;
}
export interface TournamentListItem {
  uuid: string;
  name: string;
  image: string;
  format_code: string;
  bracket_type: string;
  status: TournamentStatus;
  visibility: string;
  is_online: boolean;
  starts_at: string | null;
  max_participants: number;
  organizer: UserMini;
  participant_count: number;
  kind: "standard" | "roster";
  format_kind: "points" | "bracket" | "hybrid";
}

export type DeckSelectionMode =
  | "manual" | "random_free" | "random_no_consecutive" | "random_rotation"
  | "predetermined_order" | "choose_from_random";
export type AceRule =
  | "manual_once" | "replace_draw" | "weighted_random" | "extra_in_rotation"
  | "tiebreak_wins" | "visual_only";

export interface RosterConfig {
  decks_per_player: number;
  power_cap: number;
  min_deck_power: number | null;
  max_deck_power: number | null;
  deck_selection_mode: DeckSelectionMode;
  random_options_count: number;
  roster_visibility: "open" | "partial" | "closed";
  ace_enabled: boolean;
  ace_rule: AceRule;
  ace_reveal: "public" | "hidden_until_first_use";
  ace_required: boolean;
}

export interface RosterDeck {
  uuid: string;
  deck_uuid: string | null;
  label: string;
  power: number | null;
  suggested_power: number | null;
  is_ace: boolean;
  banlist_valid: boolean;
  is_valid: boolean;
  slot: number;
  order_index: number;
  locked: boolean;
  cover_image: string | null;
}
export type RosterStatus = "draft" | "valid" | "invalid" | "confirmed" | "locked";
export interface Roster {
  uuid: string;
  participant: Participant;
  status: RosterStatus;
  power_used: number;
  is_over_cap: boolean;
  power_cap: number;
  decks_per_player: number;
  confirmed_at: string | null;
  decks: RosterDeck[];
}
export interface TournamentPreset {
  code: string;
  name: string;
  description: string;
  config: Record<string, unknown>;
}

export interface SelectionDeck {
  uuid: string;
  label: string;
  is_ace: boolean;
  cover_image: string | null;
}
export interface RosterMatchSelection {
  participant_uuid: string;
  method: string;
  confirmed: boolean;
  revealed: boolean;
  is_ace_used: boolean;
  deck: SelectionDeck | null;
  options: SelectionDeck[];
}
export interface RosterMatch {
  uuid: string;
  position: number;
  table_number: number | null;
  state: "pending" | "reported" | "disputed" | "bye" | "done";
  participant_a: Participant | null;
  participant_b: Participant | null;
  winner_uuid: string | null;
  score_a: number;
  score_b: number;
  selections: RosterMatchSelection[];
}
export interface RosterRound {
  uuid: string;
  number: number;
  name: string;
  status: string;
  matches: RosterMatch[];
}

export interface RosterDeckStat {
  label: string;
  is_ace: boolean;
  power: number | null;
  wins: number;
  losses: number;
  games: number;
  win_rate: number | null;
}
export interface RosterStandingRow {
  rank: number;
  participant: UserMini;
  points: number;
  wins: number;
  losses: number;
  draws: number;
  ace_wins: number;
  penalties: number;
  decks: RosterDeckStat[];
}

export interface TournamentDetail extends TournamentListItem, RosterConfig {
  description: string;
  invite_code: string;
  timezone: string;
  location: string;
  online_link: string;
  auto_approve: boolean;
  requires_decklist: boolean;
  requires_checkin: boolean;
  best_of: number;
  prizes: string;
  contact: string;
  banlist_uuid: string | null;
  banlist_version_number: number | null;
  is_organizer: boolean;
  my_registration: { status: string } | null;
}

export interface Participant {
  uuid: string;
  user: UserMini;
  seed: number | null;
  status: string;
  wins: number;
  losses: number;
  final_rank: number | null;
  checked_in: boolean;
  has_submission: boolean;
}
export interface Match {
  uuid: string;
  position: number;
  table_number: number | null;
  room: string;
  state: "pending" | "reported" | "disputed" | "bye" | "done";
  best_of: number;
  score_a: number;
  score_b: number;
  participant_a: Participant | null;
  participant_b: Participant | null;
  winner_uuid: string | null;
  next_match: number | null;
  next_slot: string;
}
export interface Round {
  uuid: string;
  number: number;
  name: string;
  status: string;
  matches: Match[];
}
export interface Stage {
  uuid: string;
  kind: string;
  name: string;
  status: string;
  rounds: Round[];
}
export interface Registration {
  uuid: string;
  user: UserMini;
  status: string;
  note: string;
  created_at: string;
}
export interface Standing {
  rank: number;
  wins: number;
  losses: number;
  draws: number;
  points: number;
  participant: Participant;
  tiebreaks?: { omw?: number; gw?: number; ogw?: number };
}
export interface Submission {
  uuid: string;
  content_hash: string;
  is_valid: boolean;
  locked: boolean;
  validation: { is_valid: boolean; errors: { code: string; message: string }[]; warnings: { message: string }[] };
  created_at: string;
}

export const tournamentsApi = {
  async list(params: Record<string, string | number | undefined> = {}) {
    const { data } = await api.get<Paginated<TournamentListItem>>("/tournaments/", {
      params: { page_size: 40, ...params },
    });
    return data;
  },
  async detail(uuid: string) {
    const { data } = await api.get<TournamentDetail>(`/tournaments/${uuid}/`);
    return data;
  },
  async create(payload: Record<string, unknown>) {
    const { data } = await api.post<TournamentDetail>("/tournaments/", payload);
    return data;
  },
  async remove(uuid: string) {
    await api.delete(`/tournaments/${uuid}/`);
  },
  async update(uuid: string, payload: Record<string, unknown>) {
    const { data } = await api.patch<TournamentDetail>(`/tournaments/${uuid}/`, payload);
    return data;
  },
  action: async (uuid: string, verb: string, body?: unknown) => {
    const { data } = await api.post(`/tournaments/${uuid}/${verb}/`, body ?? {});
    return data;
  },
  async participants(uuid: string) {
    const { data } = await api.get<Participant[]>(`/tournaments/${uuid}/participants/`);
    return data;
  },
  async registrations(uuid: string) {
    const { data } = await api.get<Registration[]>(`/tournaments/${uuid}/registrations/`);
    return data;
  },
  async bracket(uuid: string) {
    const { data } = await api.get<Stage[]>(`/tournaments/${uuid}/bracket/`);
    return data;
  },
  async standings(uuid: string) {
    const { data } = await api.get<Standing[]>(`/tournaments/${uuid}/standings/`);
    return data;
  },
  async submitDeck(uuid: string, deck: string) {
    const { data } = await api.post<Submission>(`/tournaments/${uuid}/submit-deck/`, { deck });
    return data;
  },
  async mySubmission(uuid: string) {
    const { data } = await api.get<Submission | { submission: null }>(`/tournaments/${uuid}/my-submission/`);
    return data;
  },
  // Roster championship
  async presets() {
    const { data } = await api.get<TournamentPreset[]>(`/tournaments/presets/`);
    return data;
  },
  async myRoster(uuid: string) {
    const { data } = await api.get<Roster | { roster: null }>(`/tournaments/${uuid}/my-roster/`);
    return data;
  },
  async rosters(uuid: string) {
    const { data } = await api.get<Roster[]>(`/tournaments/${uuid}/rosters/`);
    return data;
  },
  async addRosterDeck(uuid: string, deck: string) {
    const { data } = await api.post<Roster>(`/tournaments/${uuid}/add-roster-deck/`, { deck });
    return data;
  },
  async removeRosterDeck(uuid: string, roster_deck: string) {
    const { data } = await api.post<Roster>(`/tournaments/${uuid}/remove-roster-deck/`, { roster_deck });
    return data;
  },
  async setAce(uuid: string, roster_deck: string | null) {
    const { data } = await api.post<Roster>(`/tournaments/${uuid}/set-ace/`, { roster_deck });
    return data;
  },
  async confirmRoster(uuid: string) {
    const { data } = await api.post<Roster>(`/tournaments/${uuid}/confirm-roster/`);
    return data;
  },
  async setDeckPower(uuid: string, roster_deck: string, power: number | null) {
    const { data } = await api.post<Roster>(`/tournaments/${uuid}/set-deck-power/`, { roster_deck, power });
    return data;
  },
  async rosterRounds(uuid: string) {
    const { data } = await api.get<RosterRound[]>(`/tournaments/${uuid}/roster-rounds/`);
    return data;
  },
  async rosterStandings(uuid: string) {
    const { data } = await api.get<RosterStandingRow[]>(`/tournaments/${uuid}/roster-standings/`);
    return data;
  },
  async runDraws(uuid: string, redraw = false) {
    const { data } = await api.post(`/tournaments/${uuid}/run-draws/`, { redraw });
    return data;
  },
  async pickDeck(matchUuid: string, roster_deck: string) {
    const { data } = await api.post(`/matches/${matchUuid}/pick-deck/`, { roster_deck });
    return data;
  },
  async confirmSelection(matchUuid: string) {
    const { data } = await api.post(`/matches/${matchUuid}/confirm-selection/`);
    return data;
  },
  async useAce(matchUuid: string) {
    const { data } = await api.post(`/matches/${matchUuid}/use-ace/`);
    return data;
  },
  async applyPenalty(uuid: string, body: { participant: string; kind: string; points: number; reason: string }) {
    const { data } = await api.post(`/tournaments/${uuid}/apply-penalty/`, body);
    return data;
  },
  async penalties(uuid: string) {
    const { data } = await api.get<{ uuid: string; participant: string; kind: string; points: number; reason: string; created_at: string }[]>(`/tournaments/${uuid}/penalties/`);
    return data;
  },
  async resolveDispute(matchUuid: string, resolution: string, score_a?: number, score_b?: number) {
    const { data } = await api.post(`/matches/${matchUuid}/resolve-dispute/`, { resolution, score_a, score_b });
    return data;
  },
  async disputeMatch(matchUuid: string, reason: string) {
    const { data } = await api.post(`/matches/${matchUuid}/dispute/`, { reason });
    return data;
  },
  // Match actions
  async reportMatch(matchUuid: string, score_a: number, score_b: number) {
    const { data } = await api.post<Match>(`/matches/${matchUuid}/report/`, { score_a, score_b });
    return data;
  },
  async confirmMatch(matchUuid: string) {
    const { data } = await api.post<Match>(`/matches/${matchUuid}/confirm/`);
    return data;
  },
  async setResult(matchUuid: string, score_a: number, score_b: number) {
    const { data } = await api.post<Match>(`/matches/${matchUuid}/set-result/`, { score_a, score_b });
    return data;
  },
};
