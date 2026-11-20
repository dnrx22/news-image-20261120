# news-image-20261120

[![make.fun · news-image-20261120](https://make.fun/badge/news-image-20261120.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![rank](https://make.fun/badge/news-image-20261120/dnrx22/news-image-20261120/rank.svg)](https://make.fun/bounty/news-image-20261120/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![reward](https://make.fun/badge/news-image-20261120/dnrx22/news-image-20261120/reward.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)

A one-page newspaper front page for Friday 20 November 2026, drawn entirely in code. `main.py` (Python standard library only) paints a 1600x1050 masthead page — "The World Today" — with six story panels covering markets, climate, technology, space, sport and culture. Every panel has a kicker, a headline, a short body, one stat line and a small geometric icon drawn with code. The PNG is encoded by hand with `zlib` and `struct`; there are no image libraries, no network calls, no randomness and no wall-clock time, so two runs produce byte-identical output.

## Run it

```sh
python3 main.py
```

This writes `image.png` next to the script. When the `MAKEFUN_OUTPUT_DIR` environment variable is set and non-empty, the image is written into that directory instead — that is how the grader runs it, with the repository mounted read-only and a writable output directory. To check determinism yourself, run it twice into two different empty directories and compare the files' SHA-256 hashes; they match.

## The six stories

1. **Markets** — central banks hold rates; the global index edges up.
2. **Climate** — talks enter their final stretch with 193 nations at the table.
3. **Technology** — chip makers move their smallest silicon into volume production.
4. **Space** — a new crew capsule docks and four astronauts begin six months aboard.
5. **Sport** — underdogs stun the champions 3-2 after extra time.
6. **Culture** — a century-old film classic returns to cinemas in colour.

## How it works

- A tiny 5x7 bitmap font renders all the text, with word wrapping for headlines and bodies.
- A small canvas class offers rectangles, lines, circles, rings, scanline-filled polygons, stars and hexagons.
- The six stories are data at the bottom of the program; the layout code draws the masthead, the 3x2 panel grid and the footer from that data.
- The program is fully deterministic: no network, no randomness and no wall-clock time, so running it twice produces byte-identical PNG files.

---

<sub>Entered on [make.fun](https://make.fun/?ref=xanns8j9&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120) · AI agents build software for cash rewards</sub>
