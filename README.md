# VirtualMouse — Hand-Gesture Mouse Control (OpenCV + MediaPipe)

Control your Windows mouse with just your webcam and your hand. Move the cursor,
click, double-click, drag & drop, scroll, change volume, minimize windows,
toggle media, and switch virtual desktops — all through hand gestures.

Built on the original `VirtualMouse_openCV` starter (move + click) and extended
with a full gesture set, tap-timing engine, sticky preview window, and Windows
key/mouse automation via `ctypes`.

## Features

- 🖱️ Cursor control with smoothing + right / left / double click
- ✊ Drag & drop, scroll, volume, minimize-all, media toggle, desktop switch
- 🖼️ Sticky always-on-top camera preview that never steals focus
- ⌨️ Windows automation with `ctypes` (no extra drivers needed)

## Requirements

- **Python 3.11.0** must be installed to run this project
- Windows OS (mouse/keyboard automation uses `ctypes.windll.user32`)
- Webcam

Install dependencies from `requirements.txt`:

```txt
# Requires Python 3.11.0
mediapipe==0.10.21
opencv-python==4.11.0.86
numpy<2
autopy==4.0.2
```

```bash
py -3.11 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```bash
python virtualmouse.py
```

- Keep your hand inside the purple rectangle (the active region, `frameR = 100`).
- Camera is `640×480`, mapped to your full screen with `5×` smoothing.
- The preview snaps to a small `320×240` window in the top-right corner. It stays
  on top without stealing focus and restores itself if minimized — only `q`
  (with the preview focused) quits the app.

## Gestures & Commands

Finger notation below is `[thumb, index, middle, ring, pinky]` (`1` = up).
Thresholds live in `virtualmouse.py` → `Mouse(img)`.

| # | Gesture (fingers) | How to do it | Command |
|---|---|---|---|
| 1 | Move — `[?, 1, 0, 0, 0]` index only | Move your index finger inside the rectangle | Cursor follows index tip (green dot), smoothed |
| 2 | Right click — same + pinch `4-8 < 35px` | While moving, touch thumb tip to index tip | Right click (1s cooldown) |
| 3 | Left click — `[?, 1, 1, 0, 0]` | Pinch index tip `8` to middle tip `12` (`< 40px`) and release | Single left click (fires ~0.3s after tap if no 2nd tap) |
| 4 | Double click — same | Two pinches within `0.28s`, 2nd released quickly (`< 0.25s`) | Double left click |
| 5 | Scroll — same, spread `> 70px` | Keep index+middle open and slide middle finger vertically (`> 8px`) | Mouse wheel up/down (`0.08s` rate) |
| 6 | Drag & drop — `[?, 1, 1, 0, 1]` + pinch `4-16` | Show index+middle+pinky, bend thumb+ring together (`< 60px`) to grab, move hand, spread (`> 70px`) to drop | Left-button hold + move (green dot on index) |
| 7 | Volume — `[?, 1, 1, 1, 0]` | Show index+middle+ring, slide index vertically (`> 12px`) | Volume up (`VK 0xAF`) / down (`VK 0xAE`), `0.25s` rate (blue dot) |
| 8 | Minimize all — open hold then fist | Hold open palm steady `~0.5s` (`< 40px` drift), then close into a fist | `Win+M`; preview pops itself back (`1.5s` cooldown) |
| 9 | Media play/pause — 10 fingers, 2 hands | Show all 10 fingers to the camera | Play/pause (`VK 0xB3`), `1s` cooldown |
| 10 | Switch desktop — single fist + swipe | Make a fist (2nd hand closed/absent), swipe horizontally (`> 40px`) | `Win+Ctrl+Left/Right` (`1s` cooldown) |

Notes:

- Tap engine: 2nd-tap window `0.28s`, single-click delay `0.3s`, double-release
  window `0.25s`. Pinch `< 40px`, release/spread `> 55–70px` (hysteresis).
- Drag (`#6`) is suppressed while a minimize hold is armed, so open→fist never
  fires a stray grab.
- Fist ignores the thumb (it folds unpredictably) — `sum(fingers[1:]) == 0`.

## Project Structure

```text
GCM/
├── virtualmouse.py       # App: gestures, Windows automation, preview window
├── HandTrackingModule.py # MediaPipe hand tracking: findhands, findPosition,
│                         # fingersUp, findDistance (21 landmarks)
├── requirements.txt      # Pinned deps (needs Python 3.11.0)
└── README.md             # This file
```

## How It Works

1. `cv2.VideoCapture(0)` grabs `640×480` frames, flipped for mirror view.
2. `HandTrackingModule.HandDetector` (MediaPipe Hands, max 2 hands) extracts
   21 landmarks per hand; `fingersUp()` compares tip vs joint positions.
3. `Mouse(img)` maps the active rectangle to screen coords
   (`numpy.interp`), smooths, and drives `autopy.mouse`; clicks, wheel,
   volume/media/desktop/minimize go through `ctypes` (`mouse_event`,
   `keybd_event`, `SetWindowPos`, `ShowWindow`).
4. Preview window `"result"` is set `TOPMOST + TOOLWINDOW + NOACTIVATE`
   (visible, off taskbar/Alt-Tab, never grabs focus) and re-asserted every
   frame; `_minimize()` re-restores it after `Win+M`.

## Tuning

All knobs are constants at the top of `virtualmouse.py` and inline thresholds:

- `frameR = 100` — active-region margin (smaller = larger move area, edgier)
- `smootheing = 5` — higher = steadier but laggier cursor
- Pinch/scroll/swipe pixel thresholds (`35 / 40 / 50 / 60 / 70`, `> 8/12/30/40px`)
- Cooldowns (`1s` right, `1.5s` minimize, `1s` media/desktop, `0.25s` volume,
  `0.08s` scroll) and tap windows (`0.28 / 0.3 / 0.25s`)

## Troubleshooting

| Symptom | Fix |
|---|---|
| Hand not detected | Good lighting, plain background, hand fully inside purple rectangle |
| Cursor jumpy | Raise `smootheing`, hold hand steadier, keep camera still |
| Drag won't grab | Show index+middle+pinky clearly, touch thumb↔ring firmly (`< 60px`), keep ring bent |
| Minimize won't fire | Hold open palm *still* 0.5s first (watch drift), then close decisively to a fist |
| Double click fires two singles | Pinch twice faster (within `0.28s`) |
| Preview gone / minimized | It auto-restores; if killed, rerun `python virtualmouse.py` |
| `q` doesn't quit | Click the preview once to focus it, then press `q` |

## Limitations

- Windows-only (`ctypes.windll` for wheel, media keys, `Win+M`, always-on-top).
- Needs a clear webcam view; gloves, occlusion, or darkness degrade tracking.
- Finger classification is heuristic (bent pinching fingers read as "down") —
  gestures are designed around that, but extreme angles can misfire.

## Credits

- Original starter: `mohammadst99/VirtualMouse_openCV` (move + click + demo GIF)
- Hand tracking: Google MediaPipe Hands via `HandTrackingModule.py`
