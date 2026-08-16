#!/usr/bin/env bash
# Descarga el bulk de cartas de Scryfall (oracle-cards) y lo deja en data/oracle.jsonl
set -e
mkdir -p data
URL=$(curl -s https://api.scryfall.com/bulk-data | python3 -c \
  "import sys,json;print([d['download_uri'] for d in json.load(sys.stdin)['data'] if d['type']=='oracle_cards'][0])")
echo "descargando $URL"
curl -L "$URL" -o data/oracle_tmp.json
python3 - <<'PY'
import json
cards=json.load(open('data/oracle_tmp.json'))
with open('data/oracle.jsonl','w') as f:
    for c in cards: f.write(json.dumps(c)+'\n')
print(f"{len(cards)} cartas en data/oracle.jsonl")
PY
rm -f data/oracle_tmp.json
