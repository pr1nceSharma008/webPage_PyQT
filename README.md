# Digital-Sync Machine Monitoring — PyQt6 Port

## Setup
```bash
pip install -r requirements.txt
```

## Run
```bash
python main.py
```

Make sure your .NET backend is running at `http://localhost:5147`
(edit `BASE` in `api_worker.py` if it's hosted elsewhere).

## File map (mirrors your original HTML structure)
| File | Role | Equivalent in your index.html |
|---|---|---|
| `theme.py` | Colors + QSS generators | tailwind.config + `<style>` block |
| `utils.py` | OEE math, time format, shift visibility | `fmt()`, `totalOEE()`, `shiftOEE()`, `getShiftVisibility()` |
| `api_worker.py` | Background thread polling your API | `fetchStatus()`, `fetchIP()`, `setInterval` |
| `machine_card.py` | One machine's card widget | `cardHTML()` + `patchCard()` |
| `loading_screen.py` | 30s countdown overlay | `#loadingOverlay` + `startLoadingCountdown()` |
| `main_window.py` | Navbar + 1-or-2-machine container | `<nav>` + `renderMachines()` |
| `main.py` | Wires it all together | your closing `<script>` init block |

## Not yet ported (tell me if you want these next)
- QR code scanner input capture (`setupQR()`)
- Toast notifications (`toast()`)
- Logo image (I used a text placeholder "Höganäs" — drop your `hogonas_logo.jpg` in and I'll wire it up with `QPixmap`)

## Adaptation notes vs. the HTML version
- Fonts: "Segoe UI"/"Consolas" as stand-ins — tell me your brand fonts and I'll swap them in `theme.py`
- The countdown ring is hand-drawn with `QPainter` (no SVG needed in PyQt)
- Glows use `QGraphicsDropShadowEffect` since QSS has no `box-shadow` property
- Tested end-to-end with a mock API server (loading screen, single-machine, two-machine layouts, and running/stopped states all verified visually — see screenshots in chat)
