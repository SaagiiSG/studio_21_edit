"""Transcribe short ranges of a 16 kHz mono WAV with word timestamps (absolute times).

usage: python3 chunk_asr.py <audio.wav> <start>-<end> [<start>-<end> ...]

Language: set STUDIO21_LANG (default "en"; Mongolian is "mn").
"""
import os
import sys
import wave

import numpy as np
from faster_whisper import WhisperModel

path = sys.argv[1]
with wave.open(path) as wf:
    pcm = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0

model = WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=4)
for rng in sys.argv[2:]:
    a, b = (float(v) for v in rng.split("-"))
    seg_audio = pcm[int(a * 16000):int(b * 16000)]
    segs, _ = model.transcribe(seg_audio, language=os.environ.get("STUDIO21_LANG", "en"), word_timestamps=True, beam_size=5,
                               condition_on_previous_text=False, vad_filter=False)
    words = [f"{w.word.strip()}[{a + w.start:.2f}-{a + w.end:.2f}]" for s in segs for w in (s.words or [])]
    print(f"{rng}: {' '.join(words)}", flush=True)
