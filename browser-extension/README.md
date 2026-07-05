# Pre-Market News → Analyser (Chrome-tillägg)

Ett klick i verktygsfältet skickar **aktuell sida** till Krantz Pre-Market
News Analyser. Analysen sparas i backend och dyker upp i dashboardens
**Historik** (🕐-knappen eller News Analyser-modalen). Slipper kopiera länkar.

Tillägget läser sidans redan renderade text, så det kommer åt även
betalvägg-/JS-sidor som serverns URL-hämtning kan missa.

## Installera (utvecklarläge)

1. Öppna `chrome://extensions` (funkar även i Edge: `edge://extensions`).
2. Slå på **Utvecklarläge** (uppe till höger).
3. Klicka **Läs in okpackat** / **Load unpacked** och välj den här mappen
   (`browser-extension`).
4. (Valfritt) Fäst tillägget i verktygsfältet via pusselbits-ikonen.

## Använda

- Gå in på en nyhetsartikel.
- Klicka på tilläggets ikon (📈-staplarna).
- En bricka på ikonen visar status: `…` (jobbar), `✓` (klar), `!` (fel),
  och en notis bekräftar. Analysen finns nu i historiken på
  **http://skzdev02:3000**.

## Inställningar

Backend-URL är förvald till `http://skzdev02:3000` (Tailscale). Vill du peka
mot en annan adress: högerklicka tillägget → **Alternativ** / **Options**.

> Obs: datorn måste nå backenden (samma Tailscale-nät). Tilläggets
> `host_permissions` täcker `skzdev02` och `100.94.139.84`. Använder du en
> annan värd behöver den läggas till i `manifest.json`.

## Filer

- `manifest.json` — MV3-manifest (action, permissions, host_permissions).
- `background.js` — service worker: extraherar sida → POST `/api/news/analyze`.
- `options.html` / `options.js` — ställ in backend-URL.
- `icon*.png` — verktygsfältsikon.
