"""Join one or more raw takes into a single SDR editing master.

Writes, inside the project:
  assets/source.mov        H.264 (CRF 12) + PCM, CFR, BT.709. HDR (HLG/PQ) is tone-mapped.
  assets/sources.json      offset of each take on the master timeline
  work/source.16k.wav      16 kHz mono audio for transcription and silence detection

usage: python3 make_master.py <project-dir> <take1> [<take2> ...] [--fps 30]
Takes are joined in the order given. Each is trimmed to whole frames so offsets stay exact.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ap = argparse.ArgumentParser(description="Join raw takes into one SDR editing master.")
ap.add_argument("project")
ap.add_argument("takes", nargs="+")
ap.add_argument("--fps", type=int, default=30)
a = ap.parse_args()
proj, takes, fps = Path(a.project), [Path(t) for t in a.takes], a.fps
(proj / "assets").mkdir(parents=True, exist_ok=True)
(proj / "work").mkdir(parents=True, exist_ok=True)

TONEMAP = ("zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,"
           "tonemap=mobius:param=0.3:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p")


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "stream=codec_type,color_transfer,width,height:format=duration",
                          "-of", "json", str(path)], capture_output=True, text=True, check=True).stdout
    j = json.loads(out)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    has_audio = any(s["codec_type"] == "audio" for s in j["streams"])
    return float(j["format"]["duration"]), v.get("color_transfer", ""), has_audio


inputs, chains, offsets, t = [], [], [], 0.0
for i, take in enumerate(takes):
    dur, trc, has_audio = probe(take)
    if not has_audio:
        raise SystemExit(f"{take} has no audio stream")
    frames = int(dur * fps)  # whole frames only
    seg = frames / fps
    hdr = trc in ("arib-std-b67", "smpte2084")
    vchain = f"[{i}:v]fps={fps},trim=end_frame={frames},setpts=PTS-STARTPTS" + ("," + TONEMAP if hdr else ",format=yuv420p")
    achain = f"[{i}:a]aresample=48000,atrim=0:{seg:.6f},apad=whole_dur={seg:.6f},asetpts=PTS-STARTPTS"
    chains += [vchain + f"[v{i}]", achain + f"[a{i}]"]
    inputs += ["-i", str(take)]
    offsets.append({"file": str(take), "offset": round(t, 6), "duration": round(seg, 6), "frames": frames,
                    "hdrToneMapped": hdr, "colorTransfer": trc})
    t += seg

n = len(takes)
graph = ";".join(chains) + ";" + "".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a]"
master = proj / "assets/source.mov"
subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", graph, "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-preset", "medium", "-crf", "12", "-g", str(fps), "-pix_fmt", "yuv420p",
                "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                "-c:a", "pcm_s16le", str(master)], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(master), "-vn", "-ac", "1", "-ar", "16000",
                str(proj / "work/source.16k.wav")], check=True)
(proj / "assets/sources.json").write_text(json.dumps({"fps": fps, "duration": round(t, 6), "takes": offsets}, indent=1))
print(json.dumps({"master": str(master), "duration": round(t, 3), "takes": offsets}, indent=1))
