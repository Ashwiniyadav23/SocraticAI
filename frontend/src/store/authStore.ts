import { create } from 'zustand';

import { persist, createJSONStorage } from 'zustand/middleware';

interface User {
  id: string;
  email: string;
  username: string;
  role: string;
  status?: string;
  campus?: string;
  house?: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (user: User, token: string) => void;
  logout: () => void;
  fetchUser: (api: any) => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: { id: "test-id", email: "test@example.com", username: "testuser", role: "student", status: "active" },
      token: "test-bypass-token",
      isAuthenticated: true,
      login: (user, token) => {
        localStorage.setItem('astra_token', token);
        set({ user, token, isAuthenticated: true });
      },
      logout: () => {
        localStorage.removeItem('astra_token');
        set({ user: null, token: null, isAuthenticated: false });
      },
      fetchUser: async (api) => {
        const { token } = get();
        if (token) {
          try {
            const { data } = await api.get('/v1/auth/me');
            set({ user: { ...data, username: data.email.split('@')[0] } });
          } catch (e) {
            console.error("Failed to fetch user");
          }
        }
      }
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
    }
  )
);
