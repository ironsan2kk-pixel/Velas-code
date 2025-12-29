import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface SettingsState {
  // Direct state fields
  sidebarCollapsed: boolean;
  showProfitInPercent: boolean;
  compactMode: boolean;
  soundEnabled: boolean;
  notificationsEnabled: boolean;
  // Actions
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleSidebar: () => void;
  setShowProfitInPercent: (show: boolean) => void;
  setCompactMode: (compact: boolean) => void;
  setSoundEnabled: (enabled: boolean) => void;
  setNotificationsEnabled: (enabled: boolean) => void;
  resetSettings: () => void;
}

const defaultSettings = {
  sidebarCollapsed: false,
  showProfitInPercent: true,
  compactMode: false,
  soundEnabled: true,
  notificationsEnabled: true,
};

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      // Initial state
      ...defaultSettings,
      
      setSidebarCollapsed: (collapsed) =>
        set({ sidebarCollapsed: collapsed }),
      
      toggleSidebar: () =>
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      
      setShowProfitInPercent: (show) =>
        set({ showProfitInPercent: show }),
      
      setCompactMode: (compact) =>
        set({ compactMode: compact }),
      
      setSoundEnabled: (enabled) =>
        set({ soundEnabled: enabled }),
      
      setNotificationsEnabled: (enabled) =>
        set({ notificationsEnabled: enabled }),
      
      resetSettings: () =>
        set(defaultSettings),
    }),
    {
      name: 'velas-settings',
    }
  )
);

export default useSettingsStore;
