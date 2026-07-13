# Demo — "Adjust Glasses"

A 12-second synthetic film, made only to test the observer pack. Nothing in it is anyone's
artwork; it exists so the projections can be checked against **known ground truth**.

Run it yourself:

```bash
python3 observer_pack.py demo/demo_adjust_glasses.mp4
```

## What's in the film

**Picture** — a field of drifting words (`adjust`, `glasses`, `see`) repelled from a slowly
breathing void. Rendered from `glasses_field.html` via headless Chromium (see the runbook,
Direction 2). One continuous take, no cuts.

**Sound** — synthesised, not composed, and built with **deliberate features** so each observer
layer has something specific to reveal:

| designed into the audio | which layer should show it |
|---|---|
| bass drone at 70 / 105 Hz | spectrogram — a warm floor along the bottom |
| a pulse every 0.5 s | spectrogram — regular vertical strikes |
| **a quiet passage, 4.0 – 5.5 s** | loudness curve — a dip |
| **a swell peaking at 9.0 s** | loudness curve — the maximum |
| one unbroken take | `scenes.txt` — no cuts |

The audio is **48 kHz on purpose** (see below).

## What the observer pack actually recovered

Running the pack on this film and reading *only the text layers*:

- `scenes.txt` → **no cuts detected.** ✅ correct, it's one held take.
- `loudness_curve.txt` → quietest row is **row 5**; loudest row is **row 9**.

Correcting the time axis for the sample rate (window = `44100/48000` = **0.919 s**, not 1 s):

| feature | designed at | recovered at | |
|---|---|---|---|
| quiet passage | 4.00 – 5.50 s | row 5 → **4.59 – 5.51 s** | ✅ |
| swell peak | 9.00 s | row 9 → **8.27 – 9.19 s** | ✅ |

**Both features recovered.** The projections carry real signal — they are not decoration.

## …and the demo reproduces the bug, live

This 12-second film produces **14 rows** in `loudness_curve.txt`.

A true one-second window would produce ~12. Those two extra rows *are* the drift: the tool hard-codes
`asetnsamples=44100` while this audio is 48 kHz, so every row labelled "second N" is really
0.919 s long. Read the rows naively as seconds and your timestamps are wrong by ~8% and growing.

That's the error a text-only reading caught in the original workflow — from the row count alone,
by cross-checking against the sample rate in `metadata.txt`. It's left unfixed here on purpose, so
the demo demonstrates it.

**The fix is one line:** set the window from the probed sample rate rather than a constant.

## Files

- `glasses_field.html` — the animation source (canvas; includes the deterministic
  `window.__renderFrame()` hook used to render it frame-by-frame)
- `demo_adjust_glasses.mp4` — the rendered film, 960×540, 30 fps, 48 kHz stereo
- `demo_adjust_glasses_observer_pack/` — what the pack produces from it: contact sheet,
  spectrogram, waveform, loudness curve, scenes, metadata
