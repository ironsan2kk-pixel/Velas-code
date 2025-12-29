/**
 * VELAS Desktop - Preload Script
 * 
 * Безопасный мост между Electron и React
 */

const { contextBridge, ipcRenderer } = require('electron');

// Expose protected APIs to renderer
contextBridge.exposeInMainWorld('electron', {
  // Backend control
  backend: {
    getStatus: () => ipcRenderer.invoke('backend:status'),
    restart: () => ipcRenderer.invoke('backend:restart'),
  },
  
  // App info
  app: {
    getInfo: () => ipcRenderer.invoke('app:info'),
  },
  
  // Notifications
  notification: {
    show: (title, body) => ipcRenderer.send('notification:show', { title, body }),
  },
  
  // Navigation listener
  onNavigate: (callback) => {
    ipcRenderer.on('navigate', (event, path) => callback(path));
  },
  
  // Platform info
  platform: process.platform,
  isElectron: true,
});

console.log('✅ VELAS preload script loaded');
