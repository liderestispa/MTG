# Formatos de CSV de colección

## CollectiDeal

```
Card name,Set code,Set name,Card number,Foil,rarity,quantity,Scryfall ID
```

- **Trae `Scryfall ID`**: úsalo siempre. Resuelve idioma y edición sin ambigüedad.
- `Card name` viene en el idioma de la carta física. No lo uses para buscar.
- `Card number` puede venir vacío en muchas filas; no lo necesitas si tienes el ID.
- La misma carta puede aparecer en varias filas (inglés y español): **súmalas por `oracle_id`**.

## Moxfield / Archidekt / Deckbox

Suelen traer `Count,Name,Edition,Condition,Language,Foil`. Sin Scryfall ID, así que hay que
resolver por nombre + edición. Normaliza antes de comparar:

```python
def norm(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii','ignore').decode().lower()
    return ''.join(ch for ch in s if ch.isalnum())
```

Indexa también por la **cara frontal** de las cartas de doble cara: las listas suelen escribir
"Bofur, Reliable Guardian" y Scryfall guarda "Bofur, Reliable Guardian // Concerted Care".

## Colapsar a pool jugable

```python
pool[oracle_id] = {
    'name': impresion_en_ingles['name'],   # el texto oracle en inglés manda
    'qty':  suma de quantity de todas las filas,
    ...campos de la impresión en inglés
}
```

Para los datos de la carta usa la impresión **en inglés** si existe: en otros idiomas Scryfall
devuelve el texto traducido en `printed_text`, pero conviene trabajar siempre con `oracle_text`.

## Reportar al usuario

Después de cargar, muestra siempre:

- Cartas distintas y copias físicas totales
- Cuántas filas se fusionaron por idioma (suele sorprender)
- Legalidad por formato (`legal_std / legal_pau / legal_brawl`)
- Filas que no resolvieron, con nombre e ID, para que las revise
