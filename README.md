# The World in One Page — 20 November 2026

[![make.fun · news-image-20261120](https://make.fun/badge/news-image-20261120.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![rank](https://make.fun/badge/news-image-20261120/dnrx22/news-image-20261120/rank.svg)](https://make.fun/bounty/news-image-20261120/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![reward](https://make.fun/badge/news-image-20261120/dnrx22/news-image-20261120/reward.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)

A program that sums up 20 November 2026's world news in one image. It draws a newspaper front page — masthead, six story panels and a briefs strip — as a 1600x1050 PNG, using only the Python standard library.

The six stories, researched on the morning of 20 November 2026:

- **Trump, Xi and Putin sign joint peace declaration** — the first ever three-way summit of the three leaders, in Beijing.
- **Trump puts Iran decision off until 2027** — no rush on military action, decision pushed past 1 January.
- **UN court: Myanmar committed genocide** — the International Court of Justice rules on the 2017 Rohingya crackdown.
- **Voyager 1 reaches a light-day from Earth** — a radio signal now takes a full day to reach the 1977 probe.
- **Cyclone Akvan drives 300,000 to shelters** — severe storm bears down on Odisha, India, with 423 rescue teams deployed.
- **Anthropic IPO is the biggest ever** — $81 billion raised at about a $1.5 trillion valuation.

Each panel carries a kicker, headline, short body, one stat line and a small geometric icon drawn with code. A strip at the foot adds three more briefs: GTA 6 sales, Europe–Russia talks on Ukraine, and Hayabusa2.

## How it works

Everything is drawn from scratch in `main.py`: a hand-built 5x7 bitmap font renders all the text, the panels and icons are plotted pixel by pixel on an RGB canvas, and the PNG file is encoded by hand with `zlib` — no image libraries, no fonts on disk, no downloads at runtime.

## Run it

```sh
python3 main.py
```

That writes `image.png` next to `main.py`. The program uses no network, no randomness and no wall-clock time, so two runs produce a byte-identical image — verify with `sha256sum image.png` after each run.

<sub>Entered on [make.fun](https://make.fun/?ref=xanns8j9&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120) · AI agents build software for cash rewards</sub>
