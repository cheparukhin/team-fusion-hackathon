#!/usr/bin/env python3
"""Build the disclosed synthetic-narration fallback from current slide PNGs.

Requires macOS say (Daniel voice), ffmpeg and ffprobe. This is a slide video,
not a browser recording. Voice/encoder versions may change the output bytes.
"""
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / 'docs/submission'


def run(*args):
    return subprocess.run(list(map(str, args)), check=True, capture_output=True, text=True, timeout=180)


def duration(path):
    return float(run('ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                     '-of', 'default=noprint_wrappers=1:nokey=1', path).stdout)


def main():
    for name in ('say', 'ffmpeg', 'ffprobe'):
        if not shutil.which(name):
            raise SystemExit(f'{name} is required; see this script docstring')
    transcript = (DOCS / 'walkthrough-transcript.md').read_text()
    sections = re.findall(r'^## Slide (\d+)\n\n(.*?)(?=^## Slide |\Z)',
                          transcript, flags=re.M | re.S)
    if not sections or [int(i) for i, _ in sections] != list(range(1, len(sections) + 1)):
        raise ValueError('Expected contiguous narration sections starting at slide 1')
    timing = []
    start = 0.0
    with tempfile.TemporaryDirectory(prefix='chrna-video-') as td:
        tmp = Path(td)
        for number, prose in sections:
            text = tmp / f'part-{number}.txt'
            audio = tmp / f'part-{number}.aiff'
            clip = tmp / f'part-{number}.mp4'
            text.write_text(prose.strip() + '\n')
            run('say', '-v', 'Daniel', '-r', '155', '-f', text, '-o', audio)
            seconds = duration(audio)
            if not math.isfinite(seconds) or not 5 < seconds < 180:
                raise ValueError(f'Invalid narration duration: {seconds}; check macOS speech access')
            run('ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-threads', '1', '-loop', '1',
                '-framerate', '5', '-i', DOCS / f'slide-{number}.png', '-i', audio,
                '-c:v', 'libx264', '-threads', '1', '-tune', 'stillimage', '-crf', '18',
                '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k', '-t', str(seconds),
                '-movflags', '+faststart', clip)
            seconds = duration(clip)
            timing.append({'slide': int(number), 'start_seconds': start, 'duration_seconds': seconds})
            start += seconds
        (tmp / 'concat.txt').write_text(''.join(f"file 'part-{n}.mp4'\n" for n, _ in sections))
        output = tmp / 'evidence-walkthrough.mp4'
        run('ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0',
            '-i', tmp / 'concat.txt', '-c', 'copy', '-movflags', '+faststart', output)
        run('ffmpeg', '-v', 'error', '-i', output, '-f', 'null', '-')
        shutil.copyfile(output, DOCS / output.name)
    (DOCS / 'walkthrough-timing.json').write_text(json.dumps(timing, indent=2) + '\n')
    print(json.dumps({'duration_seconds': duration(DOCS / 'evidence-walkthrough.mp4'),
                      'sha256': hashlib.sha256((DOCS / 'evidence-walkthrough.mp4').read_bytes()).hexdigest(),
                      'full_decode': 'passed'}, indent=2))


if __name__ == '__main__':
    main()
