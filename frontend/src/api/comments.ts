import { api } from "@/lib/api";
import type { Paginated } from "./types";

export type CommentTarget = "deck" | "banlist" | "card" | "tournament" | "profile";

export interface CommentAuthor {
  uuid: string;
  username: string;
  display_name: string;
  avatar_key: string;
  is_platform_admin: boolean;
}

export interface Comment {
  uuid: string;
  target_type: CommentTarget;
  target_uuid: string;
  author: CommentAuthor;
  body: string;
  can_delete: boolean;
  created_at: string;
}

export const commentsApi = {
  async list(targetType: CommentTarget, targetUuid: string) {
    const { data } = await api.get<Paginated<Comment>>("/comments/", {
      params: { target_type: targetType, target_uuid: targetUuid, page_size: 100 },
    });
    return data.results;
  },
  async create(targetType: CommentTarget, targetUuid: string, body: string) {
    const { data } = await api.post<Comment>("/comments/", {
      target_type: targetType,
      target_uuid: targetUuid,
      body,
    });
    return data;
  },
  async remove(uuid: string) {
    await api.delete(`/comments/${uuid}/`);
  },
};
