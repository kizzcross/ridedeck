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
}
export interface TournamentDetail extends TournamentListItem {
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
  power_policy: { uuid: string; kind: string; name: string } | null;
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
