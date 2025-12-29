import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface UISettings {
  sidebarCollapsed: boolean;
  showProfitInPercent: boolean;
  compactMode: boolean;
  soundEnabled: boolean;
  notificationsEnabled: boolean;
}

interface SettingsState {
  ui: UISettings;
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleSidebar: () => void;
  setShowProfitInPercent: (show: boolean) => void;
  setCompactMode: (compact: boolean) => void;
  setSoundEnabled: (enabled: boolean) => void;
  setNotificationsEnabled: (enabled: boolean) => void;
  resetSettings: () => void;
}

const defaultSettings: UISettings = {
  sidebarCollapsed: false,
  showProfitInPercent: true,
  compactMode: false,
  soundEnabled: true,
  notificationsEnabled: true,
};

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      ui: defaultSettings,
      
      setSidebarCollapsed: (collapsed) =>
        set((state) => ({
          ui: { ...state.ui, sidebarCollapsed: collapsed },
        })),
      
      toggleSidebar: () =>
        set((state) => ({
          ui: { ...state.ui, sidebarCollapsed: !state.ui.sidebarCollapsed },
        })),
      
      setShowProfitInPercent: (show) =>
        set((state) => ({
          ui: { ...state.ui, showProfitInPercent: show },
        })),
      
      setCompactMode: (compact) =>
        set((state) => ({
          ui: { ...state.ui, compactMode: compact },
        })),
      
      setSoundEnabled: (enabled) =>
        set((state) => ({
          ui: { ...state.ui, soundEnabled: enabled },
        })),
      
      setNotificationsEnabled: (enabled) =>
        set((state) => ({
          ui: { ...state.ui, notificationsEnabled: enabled },
        })),
      
      resetSettings: () =>
        set({ ui: defaultSettings }),
    }),
    {
      name: 'velas-settings',
    }
  )
);

export default useSettingsStore;
