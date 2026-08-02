const { app, BrowserWindow, ipcMain, safeStorage } = require('electron');
const { spawn } = require('node:child_process');
const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

let coreProcess;
let apiBase;
let coreReady = false;
const apiToken = crypto.randomBytes(32).toString('hex');

function localDataDir() {
  if (process.env.PMGO_DATA_DIR) return path.resolve(process.env.PMGO_DATA_DIR);
  if (process.platform === 'darwin') return path.join(os.homedir(), 'Library', 'Application Support', 'pmgo');
  if (process.platform === 'win32') return path.join(process.env.LOCALAPPDATA || path.join(os.homedir(), 'AppData', 'Local'), 'pmgo');
  return path.join(process.env.XDG_DATA_HOME || path.join(os.homedir(), '.local', 'share'), 'pmgo');
}

function sourceRoot() {
  return path.resolve(__dirname, '..', '..');
}

function startCore() {
  return new Promise((resolve, reject) => {
    const packaged = app.isPackaged;
    const executable = process.platform === 'win32' ? 'pmgo-api.exe' : 'pmgo-api';
    const sidecar = path.join(process.resourcesPath, 'bin', executable);
    const command = packaged ? sidecar : (process.env.PMGO_PYTHON || 'python3');
    const args = packaged
      ? ['--data-dir', localDataDir(), '--token', apiToken]
      : ['-m', 'pmgo_app.api', '--data-dir', localDataDir(), '--token', apiToken];
    coreProcess = spawn(command, args, {
      cwd: packaged ? process.resourcesPath : sourceRoot(),
      stdio: ['ignore', 'pipe', 'pipe'],
      windowsHide: true,
    });
    let output = '';
    const timer = setTimeout(() => reject(new Error('The local pmgo core did not start in time.')), 15000);
    coreProcess.stdout.on('data', (chunk) => {
      output += chunk.toString();
      const match = output.match(/PMGO_API_READY (\d+)/);
      if (match) {
        clearTimeout(timer);
        apiBase = `http://127.0.0.1:${match[1]}`;
        coreReady = true;
        resolve();
      }
    });
    coreProcess.stderr.on('data', (chunk) => console.error(`[pmgo-core] ${chunk}`));
    coreProcess.on('error', (error) => {
      clearTimeout(timer);
      reject(error);
    });
    coreProcess.on('exit', (code) => {
      clearTimeout(timer);
      if (!coreReady) reject(new Error(`The local pmgo core exited during startup (${code}).`));
      coreReady = false;
      apiBase = undefined;
    });
  });
}

function secretPath() {
  return path.join(localDataDir(), 'provider-key.bin');
}

function saveSecret(value) {
  const file = secretPath();
  if (!value) {
    if (fs.existsSync(file)) fs.unlinkSync(file);
    return;
  }
  if (!safeStorage.isEncryptionAvailable()) throw new Error('System secure storage is unavailable.');
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, safeStorage.encryptString(value));
}

function loadSecret() {
  const file = secretPath();
  if (!fs.existsSync(file) || !safeStorage.isEncryptionAvailable()) return '';
  return safeStorage.decryptString(fs.readFileSync(file));
}

async function apiRequest(_event, { route, method = 'GET', body }) {
  if (!apiBase) throw new Error('Local core is not ready.');
  const normalizedMethod = String(method).toUpperCase();
  const allowed = [
    ['GET', /^\/api\/(dashboard|providers|context|notes)(\/[^/?]+)?(\?.*)?$/],
    ['POST', /^\/api\/(projects|tasks|chat)$/],
    ['PATCH', /^\/api\/tasks\/[^/?]+$/],
    ['PUT', /^\/api\/(projects|notes)\/[^/?]+(\?.*)?$/],
    ['DELETE', /^\/api\/tasks\/[^/?]+$/],
  ];
  if (!allowed.some(([verb, pattern]) => verb === normalizedMethod && pattern.test(String(route)))) {
    throw new Error('Unsupported local operation.');
  }
  const outgoing = body ? { ...body } : undefined;
  if (route === '/api/chat' && outgoing) outgoing.api_key = loadSecret();
  const response = await fetch(`${apiBase}${route}`, {
    method: normalizedMethod,
    headers: { Authorization: `Bearer ${apiToken}`, 'Content-Type': 'application/json' },
    body: outgoing ? JSON.stringify(outgoing) : undefined,
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || `Request failed (${response.status})`);
  return result;
}

function createWindow() {
  const window = new BrowserWindow({
    width: 1320,
    height: 860,
    minWidth: 980,
    minHeight: 680,
    backgroundColor: '#f3f0e9',
    titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });
  window.loadFile(path.join(__dirname, 'renderer', 'index.html'));
}

ipcMain.handle('pmgo:request', apiRequest);
ipcMain.handle('pmgo:save-provider-key', (_event, value) => saveSecret(String(value || '')));
ipcMain.handle('pmgo:has-provider-key', () => fs.existsSync(secretPath()));
ipcMain.handle('pmgo:data-dir', () => localDataDir());

app.whenReady().then(async () => {
  await startCore();
  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
}).catch((error) => {
  console.error(error);
  app.quit();
});

app.on('before-quit', () => {
  if (coreProcess && !coreProcess.killed) coreProcess.kill();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
