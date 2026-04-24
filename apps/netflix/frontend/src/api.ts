import axios, { type InternalAxiosRequestConfig } from 'axios';

const API_BASE = '/api';

const api = axios.create({ baseURL: API_BASE });

// Attach JWT token to all requests
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('netflix_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Error boundary logging
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('[Netflix API Error]:', error.response || error.message);
    return Promise.reject(error);
  }
);

export interface ContentItem {
  id: number; title: string; description: string; category: string;
  youtube_id: string; thumbnail_url: string; release_year: number;
  rating: number; duration_minutes: number; maturity_rating: string; tags: string[];
}

export interface CategoryGroup { category: string; items: ContentItem[]; total: number; }
export interface User { id: number; email: string; display_name: string; avatar_url: string | null; created_at: string; }
export interface AuthResponse { access_token: string; token_type: string; user: User; }

export const authApi = {
  login: (email: string, password: string) =>
    api.post<AuthResponse>('/auth/login', { email, password }),
  register: (email: string, password: string, display_name: string) =>
    api.post<AuthResponse>('/auth/register', { email, password, display_name }),
};

export const contentApi = {
  browse: () => api.get<CategoryGroup[]>('/content/browse'),
  featured: () => api.get<ContentItem[]>('/content/featured'),
  get: (id: number) => api.get<ContentItem>(`/content/${id}`),
  categories: () => api.get<{category: string; count: number}[]>('/content/categories'),
};

export const searchApi = {
  search: (q: string) => api.get<ContentItem[]>(`/search?q=${encodeURIComponent(q)}`),
};

export const streamApi = {
  play: (content_id: number) => api.post('/stream/play', { content_id }),
};

export const recommendApi = {
  forItem: (id: number) => api.get<ContentItem[]>(`/recommend/item/${id}`),
  trending: () => api.get<ContentItem[]>('/recommend/trending'),
};

export default api;
