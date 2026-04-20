const { contextBridge, ipcRenderer } = require('electron')

const desktopBridge = {
  isElectron: true,
  runtime: ipcRenderer.sendSync('desktop:get-runtime-info-sync'),
  getRuntimeInfo: async () => {
    desktopBridge.runtime = await ipcRenderer.invoke('desktop:get-runtime-info')
    return desktopBridge.runtime
  },
  acknowledgeInitialAdmin: async () => {
    desktopBridge.runtime = await ipcRenderer.invoke('desktop:acknowledge-initial-admin')
    return desktopBridge.runtime
  },
}

contextBridge.exposeInMainWorld('desktop', desktopBridge)
