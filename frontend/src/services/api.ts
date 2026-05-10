import axios from 'axios';
import type { AuthUser, TokenResponse, Album, GalleryImage } from '../types';

const BASE_URL = import.meta.env.VITE_API_URL ?? '/api';

const api = axios.create({ baseURL: BASE_URL });

// ── JWT interceptor ───────────────────────────────────────────────────────
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  },
);

// ── Auth ──────────────────────────────────────────────────────────────────
export const authApi = {
  register: (data: { username: string; email: string; password: string }) =>
    api.post<AuthUser>('/auth/register', data),

  login: async (username: string, password: string): Promise<string> => {
    const res = await api.post<TokenResponse>('/auth/login', { username, password });
    const token = res.data.access_token;
    localStorage.setItem('access_token', token);
    return token;
  },

  me: () => api.get<AuthUser>('/auth/me'),

  logout: async () => {
    try {
      await api.post('/auth/logout');
    } catch {
      // Local logout must still complete if the token is already invalid.
    }
    localStorage.removeItem('access_token');
    window.location.href = '/login';
  },
};

export function getApiErrorMessage(error: unknown, fallback = 'No se pudo completar la solicitud'): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') return cleanApiMessage(detail);
    if (Array.isArray(detail)) {
      return detail.map((item) => cleanApiMessage(item?.msg ?? JSON.stringify(item))).join(' ');
    }
  }
  return fallback;
}

function cleanApiMessage(message: string): string {
  return message
    .replace(/^Value error,\s*/i, '')
    .replace(/^Input should be a valid string\s*/i, 'Ingresa un texto válido.')
    .replace(/^String should have at least (\d+) characters/i, 'Debe tener al menos $1 caracteres')
    .replace(/^String should have at most (\d+) characters/i, 'Debe tener máximo $1 caracteres')
    .trim();
}

// ── Albums ────────────────────────────────────────────────────────────────
export const albumsApi = {
  requestAlbum: (data: { title: string; description?: string; privacy?: 'public' | 'private' }) =>
    api.post<Album>('/albums/request', data),

  myAlbums: () => api.get<Album[]>('/albums/my'),

  publicAlbums: () => api.get<Album[]>('/albums/public'),

  pendingAlbums: () => api.get<Album[]>('/albums/pending'),

  reviewAlbum: (albumId: number, action: 'approve' | 'reject') =>
    api.patch<Album>(`/albums/${albumId}/review`, { action }),
};

// ── Images ────────────────────────────────────────────────────────────────
export const imagesApi = {
  upload: (albumId: number, file: File) => {
    const form = new FormData();
    form.append('file', file);
    return api.post<GalleryImage>(`/albums/${albumId}/images`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  albumImages: (albumId: number) =>
    api.get<GalleryImage[]>(`/albums/${albumId}/images`),

  imageUrl: (storedFilename: string) =>
    `${BASE_URL}/images/${storedFilename}`,

  presignedUrl: (imageId: number) =>
    api.get<{ url: string }>(`/images/url/${imageId}`),

  quarantine: () => api.get<GalleryImage[]>('/quarantine'),

  approveQuarantine: (imageId: number) =>
    api.patch<GalleryImage>(`/quarantine/${imageId}/approve`),

  rejectQuarantine: (imageId: number) =>
    api.patch<GalleryImage>(`/quarantine/${imageId}/reject`),

  deleteImage: (albumId: number, imageId: number) =>
    api.delete(`/albums/${albumId}/images/${imageId}`),
};
