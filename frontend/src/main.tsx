import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

// Initialize theme from localStorage before render
const initTheme = () => {
  const stored = localStorage.getItem('velas-theme');
  if (stored) {
    try {
      const { state } = JSON.parse(stored);
      const isDark = state?.isDark ?? true;
      document.documentElement.classList.toggle('dark', isDark);
      document.documentElement.classList.toggle('light', !isDark);
      // Update meta theme color
      const meta = document.querySelector('meta[name="theme-color"]');
      if (meta) {
        meta.setAttribute('content', isDark ? '#0d1117' : '#ffffff');
      }
    } catch {
      document.documentElement.classList.add('dark');
    }
  } else {
    // Default to dark theme
    document.documentElement.classList.add('dark');
  }
};

initTheme();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
