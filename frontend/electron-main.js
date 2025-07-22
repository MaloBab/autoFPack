import { app, BrowserWindow } from 'electron'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { dirname } from 'node:path'
import { spawn } from 'node:child_process'
import http from 'http'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

let win = null
let backendStarted = false
let backendProcess = null

function waitForBackend(url, retries = 20, interval = 500) {
  return new Promise((resolve, reject) => {
    const attempt = () => {
      console.log(`Checking backend at ${url}... (${retries} retries left)`)
      http.get(url, res => {
        if (res.statusCode === 200 || res.statusCode === 404) {
          console.log('✅ Backend is up!')
          resolve()
        } else {
          retry()
        }
      }).on('error', retry)
    }

    const retry = () => {
      if (retries <= 0) {
        reject(new Error('Backend did not start in time'))
      } else {
        retries--
        setTimeout(attempt, interval)
      }
    }

    attempt()
  })
}

function createWindow() {
  win = new BrowserWindow({
    width: 1000,
    height: 700,
    minWidth: 1000,
    minHeight: 700,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  })

  const devServerUrl = process.env.VITE_DEV_SERVER_URL || 'http://localhost:5173'

  console.log('======== Electron DEBUG ========')
  console.log('App is packaged:', app.isPackaged)
  console.log('Dev server URL:', devServerUrl)
  console.log('================================')

  let backendExePath = ''

  if (app.isPackaged && !backendStarted) {
    backendStarted = true
    backendExePath = path.join(process.resourcesPath, 'backend.exe')
    console.log('Starting backend:', backendExePath)

    backendProcess = spawn(backendExePath, { cwd: path.dirname(backendExePath) })

    backendProcess.stdout.on('data', (data) => {
      console.log(`[Backend] ${data}`)
    })

    backendProcess.stderr.on('data', (data) => {
      console.error(`[Backend ERROR] ${data}`)
    })

    backendProcess.on('close', (code) => {
      console.log(`Backend process exited with code ${code}`)
    })

    waitForBackend('http://localhost:8000/docs')
      .then(() => {
        win.loadFile(path.join(__dirname, 'dist', 'index.html'))
      })
      .catch(err => {
        console.error('❌ Backend did not start in time:', err)
        win.loadFile(path.join(__dirname, 'dist', 'index.html'))
      })
  } else {
    backendExePath = path.join(process.resourcesPath, 'backend.exe')
    console.log('Dev mode: backend path:', backendExePath)
    win.loadURL(devServerUrl)
  }

  win.on('closed', () => {
    win = null
  })
}

app.whenReady().then(createWindow)

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow()
})

app.on('before-quit', () => {
  if (backendProcess) {
    backendProcess.kill()
  }
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    if (backendProcess) {
      backendProcess.kill()
    }
    app.quit()
  }
})

