# Cómo obtener datos de Scryfall cuando el contenedor los tiene bloqueados

En sandboxes con proxy restringido, `api.scryfall.com`, `data.scryfall.io`, `mtgjson.com` y los
sitios de mazos suelen devolver `CONNECT tunnel failed, 403`. `WebFetch` tampoco sirve: Scryfall
responde 403 al fetcher.

Diagnóstico rápido de qué sí alcanzas:

```bash
for u in https://api.scryfall.com https://pypi.org https://registry.npmjs.org \
         https://raw.githubusercontent.com https://api.github.com; do
  printf "%-42s " "$u"; timeout 10 curl -sS -o /dev/null -w "%{http_code}\n" "$u"
done
```

Típicamente pasan solo los registros de paquetes y `raw.githubusercontent.com`. **No existe un
paquete de PyPI o npm que traiga los datos empaquetados** — todos los descargan en tiempo de
ejecución.

## La solución: el navegador del usuario como puente

Si hay integración con el navegador (Claude in Chrome) o acceso al escritorio del usuario, su
máquina sí alcanza Scryfall. La API manda `Access-Control-Allow-Origin: *`, así que un `fetch`
desde cualquier página funciona.

### Paso 1 — abrir una pestaña y probar

```js
const r = await fetch('https://api.scryfall.com/cards/named?exact=Lightning+Bolt');
(await r.json()).name;
```

### Paso 2 — traer las cartas exactas de la colección

Si el CSV trae Scryfall IDs, usa el endpoint `collection` (75 por petición, exacto, sin
ambigüedad de idioma ni de edición). Genera el script desde Python para no tipear los UUIDs:

```js
const out=[];
for (let i=0; i<IDS.length; i+=75) {
  const r = await fetch("https://api.scryfall.com/cards/collection", {
    method:"POST", headers:{"Content-Type":"application/json"},
    body: JSON.stringify({identifiers: IDS.slice(i,i+75).map(id=>({id}))})
  });
  (await r.json()).data.forEach(c => out.push(trim(c)));
  await new Promise(s=>setTimeout(s,120));      // cortesía con la API
}
```

Recorta los campos antes de sacarlos: `id, oracle_id, name, printed_name, lang, set,
collector_number, rarity, mana_cost, cmc, type_line, oracle_text, power, toughness, loyalty,
colors, color_identity, keywords, produced_mana, legalities, layout, card_faces, prices.usd`.

**Importante:** `JSON.stringify` descarta las claves `undefined`. Scryfall omite `power` en las
no-criaturas, así que sin normalizar (`x => x===undefined ? null : x`) el consumidor revienta
con `KeyError`.

### Paso 3 — sacar el archivo del navegador

No lo devuelvas por el chat: son cientos de KB. Dispara una descarga:

```js
const blob = new Blob([JSON.stringify(out)], {type:'application/json'});
const a = document.createElement('a');
a.href = URL.createObjectURL(blob); a.download = 'cards.json';
document.body.appendChild(a); a.click(); a.remove();
```

Luego trae el archivo al contenedor con el puente de archivos del escritorio.

**Ojo:** Chrome puede estar configurado con otra carpeta de descargas, o pedir confirmación al
usuario. Si el archivo no aparece donde esperas, pregúntale dónde quedó antes de reintentar.

### Paso 4 — el universo completo

Para el bulk (todas las cartas de Magic), pide el índice y usa el enlace directo — `fetch` sobre
`data.scryfall.io` falla por CORS, pero un `<a download>` apuntando a la URL sí descarga:

```js
const b = await (await fetch('https://api.scryfall.com/bulk-data')).json();
const url = b.data.find(x=>x.type==='oracle_cards').jsonl_download_uri;
const a=document.createElement('a'); a.href=url; a.download='oracle-cards.jsonl.gz';
document.body.appendChild(a); a.click(); a.remove();
```

`oracle_cards` comprimido ronda los 25 MB (~38.000 cartas) — cómodo de transferir. `default_cards`
y `all_cards` son mucho más grandes y rara vez hacen falta: solo si necesitas datos por edición
concreta en vez de por carta.

### Límites a respetar

- No hagas más de ~10 peticiones por segundo. Mete 100-150 ms entre llamadas.
- Búsquedas grandes con `include_multilingual` pueden tardar más que el timeout de la
  herramienta (45 s). Divídelas por set o usa el endpoint `collection`.
