# THE WORLD TODAY — 26 November 2026

[![news-image-20261126](https://make.fun/badge/news-image-20261126.svg)](https://make.fun/bounty/news-image-20261126)
[![rank](https://make.fun/badge/news-image-20261126/Dhanzganz/makefun-news-image-20261126-entry/rank.svg)](https://make.fun/bounty/news-image-20261126)
[![reward](https://make.fun/badge/news-image-20261126/Dhanzganz/makefun-news-image-20261126-entry/reward.svg)](https://make.fun/bounty/news-image-20261126)

A newspaper front page that sums up the world's news of **Thursday 26 November 2026** in a single image.

## What's on the page

- **Lead — Hong Kong, one year on.** A year after the Wang Fuk Court
  fire killed 168 people, survivors and bereaved families return to
  Tai Po on Thursday. The towers stand empty, nearly 2,000 families
  are still displaced, and families are asking who will be held to
  account.
- **Europe and Japan reach Mercury.** After an eight-year journey,
  BepiColombo slips into orbit around the smallest planet.
- **Pakistan's first astronaut flies.** Muhammad Zeeshan Ali joins
  China's Shenzhou-24 mission, the first foreign astronaut bound for
  the Tiangong station.
- **U.S. convicts Huawei of fraud.** A U.S. jury finds Huawei guilty
  of fraud and trade-secret theft; new tariffs are readied.
- **Also today:** Colombia marks 10 years since its peace accord;
  India celebrates Constitution Day while Gukesh chases the world
  chess crown; Senegal declared rightful AFCON champions by the
  court; Bangladesh raises garment wages 36%; China opens a graft
  probe into Shanghai party chief Chen Jining; Flipkart chief Kalyan
  Krishnamurthy to step down in December.

## How it is made

`main.py` is pure Python 3 standard library. The grader's Python has
no Pillow, so the program draws everything itself: its own 5x7 bitmap
font, its own vector drawing (dusk skyline, planet and orbit, rocket
and station, scales of justice), and its own PNG encoder. Two runs
write byte-identical files.

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py   # writes out/entry.png
```

Output: `entry.png`, 1024x1024, under 1 MiB, deterministic.

## License

MIT — see [LICENSE](LICENSE).
