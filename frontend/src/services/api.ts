import axios from 'axios';
import type { AuthUser, TokenResponse, Album, GalleryImage } from '../types';

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api';

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

  logout: () => {
    localStorage.removeItem('access_token');
    window.location.href = '/login';
  },
};

// ── Albums ────────────────────────────────────────────────────────────────
export const albumsApi = {
  requestAlbum: (data: { title: string; description?: string }) =>
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

  quarantine: () => api.get<GalleryImage[]>('/quarantine'),

  approveQuarantine: (imageId: number) =>
    api.patch<GalleryImage>(`/quarantine/${imageId}/approve`),

  rejectQuarantine: (imageId: number) =>
    api.patch<GalleryImage>(`/quarantine/${imageId}/reject`),

  deleteImage: (albumId: number, imageId: number) =>
    api.delete(`/albums/${albumId}/images/${imageId}`),
};
