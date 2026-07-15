import { create } from 'zustand';

export interface ChatMessage {
  id: string;
  role: 'student' | 'tutor';
  content: string;
  timestamp: string;
}

interface ChatState {
  sessionId: string | null;
  conceptName: string | null;
  messages: ChatMessage[];
  setSession: (sessionId: string, conceptName: string) => void;
  addMessage: (message: ChatMessage) => void;
  clearSession: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  sessionId: null,
  conceptName: null,
  messages: [],
  setSession: (sessionId, conceptName) => set({ sessionId, conceptName, messages: [] }),
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  clearSession: () => set({ sessionId: null, conceptName: null, messages: [] }),
}));
