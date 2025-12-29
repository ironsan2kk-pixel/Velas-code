import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type Theme = 'dark' | 'light';

interface ThemeState {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      theme: 'dark',
      
      setTheme: (theme) => {
        set({ theme });
        updateDocumentTheme(theme);
      },
      
      toggleTheme: () => {
        const newTheme = get().theme === 'dark' ? 'light' : 'dark';
        set({ theme: newTheme });
        updateDocumentTheme(newTheme);
      },
    }),
    {
      name: 'velas-theme',
      onRehydrateStorage: () => (state) => {
        // Apply theme on hydration
        if (state?.theme) {
          updateDocumentTheme(state.theme);
        }
      },
    }
  )
);

function updateDocumentTheme(theme: Theme): void {
  const root = document.documentElement;
  if (theme === 'dark') {
    root.classList.add('dark');
    root.classList.remove('light');
  } else {
    root.classList.add('light');
    root.classList.remove('dark');
  }
  
  // Update meta theme-color for mobile browsers
  const metaThemeColor = document.querySelector('meta[name="theme-color"]');
  if (metaThemeColor) {
    metaThemeColor.setAttribute(
      'content',
      theme === 'dark' ? '#0d1117' : '#ffffff'
    );
  }
}

// Initialize theme on load
if (typeof window !== 'undefined') {
  const stored = localStorage.getItem('velas-theme');
  if (stored) {
    try {
      const { state } = JSON.parse(stored);
      if (state?.theme) {
        updateDocumentTheme(state.theme);
      }
    } catch {
      // Fallback to dark theme
      updateDocumentTheme('dark');
    }
  }
}

export default useThemeStore;
