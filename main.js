
// main.js - Main process of the Electron application. Responsible for creating the browser window and handling IPC communication with the renderer process.
const { app, BrowserWindow, ipcMain } = require('electron')
const { spawn } = require('child_process')
const path = require('path')

const VENV_PYTHON = path.join(__dirname, '.venv', 'bin', 'python')
const PIPELINE = path.join(__dirname, 'python', 'pipeline.py')


// Create the browser window and load the HTML file. Also sets up IPC handlers for communication with the renderer process.
function createWindow() { // creates the browser window.
    const win = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js') // preload script that exposes the API to the renderer process
        }
    })
    win.loadFile('renderer/index.html') // loads the HTML file into the window
}
// When the app is ready, create the browser window. Also sets up an event listener to quit the app when all windows are closed (except on macOS).
app.whenReady().then(createWindow)

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit()
})


// IPC handler for running the pipeline. This listens for 'run_pipeline' events from the renderer process, spawns a child process to run the Python script, 
// and returns the output or error back to the renderer.
ipcMain.handle('run_pipeline', async (event, csvPath, provider, apiKey) => {
    return new Promise((resolve, reject) => {
        const proc = spawn(VENV_PYTHON, [PIPELINE, csvPath, provider, apiKey], {
            env: { ...process.env, AI_PROVIDER: provider }
        });

        let stdout = '';
        let stderr = '';

        proc.stdout.on('data', (d) => {
            stdout += d;
        });

        proc.stderr.on('data', (d) => {
            stderr += d;
        });

        proc.on('close', (code) => {
            console.log('Python exit code:', code);
            console.log('stdout:', stdout);
            console.log('stderr:', stderr);

            if (code !== 0) {
                // Optionally log stderr to console before rejecting for easier debugging
                console.error('Pipeline failed:', stderr);
                reject(new Error(`Exit $${code}:\nSTDERR:\n$${stderr}\nSTDOUT:\n${stdout}`));
            } else {
                resolve(stdout);
            }
        });
        
        // Optional: Handle process errors (e.g., if the Python script doesn't exist)
        proc.on('error', (err) => {
            console.error('Failed to start pipeline process:', err);
            reject(err);
        });
    });
});
// nothing after this
// error handling for uncaught exceptions in the main process

