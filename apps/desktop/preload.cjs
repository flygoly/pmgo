const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('pmgo', {
  request: (options) => ipcRenderer.invoke('pmgo:request', options),
  saveProviderKey: (value) => ipcRenderer.invoke('pmgo:save-provider-key', value),
  hasProviderKey: () => ipcRenderer.invoke('pmgo:has-provider-key'),
  dataDir: () => ipcRenderer.invoke('pmgo:data-dir'),
});
