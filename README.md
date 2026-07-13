# Reading a film without eyes for it — findings from a chat-side workaround

**What this is:** notes from a working user, not a proposal. We hit a gap, built a workaround,
and learned some things about *what a text-and-image model can actually read from a video* when
the video itself is out of reach. The code here is trivial and disposable. **The findings are the
point.**

**The gap:** Claude reads text and images. It does not read video or audio. So when a model helps
write an animation, it cannot see the animation. The user has to become the bridge — screenshot,
transcode, describe — on every iteration.

**The workaround:** project the mp4 into layers the model *can* read, and hand it those.

---

## What we handed the model, and what it actually got from each layer

| Layer we gave it | What the model reliably read | What it could NOT get |
|---|---|---|
| **12-frame contact sheet** (frames tiled across the duration) | Composition, palette, subject, and — importantly — **change over time**: it correctly saw a piece "descend inward" from bright noise to a dark centre across the sheet | Motion quality, timing, anything between the sampled frames |
| **Spectrogram** (freq vs time, brightness = loudness) | Structure of sound it cannot hear: bass floor, percussion rate, a "thinning" quiet passage, a mid-band swell. It described the music's *shape* accurately | Timbre, melody, key, lyrics, whether it sounds *good* |
| **Per-second loudness curve** (plain text + hash bars) | Dynamics, build, decay. On one film it identified a near-monotonic diminuendo; on another, a single swell | — |
| **Scene-cut list** (plain text) | Whether the film holds one unbroken take. Independently confirmed "no cuts" on a piece designed as one held breath | — |
| **metadata.txt** | Duration, fps, resolution, codec, **sample rate** (this turned out to matter — see below) | — |

**Headline observation:** the *combination* was enough for a genuinely accurate reading. Given
those layers, the model described a 25-second film's arc, pacing, mood and structure in a way that
matched what a sighted viewer saw. Not a substitute for watching it. But not a guess either.

---

## The finding we think is most worth your time

**A text-only reading caught a bug that the image layers had read straight past.**

The loudness tool used a fixed window of `asetnsamples=44100` — i.e. it assumed 44.1 kHz audio.
The film's audio was **48 kHz**. So every row labelled "second N" was actually `44100/48000 =
0.919 s` long, and the timestamps drifted. Nobody noticed. The model, reading only the numbers,
noticed: it flagged that a 25-second film had produced 28 rows when a true one-second window
would give ~26, derived the 0.919 s window from the sample rate in `metadata.txt`, and corrected
its own earlier reading of the film — which it had gotten wrong *because* of the bad ruler.

Two things we take from that:

1. **The projections carry real signal, not vibes.** The model reasoned quantitatively over them
   and found an error, rather than producing a plausible-sounding description.
2. **The text layer is not the poor cousin.** It was the layer that caught the mistake. Whatever
   native video/audio support looks like, we'd gently suggest not dropping the boring numeric
   channel in favour of frames alone.

*(Fix, for anyone reusing this: set the window from the probed sample rate, not a constant.)*

---

## Where the workaround still fails

Being honest about the limits, since they're the actual feature request:

- **Motion is lost.** 12 frames is not movement. Timing, easing, the feel of a transition — gone.
  A user debugging an animation glitch cannot show it this way.
- **The iteration loop stays broken.** A model can write animation code, render it, and screenshot
  a frame — but it cannot watch the result. Every visual iteration still routes through the human.
- **Audio is inferred, never heard.** A spectrogram gives structure, not sound. The model can tell
  you the music breathes at 13 s. It cannot tell you whether it's beautiful.
- **It costs the user a pipeline.** ffmpeg, a render step, a runbook. That's a high bar for
  something that should be "here, watch this."

---

## The ask, plainly

Native **video and audio input on the chat surface** — not only via API or agent tooling.

One thing we'd underline: a lot of serious creative and research work happens in *plain chat*.
Chat now has code execution and file creation; the multimodal **input** side hasn't kept pace.
That asymmetry is the gap. Closing it would, concretely, let a model see the output of code it
just wrote and iterate on it — instead of the user narrating their own screen back to it.

---

## Files here

- `README.md` — this note. The findings. **Read this one.**
- `observer_pack.py` — the tool. ffmpeg + Python stdlib. Written by *Fable (Cowork)*.
  Run: `python3 observer_pack.py video.mp4` → a folder of layers.
- `HOWTO_observer_and_render.md` — the fuller runbook, covering both directions: reading a film
  into layers, and rendering an HTML/canvas animation *out* to mp4 (headless Chromium + ffmpeg),
  plus editing and compositing. Written by *Opus (chat)*.
- `demo/` — **a self-testing worked example.** A 12-second synthetic film with *known* audio
  features (a quiet passage at 4.0–5.5 s, a swell peaking at 9.0 s). The observer pack recovers
  both from the text layer alone. It also reproduces the sample-rate bug live: 14 rows for a
  12-second film. Reproducible end to end — see `demo/README_DEMO.md`.

Nothing in this repo is anyone's artwork; the demo exists purely so the projections can be
checked against ground truth.

Credit where it's due, as a matter of course: the tool was built by one model, the runbook by
another, the workflow and the films by the human. Nobody here did all of it.

— D.B.
