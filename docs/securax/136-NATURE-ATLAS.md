# 136. The nature atlas: design taken from the wonders people revere

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Started 14 November 2026: the atlas and its evidence are in place; the rings and the lock's aurora use it; the other wonders follow in slices (queue nature-atlas). [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**Principle:** `natures-design` (owner, 2026-11-14), with `signature-perfect`. **Data:** [`governance/nature-atlas.json`](../../governance/nature-atlas.json), one source for every SecuRAX app.

People have always revered sunrise, water, the northern lights, emeralds, a peacock's feather and the night sky. SecuRAX borrows from them so its apps feel calm and priceless. It does not guess at "nice colours": every entry is chosen by evidence and drawn from the physics of the real thing.

## How the 80/20 selection was made

Three kinds of evidence, so that "numbers don't lie":

1. **A global vote.** The New7Wonders of Nature campaign (2007–2011) drew about 100 million votes from over 220 countries and named seven: the Amazon, Ha Long Bay, Iguazu Falls, Jeju Island, Komodo, the Puerto Princesa underground river and Table Mountain. The vote had flaws (repeat voting, national campaigns), so it is one signal among three, not the only one. ([Wikipedia](https://en.wikipedia.org/wiki/New7Wonders_of_Nature), [New7Wonders](https://about.new7wonders.com/2011/11/11/top-14-finalists-in-the-new7wonders-of-nature))
2. **What people photograph.** Hashtag studies put Yosemite first among natural wonders (about 5 million posts), Niagara and Victoria Falls first among waterfalls, Everest and the Sahara in the top ten, and Iceland first in Europe. Hashtags are a rough proxy, and the studies differ in method. ([factmagazines](https://www.factmagazines.com/travel/ten-of-the-worlds-most-instgrammable-natural-wonders), [insauga](https://www.insauga.com/niagara-falls-has-over-10-times-the-instagram-posts-as-the-next-closest-waterfall-in-the-world/))
3. **The world's best nature photography.** The 2025 Wildlife Photographer of the Year grand title went to a picture made in Namibia's Namib desert, from 60,636 entries in 113 countries. ([Natural History Museum](https://www.nhm.ac.uk/discover/news/2025/october/wildlife-photographer-of-the-year-2025-winning-images.html), [National Geographic](https://www.nationalgeographic.com/animals/article/2025-wildlife-photographer-of-the-year))

## How the colours are taken: physics first

- **Aurora:** atomic oxygen emits at 557.7 nm (yellow-green, about 100 km up) and 630.0 nm (red, higher); nitrogen at 427.8 nm (violet-blue, the lower edge). Converted to screen colour they are `#bcff00`, `#ff4f00` and `#4700ff`. They are drawn as faint light added to the blue night sky, which is how the eye and the camera see them: emerald, not neon. ([Wikipedia: Aurora](https://en.wikipedia.org/wiki/Aurora), [AuroraWatch UK](https://wp.lancs.ac.uk/aurorawatchuk/2017/05/10/the-vivid-lights-what-causes-the-colour-of-the-aurora/))
- **Grand Prismatic Spring:** a sterile deep-blue centre, then rings of microbial mats sorted by temperature, from chlorophyll greens to carotenoid yellows, oranges and rusts. ([Wikipedia](https://en.wikipedia.org/wiki/Grand_Prismatic_Spring), [MicrobeWiki](https://microbewiki.kenyon.edu/index.php/The_grand_prismatic_spring))
- **Space images:** NASA's James Webb team uses chromatic ordering, with shorter wavelengths shown bluer and longer redder. SecuRAX uses the same order for any colour scale, so the order of the colours means the order of the values. ([NASA](https://science.nasa.gov/mission/webb/science-overview/science-explainers/how-are-webbs-full-color-images-made), [Astronomy](https://www.astronomy.com/science/jwst-sees-light-invisible-to-the-eye-these-scientists-decide-how-to-color-it))
- **Others:** sunrise by Rayleigh scattering, glacier blue from ice absorbing red, peacock blue from thin-film interference, the galaxy from a flat rotation curve and a density wave, and metals from their measured reflectance.

## The rules (from the atlas)

1. One natural element per surface, chosen for its meaning.
2. Physics first: emission lines, scattering, absorption, structural colour.
3. Draw light as light (added, low intensity, over dark) and materials from measured optics. Never a flat, saturated fill.
4. Never trade the contrast of text for beauty.
5. Let it rest when the person rests: reduced motion, and calm after engagement.

## In use today

- **Sunrise, emerald and peacock:** the three rings.
- **The Milky Way and a spiral galaxy:** the lock's night sky.
- **The aurora:** low over the lock's horizon.

The rest are mapped to the views they suit, and the `nature-atlas` item in [`governance/queue.json`](../../governance/queue.json) carries the next slices.
