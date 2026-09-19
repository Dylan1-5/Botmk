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
const reactionsApi = process.env.BOTMK_REACTIONS_API || 'https://api.alyacore.xyz/sfw/interaction'
const reactionsApiKey = process.env.BOTMK_REACTIONS_API_KEY || ''
const animeAliases = {
  feliz: 'happy', triste: 'sad', amor: 'love', beso: 'kiss', muak: 'kiss', cafe: 'coffee',
  aburrido: 'bored', drama: 'dramatic', timido: 'shy', correr: 'run', llorar: 'cry',
  reir: 'laugh', abrazo: 'hug', bailar: 'dance', guiño: 'wink', wink: 'wink',
  curioso: 'curious', pensar: 'think', dormir: 'sleep', saludar: 'wave', enojado: 'angry',
  grito: 'scream', salto: 'jump', cosquillas: 'tickle', nope: 'nope', bofetada: 'slap'
}
const animeSymbols = ['(✧ω✧)', '(⌒‿⌒)', '(¬‿¬)', '(*≧ω≦)', '(✿◡‿◡)', '(・o・)', '(ง •̀_•́)ง']
let reconnecting = false

function extractNumber(value) {
  if (!value || /@lid(?:$|:)/i.test(String(value))) return ''
  const number = String(value).split('@')[0].split(':')[0].replace(/\D/g, '')
  return /^\d{8,15}$/.test(number) ? number : ''
}

async function resolveSenderNumber(conn, msg, chat) {
  const key = msg.key || {}
  for (const candidate of [key.senderPn, key.participantPn, key.participantAlt, key.remoteJidAlt, key.participant]) {
    const number = extractNumber(candidate)
    if (number) return number
  }
  const lid = key.participant || ''
  if (String(lid).endsWith('@lid') && chat.endsWith('@g.us')) {
    try {
      const metadata = await conn.groupMetadata(chat)
      const participant = (metadata.participants || []).find(p => p.lid === lid || p.id === lid)
      return extractNumber(participant?.phoneNumber || participant?.jid || '')
    } catch (error) { console.error('[Botmk number resolver]', error) }
  }
  return ''
}

function normalizeText(value) {
  return String(value).toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
}

function isViewQuestion(value) {
  const text = normalizeText(value)
  return text.includes('que estas viendo') || text.includes('que ves') || text.includes('que estas mirando')
}

async function sendAnimeReaction(conn, chat, msg, phrase) {
  const words = normalizeText(phrase).split(/\s+/)
  const requested = words[0] === 'anime' ? words[1] : words[0]
  const interaction = animeAliases[requested] || (words[0] === 'anime' ? requested : '')
  if (!interaction) return false
  if (!reactionsApiKey) {
    await conn.sendMessage(chat, { text: '⚠️ La reacción anime está instalada, pero falta configurar BOTMK_REACTIONS_API_KEY.' }, { quoted: msg })
    return true
  }
  try {
    const endpoint = `${reactionsApi}?inter=${encodeURIComponent(interaction)}&key=${encodeURIComponent(reactionsApiKey)}`
    const response = await fetch(endpoint)
    if (!response.ok) throw new Error(`API HTTP ${response.status}`)
    const data = await response.json()
    const videoUrl = data?.result
    if (!videoUrl) throw new Error('la API no devolvió un video')
    const videoResponse = await fetch(videoUrl, { headers: { Accept: 'video/mp4', 'User-Agent': 'Botmk/1.0' } })
    if (!videoResponse.ok) throw new Error(`video HTTP ${videoResponse.status}`)
    const buffer = Buffer.from(await videoResponse.arrayBuffer())
    const symbol = animeSymbols[Math.floor(Math.random() * animeSymbols.length)]
    await conn.sendMessage(chat, { video: buffer, mimetype: 'video/mp4', gifPlayback: true,
      caption: `${symbol} Reacción anime: ${interaction}.`, }, { quoted: msg })
  } catch (error) {
    await conn.sendMessage(chat, { text: `✿ No pude generar la reacción anime: ${error.message}` }, { quoted: msg })
  }
  return true
}

async function sendIllustratedView(conn, chat, msg, state) {
  const scenes = [
    [
      `👁️ *PERCEPCIÓN — PARTE 1/3*\n\n╔════════════════════════════════╗\n║        ~ ~  ANTENAS  ~ ~       ║\n║          ╭────────╮            ║\n║          │  o  o  │            ║\n║          │   ^    │            ║\n║          ╰───┬────╯            ║\n╚════════════════════════════════╝\n\nEstado neuronal: ${state}\nEstoy comenzando a explorar lo que percibo.`,
      `👁️ *PERCEPCIÓN — PARTE 1/3*\n\n╔════════════════════════════════╗\n║      ~ ✦ ~  ANTENAS  ~ ✦ ~    ║\n║          ╭────────╮            ║\n║       ✦  │  •  •  │  ✦         ║\n║          │   ^    │            ║\n║          ╰───┬────╯            ║\n╚════════════════════════════════╝\n\nEstado neuronal: ${state}\nDetecto señales cambiando a mi alrededor.`,
      `👁️ *PERCEPCIÓN — PARTE 1/3*\n\n╔════════════════════════════════╗\n║    ~ ✦ ~  ANTENAS  ~ ✦ ~      ║\n║          ╭────────╮            ║\n║       ✦  │  •  •  │  ✦         ║\n║          │  \ /   │            ║\n║          ╰───┬────╯            ║\n╚════════════════════════════════╝\n\nEstado neuronal: ${state}\nMi actividad aumenta mientras observo.`
    ],
    [
      `🧠 *PERCEPCIÓN — PARTE 2/3*\n\n╔════════════════════════════════╗\n║       .-────────────-.         ║\n║      /  o          o  \\        ║\n║     |        ^         |       ║\n║      \\    ──────    /        ║\n║       '──────────────'         ║\n║          ║  ║  ║              ║\n╚════════════════════════════════╝\n\nEstoy comparando señales con mi memoria.`,
      `🧠 *PERCEPCIÓN — PARTE 2/3*\n\n╔════════════════════════════════╗\n║       .-────────────-.         ║\n║      /  •          •  \\        ║\n║     |    ✦    ^   ✦    |       ║\n║      \\    ──────    /        ║\n║       '──────────────'         ║\n║        ║  ║  ║  ║  ║          ║\n╚════════════════════════════════╝\n\nLa memoria encuentra un patrón parecido.`,
      `🧠 *PERCEPCIÓN — PARTE 2/3*\n\n╔════════════════════════════════╗\n║       .-────────────-.         ║\n║      /  •          •  \\        ║\n║     |    ✦    ^   ✦    |       ║\n║      \\   ────────   /        ║\n║       '──────────────'         ║\n║     ║  ║  ║  ║  ║  ║  ║        ║\n╚════════════════════════════════╝\n\nYa elegí una interpretación experimental.`
    ],
    [
      `✅ *PERCEPCIÓN — PARTE 3/3*\n\n╔════════════════════════════════╗\n║       RESULTADO EXPERIMENTAL   ║\n║                                ║\n║          [ ${state} ]           ║\n║                                ║\n║       actividad → estado       ║\n║       estado → descripción     ║\n╚════════════════════════════════╝\n\nTodavía no es visión humana: es una ilustración de mi actividad.`,
      `✅ *PERCEPCIÓN — PARTE 3/3*\n\n╔════════════════════════════════╗\n║       RESULTADO EXPERIMENTAL   ║\n║                                ║\n║       [ ${state} ]  →  ✦       ║\n║                                ║\n║       actividad → estado       ║\n║       estado → intención       ║\n╚════════════════════════════════╝\n\nEstoy preparando una respuesta en español.`,
      `✅ *PERCEPCIÓN — PARTE 3/3*\n\n╔════════════════════════════════╗\n║          PERCEPCIÓN LISTA      ║\n║                                ║\n║       [ ${state} ]  →  ✦       ║\n║                                ║\n║  Mi estado cambió mientras     ║\n║  procesaba las señales.        ║\n╚════════════════════════════════╝\n\nRepresentación textual, no una cámara real.`
    ]
  ]
  for (const frames of scenes) {
    let sent = await conn.sendMessage(chat, { text: frames[0] }, { quoted: msg })
    for (const frame of frames.slice(1)) {
      await new Promise(resolve => setTimeout(resolve, 900))
      try {
        await conn.sendMessage(chat, { text: frame, edit: sent.key })
      } catch (error) {
        console.error('[Botmk edit fallback]', error)
        sent = await conn.sendMessage(chat, { text: frame }, { quoted: msg })
      }
    }
  }
}
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
      const sender = await resolveSenderNumber(conn, msg, chat)
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
      if (await sendAnimeReaction(conn, chat, msg, phrase)) continue
      try {
        const result = await worker.ask(phrase)
        if (result.ok) {
          if (isViewQuestion(phrase)) {
            const state = result.result?.mind?.estado_interno || 'actividad experimental'
            await conn.sendPresenceUpdate('composing', chat)
            await sendIllustratedView(conn, chat, msg, state)
            await conn.sendPresenceUpdate('paused', chat)
            continue
          }
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
