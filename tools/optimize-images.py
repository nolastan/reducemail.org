#!/usr/bin/env python3
"""Shrink the imported article images in place.

The Ghost export shipped full-size originals — several 2000px PNGs of
photographs weighing 3–6MB each. Articles render in a 720px column, so nothing
needs to be wider than 1600px, and a photograph saved as PNG is roughly ten
times the size of the same image as JPEG.

For each image this:
  * downscales so the longest edge is at most 1600px (never upscales),
  * re-encodes JPEGs at quality 85,
  * converts a PNG to JPEG when that saves a meaningful amount AND the PNG has
    no real transparency to lose.

Converted files change extension; `localize()` in import-blog.py falls back to
the sibling extension, so rerunning the importer picks the new names up.

    python3 tools/optimize-images.py [--dry-run]
"""

import os
import struct
import subprocess
import sys
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES = os.path.join(ROOT, "content", "images")

MAX_EDGE = 1600
# sips' quality scale runs hot — its 50 lands around libjpeg's 80, which is
# artifact-free on these photos at 1600px. Raising it mostly buys file size.
JPEG_QUALITY = "50"
# Only swap a PNG for a JPEG when the saving is worth the changed filename.
CONVERT_THRESHOLD = 0.6


def sips_get(path, *keys):
    args = ["sips"]
    for k in keys:
        args += ["-g", k]
    out = subprocess.run(args + [path], capture_output=True, text=True).stdout
    vals = {}
    for line in out.splitlines():
        line = line.strip()
        for k in keys:
            if line.startswith(k + ":"):
                v = line.split(None, 1)[1].strip()
                vals[k] = None if v == "<nil>" else v
    return vals


def png_has_transparency(path):
    """True only if some pixel is actually not fully opaque.

    `sips -g hasAlpha` reports the channel's presence, not its use, and most of
    these exports carry a fully-opaque alpha channel. Flattening those onto
    white is free; flattening a genuinely transparent one is not.
    """
    with open(path, "rb") as f:
        data = f.read()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return False

    pos = 8
    ihdr = None
    idat = []
    trns = False
    while pos + 8 <= len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        ctype = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        if ctype == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", body[:13])
        elif ctype == b"IDAT":
            idat.append(body)
        elif ctype == b"tRNS":
            trns = True
        elif ctype == b"IEND":
            break
        pos += 12 + length

    if ihdr is None:
        return True  # unreadable — assume the worst and leave it alone
    width, height, depth, color, _, _, interlace = ihdr

    if color in (0, 2):
        return trns
    if color == 3:
        return trns
    if depth != 8 or interlace:
        return True  # not worth decoding; keep the PNG

    channels = 4 if color == 6 else 2
    stride = width * channels
    try:
        raw = zlib.decompress(b"".join(idat))
    except zlib.error:
        return True

    prev = bytearray(stride)
    off = 0
    for _ in range(height):
        if off >= len(raw):
            break
        filt = raw[off]
        line = bytearray(raw[off + 1:off + 1 + stride])
        off += 1 + stride
        # Undo the per-scanline filter so alpha bytes are real values.
        if filt == 1:
            for i in range(channels, stride):
                line[i] = (line[i] + line[i - channels]) & 0xFF
        elif filt == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif filt == 3:
            for i in range(stride):
                left = line[i - channels] if i >= channels else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif filt == 4:
            for i in range(stride):
                a = line[i - channels] if i >= channels else 0
                b = prev[i]
                c = prev[i - channels] if i >= channels else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        if any(line[i] != 0xFF for i in range(channels - 1, stride, channels)):
            return True
        prev = line
    return False


def run(args):
    return subprocess.run(args, capture_output=True, text=True).returncode == 0


def optimize(path, dry_run):
    vals = sips_get(path, "pixelWidth", "pixelHeight", "format")
    w, h, fmt = vals.get("pixelWidth"), vals.get("pixelHeight"), vals.get("format")
    if not w or not h:
        print("  skip (unreadable): %s" % path)
        return 0, 0, None
    w, h, before = int(w), int(h), os.path.getsize(path)

    tmp_same = path + ".tmp-same"
    tmp_jpeg = os.path.splitext(path)[0] + ".tmp-jpeg"
    resize = ["-Z", str(MAX_EDGE)] if max(w, h) > MAX_EDGE else []

    # Candidate 1: same format, resized.
    subprocess.run(["cp", path, tmp_same], check=True)
    if resize:
        run(["sips"] + resize + [tmp_same])
    if fmt in ("jpeg", "jpg"):
        run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", JPEG_QUALITY,
             tmp_same, "--out", tmp_same])
    same_size = os.path.getsize(tmp_same)

    # Candidate 2: JPEG — only offered when nothing transparent would be lost.
    jpeg_size = None
    if fmt == "png" and not png_has_transparency(path):
        if run(["sips"] + resize + ["-s", "format", "jpeg", "-s", "formatOptions",
                                    JPEG_QUALITY, path, "--out", tmp_jpeg]):
            jpeg_size = os.path.getsize(tmp_jpeg)

    winner_path, winner_size, new_path = tmp_same, same_size, path
    if jpeg_size is not None and jpeg_size < same_size * (1 - CONVERT_THRESHOLD):
        winner_path, winner_size = tmp_jpeg, jpeg_size
        new_path = os.path.splitext(path)[0] + ".jpg"

    if winner_size >= before:
        for t in (tmp_same, tmp_jpeg):
            if os.path.exists(t):
                os.remove(t)
        return before, before, None

    if dry_run:
        for t in (tmp_same, tmp_jpeg):
            if os.path.exists(t):
                os.remove(t)
        return before, winner_size, (new_path if new_path != path else None)

    os.replace(winner_path, new_path)
    if new_path != path:
        os.remove(path)
    for t in (tmp_same, tmp_jpeg):
        if os.path.exists(t):
            os.remove(t)
    return before, winner_size, (new_path if new_path != path else None)


def main():
    dry_run = "--dry-run" in sys.argv
    files = []
    for dirpath, _, names in os.walk(IMAGES):
        for name in sorted(names):
            if name.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
                files.append(os.path.join(dirpath, name))

    total_before = total_after = 0
    renamed = []
    for path in sorted(files):
        before, after, new_path = optimize(path, dry_run)
        total_before += before
        total_after += after
        if new_path:
            renamed.append((path, new_path))

    print("%d files: %.1f MB -> %.1f MB (%.0f%% smaller)" % (
        len(files), total_before / 1e6, total_after / 1e6,
        100 * (1 - total_after / total_before) if total_before else 0))
    print("%d converted to JPEG" % len(renamed))


if __name__ == "__main__":
    main()
