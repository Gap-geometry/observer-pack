#!/usr/bin/env python3
"""
observer_pack.py — render an mp4 into layers every kind of observer can read.

Usage:    python observer_pack.py video.mp4
Output:   video_observer_pack/   containing:
  contact_sheet.png   - 12 frames tiled across the duration   (vision observers)
  spectrogram.png     - the audio as frequency-vs-time image  (vision observers)
  waveform.png        - the audio's amplitude silhouette      (vision observers)
  loudness_curve.txt  - per-second RMS level, plain text      (any text observer)
  scenes.txt          - detected cut timestamps, plain text   (any text observer)
  metadata.txt        - streams, duration, fps, resolution    (any text observer)

Requires: ffmpeg + ffprobe on PATH. Python stdlib only.
House principle: per-observer rendering — same object, honest projections,
each teammate reads the layer their senses allow. 🖤📐
"""
import subprocess, sys, os, json, re

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)

def main(path):
    base = os.path.splitext(os.path.basename(path))[0]
    out = f"{base}_observer_pack"
    os.makedirs(out, exist_ok=True)

    # --- metadata (text layer) ---
    meta = run(["ffprobe", "-v", "error", "-show_format", "-show_streams",
                "-of", "json", path])
    info = json.loads(meta.stdout or "{}")
    with open(f"{out}/metadata.txt", "w", encoding="utf-8") as f:
        dur = float(info.get("format", {}).get("duration", 0))
        f.write(f"file: {os.path.basename(path)}\nduration: {dur:.2f} s\n")
        for s in info.get("streams", []):
            if s.get("codec_type") == "video":
                f.write(f"video: {s.get('width')}x{s.get('height')} "
                        f"{s.get('codec_name')} {s.get('avg_frame_rate')} fps\n")
            if s.get("codec_type") == "audio":
                f.write(f"audio: {s.get('codec_name')} {s.get('sample_rate')} Hz "
                        f"{s.get('channels')} ch\n")
    dur = max(dur, 0.1)

    # --- contact sheet: 12 frames, evenly spaced (vision layer) ---
    fps_expr = 12.0 / dur
    run(["ffmpeg", "-y", "-v", "error", "-i", path,
         "-vf", f"fps={fps_expr},scale=320:-1,tile=4x3",
         "-frames:v", "1", f"{out}/contact_sheet.png"])

    # --- spectrogram + waveform (vision layer for the ears) ---
    run(["ffmpeg", "-y", "-v", "error", "-i", path,
         "-lavfi", "showspectrumpic=s=1280x480:legend=1",
         f"{out}/spectrogram.png"])
    run(["ffmpeg", "-y", "-v", "error", "-i", path,
         "-lavfi", "showwavespic=s=1280x300:colors=orange",
         f"{out}/waveform.png"])

    # --- per-second loudness curve (pure text layer) ---
    r = run(["ffmpeg", "-v", "info", "-i", path,
             "-af", "asetnsamples=44100,astats=metadata=1:reset=1,"
                    "ametadata=print:key=lavfi.astats.Overall.RMS_level:file=-",
             "-f", "null", "-"])
    levels = re.findall(r"RMS_level=(-?[\d.]+|-inf)", r.stdout)
    with open(f"{out}/loudness_curve.txt", "w", encoding="utf-8") as f:
        f.write("second\tRMS_dB\tbar\n")
        for i, v in enumerate(levels):
            db = -90.0 if v == "-inf" else float(v)
            bar = "#" * max(0, int((db + 60) / 2))   # -60dB..0dB -> 0..30 chars
            f.write(f"{i:>4}\t{db:7.1f}\t{bar}\n")

    # --- scene cuts (pure text layer) ---
    r = run(["ffmpeg", "-v", "info", "-i", path,
             "-vf", "select='gt(scene,0.3)',metadata=print:file=-",
             "-f", "null", "-"])
    times = re.findall(r"pts_time:([\d.]+)", r.stdout)
    with open(f"{out}/scenes.txt", "w", encoding="utf-8") as f:
        f.write("detected cuts (scene-change > 0.3):\n")
        f.write("\n".join(f"  {float(t):7.2f} s" for t in times) or "  none detected")
        f.write("\n")

    print(f"observer pack ready: {out}/")
    print("  vision layer : contact_sheet.png, spectrogram.png, waveform.png")
    print("  text layer   : loudness_curve.txt, scenes.txt, metadata.txt")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python observer_pack.py video.mp4"); sys.exit(1)
    main(sys.argv[1])
