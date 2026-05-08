// ── Roles ────────────────────────────────────────────────────────────────
export type Role = 'visitor' | 'user' | 'supervisor';

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
}

// ── Albums ────────────────────────────────────────────────────────────────
export type AlbumStatus = 'PENDING' | 'APPROVED' | 'REJECTED';

export interface Album {
  id: number;
  title: string;
  description: string | null;
  status: AlbumStatus;
  owner_id: number;
  created_at: string;
  reviewed_at: string | null;
}

// ── Images ─────────────────────────────────────────────────────────────────
export type ImageStatus = 'CLEAN' | 'QUARANTINED' | 'APPROVED_MANUAL' | 'REJECTED';

export interface StegAnalysis {
  result: 'CLEAN' | 'SUSPICIOUS' | 'ERROR';
  is_suspicious: boolean;
  dimensions?: string;
  lsb_ratio?: number;
  lsb_suspicious?: boolean;
  histogram_suspicious?: boolean;
  entropy_suspicious?: boolean;
  diagnosis?: string;
}

export interface GalleryImage {
  id: number;
  original_filename: string;
  stored_filename: string;
  mime_type: string;
  file_size: number;
  status: ImageStatus;
  steg_result: StegAnalysis | null;
  album_id: number;
  owner_id: number;
  created_at: string;
  reviewed_at?: string | null;
}
