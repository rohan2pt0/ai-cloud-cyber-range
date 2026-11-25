# Third-party notices

Parts of SecuRAX made by someone else, with their licences. Each licence text travels with the files it covers.

## Tesseract.js text reader and its core wasm

- **What:** the offline text reader bundled in the Life OS (reading text out of an image you paste in), and the WebAssembly engine core it runs.
- **Files:** `guiding-map/ocr/tesseract.min.js`, `guiding-map/ocr/worker.min.js`, `guiding-map/ocr/tesseract-core-simd-lstm.wasm.js`
- **Name and version:** Tesseract.js 5.1.1 (the reader and its worker) and its WebAssembly core (tesseract.js-core)
- **Licence:** Apache License 2.0 — the full text is in `guiding-map/ocr/LICENSE-APACHE-2.0.txt`
- **Upstream:** https://github.com/naptha/tesseract.js and https://github.com/naptha/tesseract.js-core
- **Where it is used:** the Life OS text reader (`guiding-map/ocr/`), entirely on the device.

## English tessdata language file

- **What:** the English trained language data the text reader needs.
- **Files:** `guiding-map/ocr/eng.traineddata.gz`
- **Name and version:** the English traineddata for Tesseract, from the tessdata project (the 4.0.0 set Tesseract.js loads by default)
- **Licence:** Apache License 2.0 — the full text is in `guiding-map/ocr/LICENSE-APACHE-2.0.txt`
- **Upstream:** https://github.com/tesseract-ocr/tessdata (packaged at https://github.com/naptha/tesseract.js-data)
- **Where it is used:** the Life OS text reader (`guiding-map/ocr/`), entirely on the device.

## Typefaces: Jost and Instrument Serif

- **What:** the two typefaces the Life OS is set in.
- **Files:** `guiding-map/fonts/Jost-Variable.woff2` with its licence in `guiding-map/fonts/Jost-OFL.txt`; `guiding-map/fonts/InstrumentSerif-Regular.woff2` with its licence in `guiding-map/fonts/Instrument_Serif-OFL.txt`
- **Name and version:** Jost (The Jost Project Authors, 2020); Instrument Serif (The Instrument Serif Project Authors, 2022)
- **Licence:** SIL Open Font License, Version 1.1 — the full text of each sits beside the font file it covers
- **Upstream:** https://github.com/indestructible-type/Jost and https://github.com/Instrument/instrument-serif
- **Where it is used:** every screen of the Life OS (`guiding-map/`) and the product site (`website/`, copied there as `sans.woff2` and `serif.woff2` at build time), self-hosted; no font is fetched from the network.
