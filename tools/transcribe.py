"""Local faster-whisper transcription -> herk-edit-kit word-level JSON.

usage: python3 transcribe.py <audio.wav> <out.json> <source-duration-secs> [model]
"""
import json
import sys
import wave

import numpy as np
from faster_whisper import WhisperModel

audio, out, duration = sys.argv[1], sys.argv[2], float(sys.argv[3])
model_name = sys.argv[4] if len(sys.argv) > 4 else "large-v3"

# Input is 16 kHz mono s16 WAV from ffmpeg; decode here to avoid PyAV version issues.
with wave.open(audio) as wf:
    assert wf.getframerate() == 16000 and wf.getnchannels() == 1 and wf.getsampwidth() == 2
    pcm = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0

model = WhisperModel(model_name, device="cpu", compute_type="int8", cpu_threads=4)
segments, info = model.transcribe(
    pcm,
    language="en",
    word_timestamps=True,
    vad_filter=False,
    condition_on_previous_text=False,
    beam_size=5,
)

words, seg_out = [], []
for seg in segments:
    seg_out.append({"start": round(seg.start, 3), "end": round(seg.end, 3), "text": seg.text.strip()})
    for w in seg.words or []:
        t = w.word.strip()
        if t:
            words.append({"text": t, "start": round(w.start, 3), "end": round(w.end, 3), "probability": round(w.probability, 3)})
    print(f"[{seg.start:6.2f} -> {seg.end:6.2f}] {seg.text.strip()}", flush=True)

doc = {
    "text": " ".join(w["text"] for w in words),
    "audio_duration_secs": duration,
    "language": info.language,
    "provider": f"faster-whisper/{model_name} (local)",
    "words": words,
    "segments": seg_out,
}
with open(out, "w") as f:
    json.dump(doc, f, indent=1)
print(f"wrote {out}: {len(words)} words")
