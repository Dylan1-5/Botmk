const lidCache = new Map()
const metaCache = new Map()
const META_TTL = 300_000

function normalizeJid(raw) {
  if (!raw) return ''
  const value = String(raw).trim()
  if (!value) return ''
  if (value.includes('@')) return value
  const digits = value.replace(/\D/g, '')
  return digits ? `${digits}@s.whatsapp.net` : value
}

function cacheLid(lid, jid) {
  if (lid && jid && !jid.endsWith('@lid')) lidCache.set(lid, jid)
}

async function resolveJidAsync(raw, sock, groupJid = '') {
  const jid = normalizeJid(raw)
  if (!jid || !jid.endsWith('@lid')) return jid
  if (lidCache.has(jid)) return lidCache.get(jid)

  try {
    if (typeof sock.findJidByLid === 'function') {
      const found = sock.findJidByLid(jid)
      if (found && !found.endsWith('@lid')) { cacheLid(jid, found); return found }
    }
  } catch {}

  if (!groupJid?.endsWith('@g.us')) return jid
  let metadata = metaCache.get(groupJid)
  if (!metadata || Date.now() - metadata.time > META_TTL) {
    try {
      metadata = { data: await sock.groupMetadata(groupJid), time: Date.now() }
      metaCache.set(groupJid, metadata)
    } catch { return jid }
  }
  const lidBase = jid.split('@')[0]
  for (const participant of metadata.data?.participants || []) {
    const participantLid = String(participant.lid || '').split('@')[0]
    if (participantLid !== lidBase) continue
    const phone = participant.phoneNumber || (participant.id?.endsWith('@lid') ? '' : participant.id) || participant.jid
    const resolved = normalizeJid(phone)
    if (resolved && !resolved.endsWith('@lid')) { cacheLid(jid, resolved); return resolved }
  }
  return jid
}

export { normalizeJid, resolveJidAsync }
