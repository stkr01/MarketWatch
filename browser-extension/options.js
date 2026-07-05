const DEFAULT_API = 'http://skzdev02:3000'
const input = document.getElementById('api')
const status = document.getElementById('status')

chrome.storage.sync.get('apiBase', ({ apiBase }) => {
  input.value = apiBase || DEFAULT_API
})

document.getElementById('save').addEventListener('click', () => {
  const val = input.value.trim().replace(/\/+$/, '') || DEFAULT_API
  chrome.storage.sync.set({ apiBase: val }, () => {
    input.value = val
    status.textContent = '✓ Sparat'
    setTimeout(() => (status.textContent = ''), 2000)
  })
})
