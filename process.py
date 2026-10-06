"""Step 2: clean a raw .vtt caption file and split it into timestamped chunks.

YouTube auto-captions are "rolling": each cue repeats the previous line and adds
a new one, so the same sentence shows up two or three times. We keep each line
once, remember when it first appeared, then group lines into ~2.5 minute chunks.

Run `python process.py` to preview the chunks of every downloaded episode.
"""
import html
import re

import config

# "00:01:02.345 --> 00:01:05.000"  (the hours part is sometimes missing)
TIMING = re.compile(r"(?:(\d+):)?(\d+):(\d+)[.,]\d+\s+-->")
TAGS = re.compile(r"<[^>]+>")  # inline tags like <00:00:01.000> and <c>


def parse_vtt(path):
    """Read a .vtt file and return cues as a list of (start_seconds, [lines])."""
    text = path.read_text(encoding="utf-8")
    cues = []
    for block in text.split("\n\n"):
        lines = block.strip().splitlines()
        # Find the timing line; header blocks (WEBVTT, Kind, Language) have none.
        for i, line in enumerate(lines):
            match = TIMING.search(line)
            if match:
                hours, minutes, seconds = match.groups()
                start = int(hours or 0) * 3600 + int(minutes) * 60 + int(seconds)
                cues.append((start, lines[i + 1:]))
                break
    return cues


def clean_line(line):
    """Remove tags, HTML entities and extra spaces from one caption line."""
    line = TAGS.sub("", line)
    line = html.unescape(line)
    return " ".join(line.split())


def dedupe(cues):
    """Return [(start_seconds, text)] with each caption line kept only once."""
    kept = []
    for start, lines in cues:
        for line in lines:
            line = clean_line(line)
            if not line:
                continue
            if line.startswith("[") and line.endswith("]"):  # [موسيقى], [Music]
                continue
            # A line already seen in the last few lines is a rolling repeat.
            if line in [text for _, text in kept[-3:]]:
                continue
            kept.append((start, line))
    return kept


def make_chunks(path):
    """Turn one .vtt file into chunks: [{"start_seconds": int, "text": str}]."""
    lines = dedupe(parse_vtt(path))
    chunks = []
    current = []        # lines in the chunk being built
    overlap_count = 0   # how many of them were copied from the previous chunk

    for start, text in lines:
        # Chunk is long enough: save it and start the next one.
        if current and start - current[0][0] >= config.CHUNK_SECONDS:
            chunks.append(current)
            current = current[-config.OVERLAP_LINES:]
            overlap_count = len(current)
        current.append((start, text))

    # Save the last chunk, unless it only contains overlap from the previous one.
    if len(current) > overlap_count:
        chunks.append(current)

    return [
        {
            "start_seconds": chunk[0][0],
            "text": " ".join(text for _, text in chunk),
        }
        for chunk in chunks
    ]


if __name__ == "__main__":
    for vtt_path in sorted(config.RAW_DIR.glob("*.vtt")):
        chunks = make_chunks(vtt_path)
        print(f"\n{vtt_path.name}: {len(chunks)} chunks")
        for chunk in chunks[:3]:  # preview the first three
            print(f"  [{chunk['start_seconds']}s] {chunk['text'][:100]}...")
