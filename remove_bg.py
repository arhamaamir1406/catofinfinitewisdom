import cv2
import numpy as np
from rembg import remove, new_session
from PIL import Image
import imageio_ffmpeg
import subprocess
import os
import sys
import tempfile
import shutil

INPUT = "cat_video.mp4"
OUTPUT = "cat_background_removed.webm"

cap = cv2.VideoCapture(INPUT)
if not cap.isOpened():
    print("ERROR: Could not open video")
    sys.exit(1)

fps = cap.get(cv2.CAP_PROP_FPS)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
print(f"Video: {width}x{height} @ {fps:.1f}fps, {total} frames")

# isnet-general-use gives clean subject masks
session = new_session("isnet-general-use")

tmp_dir = tempfile.mkdtemp(prefix="rembg_frames_")
print(f"Temp frames: {tmp_dir}")

frame_idx = 0
while True:
    ret, frame = cap.read()
    if not ret:
        break
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb)
    result = remove(pil_img, session=session, bgcolor=None)  # RGBA output
    out_path = os.path.join(tmp_dir, f"frame_{frame_idx:06d}.png")
    result.save(out_path)
    frame_idx += 1
    if frame_idx % 10 == 0 or frame_idx == total:
        print(f"  {frame_idx}/{total}", flush=True)

cap.release()
print(f"Processed {frame_idx} frames.")

# Use bundled ffmpeg from imageio-ffmpeg (no system install needed)
ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
frame_pattern = os.path.join(tmp_dir, "frame_%06d.png")

cmd = [
    ffmpeg_exe, "-y",
    "-framerate", str(fps),
    "-i", frame_pattern,
    "-c:v", "libvpx-vp9",
    "-pix_fmt", "yuva420p",
    "-b:v", "0", "-crf", "30",
    "-auto-alt-ref", "0",
    OUTPUT,
]
print(f"Assembling {OUTPUT}...")
proc = subprocess.run(cmd, capture_output=True, text=True)
if proc.returncode != 0:
    print("ffmpeg error:\n", proc.stderr[-2000:])
    print(f"Frames preserved in: {tmp_dir}")
    sys.exit(1)

shutil.rmtree(tmp_dir)
print(f"Done! Saved: {OUTPUT}")
print("Note: .webm (VP9) supports transparent alpha. Open in Chrome/Firefox or VLC.")
