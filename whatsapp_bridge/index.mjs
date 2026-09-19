import fs from 'node:fs'
import path from 'node:path'
import readline from 'node:readline'
import process from 'node:process'
import { fileURLToPath } from 'node:url'
import { spawn } from 'node:child_process'
import P from 'pino'
import { makeWASocket, useMultiFileAuthState, fetchLatestBaileysVersion, DisconnectReason, makeCacheableSignalKeyStore } from '@whiskeysockets/baileys'
import { Boom } from '@hapi/boom'
import { resolveJidAsync, patchGroupMetadata } from './jid_resolver.mjs'

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
  curioso: 'curious', pensar: 'think', pensarfuerte: 'thinkhard', dormir: 'sleep', saludar: 'wave', enojado: 'angry',
  grito: 'scream', salto: 'jump', cosquillas: 'tickle', nope: 'nope', bofetada: 'slap',
  morder: 'bite', sonrojo: 'blush', caminar: 'walk', pegar: 'punch', acariciar: 'pat',
  palmada: 'palm', guiñar: 'wink', cantar: 'sing', empujar: 'push', calor: 'heat',
  jugar: 'gaming', dibujar: 'draw', llamar: 'call', acurrucar: 'snuggle', tropezar: 'trip',
  mirar: 'stare', oler: 'sniff', consolar: 'comfort', espiar: 'peek', frio: 'cold',
  gritar: 'scream', darbeso: 'blowkiss', acurrucarse: 'cuddle', cosquillear: 'tickle'
}
const animeSymbols = ['(✧ω✧)', '(⌒‿⌒)', '(¬‿¬)', '(*≧ω≦)', '(✿◡‿◡)', '(・o・)', '(ง •̀_•́)ง']
const animeInteractions = new Set(`angry bleh bored clap coffee dramatic drunk impregnate kisscheek laugh love pout punch run sad scared seduce shy sleep smoke spit step think walk hug kill eat kiss wink pat palm happy bully bite blush wave bath smug smile highfive handhold cringe bonk cry lick slap dance cuddle cold sing tickle scream push nope jump heat gaming draw call snuggle blowkiss trip stare sniff curious thinkhard comfort peek`.split(' '))
const animeCaptions = {
  hug: 'abrazó a', kiss: 'le dio un beso a', kisscheek: 'le dio un beso en la mejilla a', slap: 'le dio una bofetada a', punch: 'le dio un puñetazo a',
  pat: 'le dio una caricia a', wave: 'saludó a', wink: 'le guiñó a', highfive: 'chocó los cinco con', handhold: 'le agarró la mano a',
  cuddle: 'se acurrucó con', snuggle: 'se acurrucó dulcemente con', tickle: 'le hizo cosquillas a', push: 'empujó a', bite: 'mordió a',
  love: 'siente atracción por', angry: 'está muy enojado con', sad: 'está triste por', happy: 'está feliz con', dance: 'está bailando con',
  sing: 'le está cantando a', scream: 'le está gritando a', stare: 'se queda mirando fijamente a', sniff: 'está olfateando a',
  curious: 'está curioso por lo que hace', comfort: 'está consolando a', peek: 'está espiando a',
  cry: 'llora por', scared: 'está asustado por', bored: 'está aburrido de', cringe: 'siente cringe por',
  blush: 'se sonrojó por', pout: 'hace pucheros con', drunk: 'está borracho con', dramatic: 'le hace un drama a',
  cold: 'tiene frío por', heat: 'tiene calor por',
}
const emotionalInteractions = new Set(['cry', 'sad', 'scared', 'bored', 'cringe', 'blush', 'pout', 'drunk', 'cold', 'heat', 'angry', 'happy'])
const directEmotionCaptions = {
  cry: 'llora con', sad: 'comparte tristeza con', scared: 'se pone nervioso con', bored: 'se aburre con', cringe: 'siente cringe con',
  blush: 'se sonroja con', pout: 'hace pucheros con', drunk: 'está borracho con', cold: 'tiene frío con', heat: 'tiene calor con',
  angry: 'se enoja con', happy: 'está feliz con'
}
let reconnecting = false

function extractNumber(value) {
  if (!value || /@lid(?:$|:)/i.test(String(value))) return ''
  const number = String(value).split('@')[0].split(':')[0].replace(/\D/g, '')
  return /^\d{8,15}$/.test(number) ? number : ''
}

async function resolveRawNumber(conn, raw, chat) {
  const direct = extractNumber(raw)
  if (direct) return direct
  try {
    const resolved = await resolveJidAsync(raw, conn, chat)
    return extractNumber(resolved)
  } catch (error) {
    console.error('[Botmk LID resolver]', error)
    return ''
  }
}

async function isGroupModerator(conn, chat, sender) {
  if (sender === ownerPhone) return true
  try {
    const metadata = await conn.groupMetadata(chat)
    for (const participant of metadata.participants || []) {
      const number = await resolveRawNumber(conn, participant.phoneNumber || participant.jid || participant.id || '', chat)
      if (number === sender) return participant.admin === 'admin' || participant.admin === 'superadmin'
    }
  } catch (error) { console.error('[Botmk admin check]', error) }
  return false
}

async function resolveSenderNumber(conn, msg, chat) {
  const key = msg.key || {}
  for (const candidate of [key.senderPn, key.participantPn, key.participantAlt, key.remoteJidAlt, key.participant]) {
    const number = await resolveRawNumber(conn, candidate, chat)
    if (number) return number
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
  const interaction = animeAliases[requested] || (words[0] === 'anime' ? requested : (animeInteractions.has(words[0]) ? words[0] : ''))
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
    const sender = await resolveSenderNumber(conn, msg, chat)
    const context = msg.message?.extendedTextMessage?.contextInfo || {}
    const isReply = Boolean(context.participant && (context.quotedMessage || context.stanzaId))
    const targetRaw = context.mentionedJid?.[0] || context.participant || ''
    const target = await resolveRawNumber(conn, targetRaw, chat) || sender
    const fromTag = `@${sender || 'usuario'}`
    const toTag = `@${target || 'usuario'}`
    const symbol = animeSymbols[Math.floor(Math.random() * animeSymbols.length)]
    const action = (!isReply && emotionalInteractions.has(interaction) ? directEmotionCaptions[interaction] : null) || animeCaptions[interaction] || `hizo ${interaction} con`
    const caption = sender === target ? `${fromTag} ${action.replace(/ (a|por|con|de)$/, '')} ${symbol}.` : `${fromTag} ${action} ${toTag} ${symbol}.`
    const mentions = [...new Set([sender && `${sender}@s.whatsapp.net`, target && `${target}@s.whatsapp.net`].filter(Boolean))]
    await conn.sendMessage(chat, { video: buffer, mimetype: 'video/mp4', gifPlayback: true,
      caption, mentions }, { quoted: msg })
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
  patchGroupMetadata(conn)
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
      if (chat.endsWith('@g.us') && command === 'quitar' || (chat.endsWith('@g.us') && command.startsWith('quitar '))) {
        if (!(await isGroupModerator(conn, chat, sender))) continue
        const context = msg.message?.extendedTextMessage?.contextInfo || {}
        const targetRaw = context.mentionedJid?.[0] || context.participant || ''
        const target = await resolveRawNumber(conn, targetRaw, chat)
        if (!target) continue
        try {
          await conn.groupParticipantsUpdate(chat, [`${target}@s.whatsapp.net`], 'remove')
        } catch (error) { console.error('[Botmk quitar]', error) }
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
