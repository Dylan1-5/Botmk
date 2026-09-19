import fs from 'node:fs'
import path from 'node:path'
import readline from 'node:readline'
import process from 'node:process'
import { fileURLToPath } from 'node:url'
import { spawn } from 'node:child_process'
import P from 'pino'
import { makeWASocket, useMultiFileAuthState, fetchLatestBaileysVersion, DisconnectReason, makeCacheableSignalKeyStore } from '@whiskeysockets/baileys'
import { Boom } from '@hapi/boom'

const prefix = 'nex'
const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const sessionDir = process.env.BOTMK_SESSION_DIR || path.join(repoRoot, 'sessions_botmk')
const allowedChat = process.env.BOTMK_ALLOWED_CHAT || ''
const ownerPhone = String(process.env.BOTMK_OWNER_PHONE || '50662907002').replace(/\D/g, '')
const python = process.env.BOTMK_PYTHON || 'python3'
let reconnecting = false

function startWorker() {
  const child = spawn(python, ['-u', '-m', 'botmk_bridge'], {
    cwd: repoRoot,
    env: { ...process.env, PYTHONPATH: repoRoot },
    stdio: ['pipe', 'pipe', 'inherit']
  })
  const pending = []
  const rl = readline.createInterface({ input: child.stdout })
  rl.on('line', line => { const item = pending.shift(); if (item) item(JSON.parse(line)) })
  return { child, ask: text => new Promise((resolve, reject) => { pending.push(resolve); child.stdin.write(JSON.stringify({ text }) + '\n') }) }
}

async function start() {
  fs.mkdirSync(sessionDir, { recursive: true })
  const { state, saveCreds } = await useMultiFileAuthState(sessionDir)
  const { version } = await fetchLatestBaileysVersion()
  const conn = makeWASocket({ version, logger: P({ level: 'silent' }), printQRInTerminal: false,
    auth: { creds: state.creds, keys: makeCacheableSignalKeyStore(state.keys, P({ level: 'silent' })) },
    browser: ['Botmk', 'Ubuntu', '1.0'], syncFullHistory: false, markOnlineOnConnect: true })
  conn.ev.on('creds.update', saveCreds)
  if (!state.creds.registered) {
    const phone = String(process.env.BOTMK_PHONE || '').replace(/\D/g, '')
    if (!phone) throw new Error('Define BOTMK_PHONE con el número independiente que se vinculará.')
    setTimeout(async () => {
      const code = await conn.requestPairingCode(phone)
      console.log(`BOTMK_PAIRING_CODE=${code.match(/.{1,4}/g)?.join('-') || code}`)
    }, 2500)
  }
  const worker = startWorker()
  conn.ev.on('messages.upsert', async ({ messages }) => {
    for (const msg of messages || []) {
      if (msg.key?.fromMe) continue
      const chat = msg.key?.remoteJid || ''
      if (allowedChat && chat !== allowedChat) continue
      const text = msg.message?.conversation || msg.message?.extendedTextMessage?.text || ''
      if (!text.toLowerCase().startsWith(prefix)) continue
      const phrase = text.slice(prefix.length).trim()
      if (!phrase) continue
      const sender = String(msg.key?.participant || msg.key?.participantAlt || '').replace(/\D/g, '')
      const command = phrase.toLowerCase()
      if (chat.endsWith('@g.us') && sender === ownerPhone && ['salte', 'vamos', 'sacame'].includes(command)) {
        try {
          const ownerJid = `${ownerPhone}@s.whatsapp.net`
          if (command === 'sacame' || command === 'vamos') {
            await conn.groupParticipantsUpdate(chat, [ownerJid], 'remove')
          }
          if (command === 'salte' || command === 'vamos') {
            await conn.groupLeave(chat)
          }
        } catch (error) { console.error('[Botmk group command]', error) }
        continue
      }
      try {
        const result = await worker.ask(phrase)
        if (result.ok) {
          await conn.sendPresenceUpdate('composing', chat)
          const delayMs = Math.min(2500, Math.max(400, result.reply.length * 28))
          await new Promise(resolve => setTimeout(resolve, delayMs))
          await conn.sendMessage(chat, { text: result.reply }, { quoted: msg })
          await conn.sendPresenceUpdate('paused', chat)
        }
      } catch (error) { console.error('[Botmk worker]', error) }
    }
  })
  conn.ev.on('connection.update', ({ connection, lastDisconnect }) => {
    if (connection === 'open') console.log('BOTMK_CONNECTED')
    if (connection === 'close' && new Boom(lastDisconnect?.error)?.output?.statusCode !== DisconnectReason.loggedOut && !reconnecting) {
      reconnecting = true; setTimeout(() => { reconnecting = false; start().catch(console.error) }, 5000)
    }
  })
}
start().catch(error => { console.error('[Botmk]', error); process.exitCode = 1 })
