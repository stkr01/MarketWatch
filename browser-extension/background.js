// One-click: grab the current page, send it to the Pre-Market News Analyser,
// and let the analysis show up in the dashboard history. No copy/paste.

const DEFAULT_API = 'http://skzdev02:3000'

async function getApiBase() {
  const { apiBase } = await chrome.storage.sync.get('apiBase')
  return (apiBase || DEFAULT_API).replace(/\/+$/, '')
}

// Runs in the page context to extract the main article text + title.
function extractPage() {
  const pickText = () => {
    for (const sel of ['article', 'main', '[role="main"]']) {
      const el = document.querySelector(sel)
      const t = el && el.innerText ? el.innerText.trim() : ''
      if (t.length > 200) return t
    }
    return document.body ? document.body.innerText : ''
  }
  const og = document.querySelector('meta[property="og:title"]')
  const title = ((og && og.content) || document.title || '').trim()
  const text = (pickText() || '').replace(/[ \t]+\n/g, '\n').replace(/\n{3,}/g, '\n\n').trim()
  return { url: location.href, title, text: text.slice(0, 20000) }
}

async function setBadge(text, color) {
  try {
    await chrome.action.setBadgeText({ text })
    if (color) await chrome.action.setBadgeBackgroundColor({ color })
  } catch (_) { /* noop */ }
}

function notify(title, message) {
  try {
    chrome.notifications.create('', {
      type: 'basic',
      iconUrl: 'icon128.png',
      title,
      message,
    })
  } catch (_) { /* noop */ }
}

chrome.action.onClicked.addListener(async (tab) => {
  if (!tab || !tab.id) return

  const url = tab.url || ''
  if (/^(chrome|edge|about|chrome-extension):/i.test(url)) {
    await setBadge('!', '#dc2626')
    notify('Kan inte analysera', 'Den här sidan kan inte läsas (webbläsarens egen sida).')
    setTimeout(() => setBadge('', null), 5000)
    return
  }

  try {
    await setBadge('…', '#6b7280')

    const [inj] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: extractPage,
    })
    const page = (inj && inj.result) || {}
    if (!page.text || page.text.length < 80) {
      throw new Error('Kunde inte läsa tillräckligt med text från sidan.')
    }

    const api = await getApiBase()
    const resp = await fetch(`${api}/api/news/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: page.url, title: page.title || null, text: page.text }),
    })

    if (!resp.ok) {
      let detail = `Servern svarade ${resp.status}`
      try { detail = (await resp.json()).detail || detail } catch (_) { /* noop */ }
      throw new Error(detail)
    }

    const data = await resp.json().catch(() => ({}))
    const n = Array.isArray(data.assets) ? data.assets.length : 0
    await setBadge('✓', '#16a34a')
    notify('✓ Analys sparad', `${page.title || 'Sidan'} — ${n} påverkade assets. Finns nu i News Analyser-historiken.`)
    setTimeout(() => setBadge('', null), 4000)
  } catch (e) {
    await setBadge('!', '#dc2626')
    notify('Kunde inte analysera', String((e && e.message) || e))
    setTimeout(() => setBadge('', null), 6000)
  }
})
