// ── Roles ────────────────────────────────────────────────────────────────
export type Role = 'visitor' | 'user' | 'supervisor' | 'admin';

// ── Auth ─────────────────────────────────────────────────────────────────
export interface AuthUser {
  id: number;
  username: string;
  email: string;
  role: Role;
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

// ── Albums ────────────────────────────────────────────────────────────────
export type AlbumStatus = 'pending' | 'approved' | 'rejected';

export interface Album {
  id: number;
  title: string;
  description: string | null;
  privacy: 'public' | 'private';
  status: AlbumStatus;
  user_id: number;
  created_at: string;
  updated_at: string;
  reviewed_by: number | null;
  reviewed_at: string | null;
  rejection_reason: string | null;
}

// ── Images ─────────────────────────────────────────────────────────────────
export type ImageStatus = 'CLEAN' | 'SUSPICIOUS' | 'APPROVED_MANUAL' | 'REJECTED';

export interface StegAnalysis {
  result: 'CLEAN' | 'SUSPICIOUS' | 'ERROR';
  is_suspicious: boolean;
  dimensions?: string;
  format?: string;
  lsb_ratio?: number;
  histogram_pair_diff?: number;
  lsb_suspicious?: boolean;
  histogram_suspicious?: boolean;
  entropy_suspicious?: boolean;
  zone_analysis?: Record<'start' | 'middle' | 'end', {
    e1?: number;
    e2?: number;
    r1?: number;
    r2?: number;
  }>;
  diagnosis?: string;
}

export interface GalleryImage {
  id: number;
  original_filename: string;
  stored_filename: string;
  status: ImageStatus;
  steg_result: StegAnalysis | null;
  album_id: number;
  user_id: number;
  created_at: string;
  reviewed_at?: string | null;
}
