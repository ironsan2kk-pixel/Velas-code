/**
 * VELAS Desktop - Electron Main Process
 */

const { app, BrowserWindow, Tray, Menu, ipcMain, shell, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');

const isDev = !app.isPackaged;
const BACKEND_PORT = 8000;
const FRONTEND_PORT = isDev ? 5173 : null;

let mainWindow = null;
let tray = null;
let pythonProcess = null;
let isQuitting = false;

function getResourcePath(relativePath) {
  if (isDev) {
    return path.join(__dirname, '..', relativePath);
  }
  return path.join(process.resourcesPath, relativePath);
}

function checkBackend() {
  return new Promise((resolve) => {
    const req = http.get(`http://localhost:${BACKEND_PORT}/api/health`, (res) => {
      resolve(res.statusCode === 200);
    });
    req.on('error', () => resolve(false));
    req.setTimeout(1000, () => {
      req.destroy();
      resolve(false);
    });
  });
}

async function waitForBackend(maxAttempts = 30) {
  for (let i = 0; i < maxAttempts; i++) {
    if (await checkBackend()) {
      console.log('Backend is ready');
      return true;
    }
    await new Promise(r => setTimeout(r, 1000));
    console.log(`Waiting for backend... (${i + 1}/${maxAttempts})`);
  }
  return false;
}

function startBackend() {
  return new Promise((resolve, reject) => {
    const backendPath = getResourcePath('backend');
    const pythonPath = process.platform === 'win32' ? 'python' : 'python3';
    
    console.log('Starting Python backend...');
    console.log('Path:', backendPath);
    
    pythonProcess = spawn(pythonPath, [
      '-m', 'uvicorn',
      'api.main:app',
      '--host', '0.0.0.0',
      '--port', String(BACKEND_PORT),
    ], {
      cwd: backendPath,
      stdio: ['ignore', 'pipe', 'pipe'],
      env: { ...process.env, PYTHONUNBUFFERED: '1' }
    });
    
    pythonProcess.stdout.on('data', (data) => {
      console.log(`[Backend] ${data.toString().trim()}`);
    });
    
    pythonProcess.stderr.on('data', (data) => {
      console.error(`[Backend] ${data.toString().trim()}`);
    });
    
    pythonProcess.on('error', (err) => {
      console.error('Failed to start backend:', err);
      reject(err);
    });
    
    pythonProcess.on('exit', (code) => {
      console.log(`Backend exited with code ${code}`);
      if (!isQuitting) {
        setTimeout(() => startBackend(), 3000);
      }
    });
    
    waitForBackend().then((ready) => {
      if (ready) resolve();
      else reject(new Error('Backend failed to start'));
    });
  });
}

function stopBackend() {
  if (pythonProcess) {
    console.log('Stopping backend...');
    if (process.platform === 'win32') {
      spawn('taskkill', ['/pid', pythonProcess.pid, '/f', '/t']);
    } else {
      pythonProcess.kill('SIGTERM');
    }
    pythonProcess = null;
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 768,
    title: 'VELAS Trading System',
    icon: path.join(__dirname, '../frontend/public/icons/icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    show: false,
    backgroundColor: '#0d1117'
  });
  
  if (isDev) {
    mainWindow.loadURL(`http://localhost:${FRONTEND_PORT}`);
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../frontend/dist/index.html'));
  }
  
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });
  
  mainWindow.on('close', (event) => {
    if (!isQuitting) {
      event.preventDefault();
      mainWindow.hide();
    }
  });
  
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
  
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
}

function createTray() {
  const iconPath = path.join(__dirname, '../frontend/public/icons/icon.png');
  try {
    tray = new Tray(iconPath);
  } catch (e) {
    console.log('Tray icon not found, skipping');
    return;
  }
  
  const contextMenu = Menu.buildFromTemplate([
    { label: 'Open VELAS', click: () => { if (mainWindow) { mainWindow.show(); mainWindow.focus(); } } },
    { type: 'separator' },
    { label: 'Restart Backend', click: async () => { stopBackend(); await startBackend(); } },
    { type: 'separator' },
    { label: 'Exit', click: () => { isQuitting = true; app.quit(); } }
  ]);
  
  tray.setToolTip('VELAS Trading System');
  tray.setContextMenu(contextMenu);
  tray.on('double-click', () => { if (mainWindow) { mainWindow.show(); mainWindow.focus(); } });
}

function setupIPC() {
  ipcMain.handle('backend:status', async () => await checkBackend());
  ipcMain.handle('backend:restart', async () => { stopBackend(); await startBackend(); return true; });
  ipcMain.handle('app:info', () => ({ version: app.getVersion(), isDev, platform: process.platform }));
  ipcMain.on('notification:show', (event, { title, body }) => {
    const { Notification } = require('electron');
    new Notification({ title, body }).show();
  });
}

app.whenReady().then(async () => {
  console.log('VELAS Desktop starting...');
  
  try {
    await startBackend();
    createWindow();
    createTray();
    setupIPC();
    console.log('VELAS Desktop ready');
  } catch (err) {
    console.error('Startup failed:', err);
    dialog.showErrorBox('Startup Error',
      'Failed to start VELAS Trading System.\n\n' +
      'Make sure Python 3.11+ is installed and available in PATH.\n\n' +
      `Error: ${err.message}`
    );
    app.quit();
  }
});

app.on('activate', () => { if (mainWindow === null) createWindow(); else mainWindow.show(); });
app.on('window-all-closed', () => { /* minimize to tray */ });
app.on('before-quit', () => { isQuitting = true; stopBackend(); });

const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.show();
      mainWindow.focus();
    }
  });
}
