export type Role = "user" | "supervisor" | "admin";

export interface User {
  id: number;
  username: string;
  email: string;
  role: Role;
}

export interface AuthToken {
  access_token: string;
  token_type: "bearer";
  user: User;
}

export type AlbumStatus = "pending" | "approved" | "rejected";
export type AlbumPrivacy = "public" | "private";

export interface Album {
  id: number;
  title: string;
  description: string;
  privacy: AlbumPrivacy;
  status: AlbumStatus;
  user_id: number;
  created_at: string;
  updated_at: string;
  reviewed_by?: number | null;
  reviewed_at?: string | null;
  rejection_reason?: string | null;
}

export interface AlbumCreatePayload {
  title: string;
  description: string;
  privacy: AlbumPrivacy;
}
