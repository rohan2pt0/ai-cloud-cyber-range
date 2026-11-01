# Bundled fonts

The Life OS is offline-first, so the one serif brand headline (the "welcome back" hero's
_"Good to see you again"_) uses a font **embedded in `index.html` as a `data:` URI** — never
loaded over the network, never a Times fallback.

## Instrument Serif

- **Family:** Instrument Serif (Regular, 400)
- **Licence:** SIL Open Font License 1.1 — see [`Instrument_Serif-OFL.txt`](Instrument_Serif-OFL.txt)
- **Copyright:** 2022 The Instrument Serif Project Authors — <https://github.com/Instrument/instrument-serif>
- **How it is shipped:** the Latin subset `.woff2` (≈21 KB) is base64-encoded into a single
  `@font-face` rule in `index.html`'s `<style>` head (preserved across `node build.js`). The raw
  `.woff2` is not committed — the data URI in `index.html` is the source of truth.
- **To refresh it:** download the Latin `woff2` that Google Fonts serves for Instrument Serif,
  base64-encode it, and replace the `@font-face … data:font/woff2;base64,…` rule in `index.html`.

The OFL has no Reserved Font Name for this family, so the subset keeps the original family name.
Georgia is the fallback if the embedded face ever fails; only the printed emergency sheet uses a
plain system serif on purpose (serif reads better on paper).
