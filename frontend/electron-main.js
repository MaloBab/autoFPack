import { spawn } from 'child_process'
import path from 'path'

let backendProcess = null

function createWindow() {
  const win = new BrowserWindow({
    width: 1000,
    height: 700,
    minWidth: 1000,
    minHeight:700,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
    }
  })

  if (app.isPackaged) {
    win.loadFile(path.join(__dirname, 'dist/index.html'))

    const backendPath = path.join(__dirname, '../backend/App/main.py')
    backendProcess = spawn('python', [backendPath], {
      cwd: path.dirname(backendPath),
      shell: true
    })

    backendProcess.stdout.on('data', (data) => {
      console.log(`[FASTAPI] ${data}`)
    })

    backendProcess.stderr.on('data', (data) => {
      console.error(`[FASTAPI-ERR] ${data}`)
    })

  } else {
    win.loadURL('http://localhost:5173')
  }
}