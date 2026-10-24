# The Corner at Dawn — an autopoietic street performance

An original piece of digital street music, performed by a self-playing
system (`perform.py`) for poidh bounty #1455 "Share your digital street
music performance".

**Listen:** `corner-at-dawn.mp3` (or watch `corner-at-dawn.mp4`)

## The performer

No samples, no loops, no DAW. One Python program walks onto the corner and
plays, start to finish, in a single pass:

- **Fingerpicked guitar** — Karplus-Strong plucked strings, arpeggiating
  Am(add9) – Fmaj7 – Cmaj7 – G6 (the chords of first light).
- **An improvising lead** — a second string voice that random-walks over the
  chord tones and pentatonic colour, deciding each phrase as it goes. It
  rests when it feels like it.
- **Bass + street percussion** — root-note bass, a foot-stomp thump and a
  hand shaker, all synthesized from envelopes.

Arrangement: alone on the corner (intro) → the tune arrives (theme) →
showing off a little (variation) → a hush while a passer-by stops
(breakdown) → reprise for the small crowd → one last chord, left ringing.

## The rules of the street

Per the bounty: recorded in one take, **no audio filters** — no EQ, no
compression, no reverb. The only processing is a **noise gate** under
−52 dB (explicitly allowed) and final peak normalization so the file
doesn't clip. Rendered dry at 44.1 kHz, 78 seconds.

The performance is seeded (1455), so the composition is fixed the way a
busker's arrangement settles after a week on the same corner — run
`perform.py` anywhere and it plays the same set.

## Run it

```sh
python3 perform.py corner-at-dawn.wav   # needs only numpy
```

Dedicated to the public domain under CC0 1.0, same as the performance.
