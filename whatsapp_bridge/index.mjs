import fs from 'node:fs'
import path from 'node:path'
import readline from 'node:readline'
import process from 'node:process'
import { fileURLToPath } from 'node:url'
import { spawn } from 'node:child_process'
import P from 'pino'
import { makeWASocket, useMultiFileAuthState, fetchLatestBaileysVersion, DisconnectReason, makeCacheableSignalKeyStore, Browsers } from '@whiskeysockets/baileys'
import { Boom } from '@hapi/boom'

const prefix = 'nex'
const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const sessionDir = process.env.BOTMK_SESSION_DIR || path.join(repoRoot, 'sessions_botmk')
const allowedChat = process.env.BOTMK_ALLOWED_CHAT || ''
const python = process.env.BOTMK_PYTHON || 'python3'

let reconnecting = false
let worker = null
let activeConn = null

function startWorker() {
  if (worker?.child) {
    try { worker.child.kill() } catch (e) {}
  }

  const child = spawn(python, ['-u', '-m', 'botmk_bridge'], {
    cwd: repoRoot,
    env: { ...process.env, PYTHONPATH: repoRoot },
    stdio: ['pipe', 'pipe', 'inherit']
  })

  const pending = []
  const rl = readline.createInterface({ input: child.stdout })

  rl.on('line', line => {
    try {
      const data = JSON.parse(line)
      
      // Capturar mensajes espontáneos (libre albedrío)
      if (data.spontaneous) {
        if (activeConn && allowedChat) {
          activeConn.sendMessage(allowedChat, { text: data.reply }).catch(console.error)
        }
        return
      }

      const item = pending.shift()
      if (item) {
        item.resolve(data)
      }
    } catch (err) {
      const item = pending.shift()
      if (item) {
        item.reject(new Error(`Respuesta inválida del worker: ${line}`))
      }
    }
  })

  child.on('exit', () => {
    while (pending.length) {
      const item = pending.shift()
      item.reject(new Error('Worker process terminated'))
    }
  })

  return {
    child,
    ask: text => new Promise((resolve, reject) => {
      pending.push({ resolve, reject })
      child.stdin.write(JSON.stringify({ text }) + '\n')
    })
  }
}

async function start() {
  fs.mkdirSync(sessionDir, { recursive: true })
  const { state, saveCreds } = await useMultiFileAuthState(sessionDir)
  const { version } = await fetchLatestBaileysVersion()

  const conn = makeWASocket({
    version,
    logger: P({ level: 'silent' }),
    printQRInTerminal: false,
    auth: {
      creds: state.creds,
      keys: makeCacheableSignalKeyStore(state.keys, P({ level: 'silent' }))
    },
    browser: Browsers.ubuntu('Chrome'),
    syncFullHistory: false,
    markOnlineOnConnect: true
  })

  activeConn = conn
  conn.ev.on('creds.update', saveCreds)

  if (!state.creds.registered) {
    const phone = String(process.env.BOTMK_PHONE || '').replace(/\D/g, '')
    if (!phone) throw new Error('Define BOTMK_PHONE con el número en formato internacional sin el signo +.')
    
    setTimeout(async () => {
      try {
        const code = await conn.requestPairingCode(phone)
        const formattedCode = code?.match(/.{1,4}/g)?.join('-') || code
        console.log(`\n========================================`)
        console.log(`BOTMK_PAIRING_CODE: ${formattedCode}`)
        console.log(`========================================\n`)
      } catch (err) {
        console.error('Error generando pairing code:', err)
      }
    }, 3000)
  }

  if (!worker) {
    worker = startWorker()
  }

  conn.ev.on('messages.upsert', async ({ messages }) => {
    for (const msg of messages || []) {
      if (msg.key?.fromMe) continue
      const chat = msg.key?.remoteJid || ''
      if (allowedChat && chat !== allowedChat) continue

      const text = msg.message?.conversation || msg.message?.extendedTextMessage?.text || ''
      if (!text.toLowerCase().startsWith(prefix)) continue

      const phrase = text.slice(prefix.length).trim()
      if (!phrase) continue

      try {
        const result = await worker.ask(phrase)
        if (result.ok) {
          await conn.sendMessage(chat, { text: result.reply }, { quoted: msg })
        }
      } catch (error) {
        console.error('[Botmk worker]', error)
      }
    }
  })

  conn.ev.on('connection.update', ({ connection, lastDisconnect }) => {
    if (connection === 'open') console.log('BOTMK_CONNECTED')

    const statusCode = lastDisconnect?.error?.output?.statusCode
    const shouldReconnect = connection === 'close' && statusCode !== DisconnectReason.loggedOut

    if (shouldReconnect && !reconnecting) {
      reconnecting = true
      setTimeout(() => {
        reconnecting = false
        start().catch(console.error)
      }, 5000)
    }
  })
}

start().catch(error => {
  console.error('[Botmk]', error)
  process.exitCode = 1
})
