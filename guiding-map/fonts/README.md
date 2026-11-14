# Bundled fonts

The Life OS is offline-first, so the one serif brand headline (the "welcome back" hero's
_"Good to see you again"_) uses a font **embedded in `index.html` as a `data:` URI** — never
loaded over the network, never a Times fallback.

## Instrument Serif

- **Family:** Instrument Serif (Regular, 400)
- **Licence:** SIL Open Font License 1.1 — see [`Instrument_Serif-OFL.txt`](Instrument_Serif-OFL.txt)
- **Copyright:** 2022 The Instrument Serif Project Authors — <https://github.com/Instrument/instrument-serif>
- **The file:** `InstrumentSerif-Regular.woff2` (the same Latin subset) is the source for the premium language
  (`governance/design.json` → `premium.type.display_font_file`). `governance/design.py` embeds it as a data URI in pages that open
  from disk, and a hosted page may link the file. A test checks the Life OS embed and this file are the same bytes.
- **How it is shipped in the Life OS:** the Latin subset `.woff2` (≈21 KB) is base64-encoded into a single
  `@font-face` rule in `index.html`'s `<style>` head (preserved across `node build.js`). 
- **To refresh it:** download the Latin `woff2` that Google Fonts serves for Instrument Serif,
  base64-encode it, and replace the `@font-face … data:font/woff2;base64,…` rule in `index.html`.

The OFL has no Reserved Font Name for this family, so the subset keeps the original family name.
Georgia is the fallback if the embedded face ever fails; only the printed emergency sheet uses a
plain system serif on purpose (serif reads better on paper).

## Jost (the shared sans, 2026-11-14)

- **Family:** Jost, variable (weights 100 to 900, upright), Latin subset.
- **Licence:** SIL Open Font License 1.1, see [`Jost-OFL.txt`](Jost-OFL.txt). Copyright 2020 The Jost Project Authors
  (<https://github.com/indestructible-type/Jost>), via the Fontsource package `@fontsource-variable/jost` 5.3.0.
- **Why:** a geometric sans in the Futura tradition, the classic text face of the great luxury houses; it pairs with the
  editorial serif above (display only). Text is sized by x-height (`font-size-adjust`), so the switch kept every layout.
- **How it is shipped:** `guiding-map/build.js` (the Life OS) and `governance/oskit.py` (every kit edition) embed
  `Jost-Variable.woff2` (about 27 KB) as a `data:` URI with the shared look (`shared/lux.css`). Offline, no network.
