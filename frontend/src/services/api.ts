import axios from "axios";
import type { Album, AlbumCreatePayload, AlbumStatus, AuthToken, User } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
  withCredentials: true,
});

let currentAccessToken: string | null = null;

export const setAccessToken = (token: string | null) => {
  currentAccessToken = token;
};

api.interceptors.request.use((config) => {
  if (currentAccessToken) {
    config.headers.Authorization = `Bearer ${currentAccessToken}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      originalRequest.url &&
      !originalRequest.url.includes("/auth/login") &&
      !originalRequest.url.includes("/auth/refresh")
    ) {
      originalRequest._retry = true;
      try {
        const { data } = await axios.post<AuthToken>(
          `${API_BASE_URL}/auth/refresh`,
          {},
          { withCredentials: true }
        );
        setAccessToken(data.access_token);
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        setAccessToken(null);
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);

export async function login(username: string, password: string): Promise<AuthToken> {
  const { data } = await api.post<AuthToken>("/auth/login", { username, password });
  return data;
}

export async function logoutRequest(): Promise<void> {
  await api.post("/auth/logout");
}

export async function register(username: string, email: string, password: string): Promise<User> {
  const { data } = await api.post<User>("/auth/register", { username, email, password });
  return data;
}

export async function fetchMe(): Promise<User> {
  const { data } = await api.get<User>("/auth/me");
  return data;
}

export async function requestAlbum(payload: AlbumCreatePayload): Promise<Album> {
  const { data } = await api.post<Album>("/albums/request", payload);
  return data;
}

export async function fetchMyAlbums(status?: AlbumStatus): Promise<Album[]> {
  const { data } = await api.get<Album[]>("/albums/my", { params: { status } });
  return data;
}

export async function fetchPublicAlbums(): Promise<Album[]> {
  const { data } = await api.get<Album[]>("/albums/public");
  return data;
}

export async function fetchSupervisorAlbums(status?: AlbumStatus): Promise<Album[]> {
  const { data } = await api.get<Album[]>("/albums/supervisor", { params: { status } });
  return data;
}

export async function approveAlbum(albumId: number): Promise<Album> {
  const { data } = await api.patch<Album>(`/albums/${albumId}/approve`);
  return data;
}

export async function rejectAlbum(albumId: number, rejection_reason?: string): Promise<Album> {
  const { data } = await api.patch<Album>(`/albums/${albumId}/reject`, { rejection_reason });
  return data;
}
