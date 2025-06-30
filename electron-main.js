import { app, BrowserWindow } from 'electron'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { dirname } from 'node:path'

// Recrée le chemin __dirname en ESM
const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

let win = null

function createWindow() {
  win = new BrowserWindow({
    width: 1000,
    height: 700,
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

  if (app.isPackaged) {
    win.loadFile(path.join(__dirname, 'dist', 'index.html'))
  } else {
    // Mode développement : charger l'URL Vite
    win.loadURL(devServerUrl)
    win.webContents.openDevTools()
  }

  win.on('closed', () => {
    win = null
  })
}

// App prête → créer la fenêtre
app.whenReady().then(createWindow)

// Recrée la fenêtre si l'app est relancée (macOS)
app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow()
})

// Quitter l'app si toutes les fenêtres sont fermées (sauf macOS)
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})
