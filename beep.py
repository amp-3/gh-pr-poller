#!/usr/bin/env python3
"""beep - 完了通知音を再生するモジュール（Windows / macOS 対応）"""

import math
import os
import platform
import struct
import subprocess
import tempfile
import wave


def _beep_windows(frequency, duration_ms):
    import winsound
    winsound.Beep(frequency, duration_ms)


def _beep_macos(frequency, duration_ms):
    sample_rate = 44100
    n_samples = int(sample_rate * duration_ms / 1000)
    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        with wave.open(tmp_path, "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            for i in range(n_samples):
                value = int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
                wf.writeframes(struct.pack("<h", value))
        subprocess.run(["afplay", tmp_path], check=True)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


def play_completion_beep():
    """完了通知音を再生する（800Hz + 1200Hz）"""
    system = platform.system()
    if system == "Windows":
        _beep_windows(800, 200)
        _beep_windows(1200, 200)
    elif system == "Darwin":
        _beep_macos(800, 200)
        _beep_macos(1200, 200)
    else:
        print(f"[beep] 未対応のOS: {system} - 通知音をスキップします")


def play_completion_beep_high():
    """完了通知音（高音）を再生する（1000Hz + 1400Hz）"""
    system = platform.system()
    if system == "Windows":
        _beep_windows(1000, 100)
        _beep_windows(1400, 100)
    elif system == "Darwin":
        _beep_macos(1000, 100)
        _beep_macos(1400, 100)
    else:
        print(f"[beep] 未対応のOS: {system} - 通知音をスキップします")
