import { create } from 'zustand';

interface Notification { id: string; severity: string; title: string; description: string; is_read: boolean; created_at: string; source: string; }
interface NotifState {
  notifications: Notification[];
  unreadCount: number;
  addNotification: (n: Notification) => void;
  markRead: (id: string) => void;
  clearAll: () => void;
}

export const useNotificationStore = create<NotifState>((set) => ({
  notifications: [],
  unreadCount: 0,
  addNotification: (n) => set((s) => ({
    notifications: [n, ...s.notifications].slice(0, 100),
    unreadCount: s.unreadCount + (n.is_read ? 0 : 1),
  })),
  markRead: (id) => set((s) => ({
    notifications: s.notifications.map(n => n.id === id ? {...n, is_read: true} : n),
    unreadCount: Math.max(0, s.unreadCount - 1),
  })),
  clearAll: () => set({ notifications: [], unreadCount: 0 }),
}));