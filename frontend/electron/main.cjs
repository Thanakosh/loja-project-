const { app, BrowserWindow } = require('electron');
const path = require('path');

const isDev = !app.isPackaged;

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 1024,
    minHeight: 720,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  if (isDev) {
    const configuredDevServerUrl = process.env.ELECTRON_START_URL;
    const isLocalDevServer =
      configuredDevServerUrl && /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?(\/|$)/i.test(configuredDevServerUrl);
    if (configuredDevServerUrl && !isLocalDevServer) {
      console.warn('Ignoring ELECTRON_START_URL because it is not a localhost URL.');
    }
    const devServerUrl = isLocalDevServer ? configuredDevServerUrl : 'http://localhost:5173';
    mainWindow.loadURL(devServerUrl);
    mainWindow.webContents.openDevTools({ mode: 'detach' });
  } else {
    mainWindow.loadFile(path.join(app.getAppPath(), 'dist', 'index.html'));
  }
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
