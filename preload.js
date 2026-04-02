const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('api', {
    runPipeline: (csvPath, provider, apiKey) =>
        ipcRenderer.invoke('run_pipeline', csvPath, provider, apiKey)
})