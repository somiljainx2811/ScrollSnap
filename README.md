<<<<<<< HEAD
# 📸 ScrollSnap — Manual Scroll Screenshot Stitcher

Capture long screenshots by scrolling manually. Works on **Linux** and **Windows**.
No root/admin required. Works on ANY app or website — because YOU control the scroll.

---

## ✅ Requirements

- Python 3.10+
- tkinter (usually pre-installed)

### Linux (Ubuntu/Debian)
```bash
sudo apt install python3-tk python3-pip
pip install -r requirements.txt
```

### Windows
```
pip install -r requirements.txt
```
(tkinter ships with the official Python installer for Windows)

---

## 🚀 Run

```bash
python3 scrollsnap.py
```

---

## 🎮 How to Use

1. **Select Region** — Click the button, then drag on your screen to define the capture area
2. **Start Capture** — Switches to capture mode (app stays open but focus goes to your target window)
3. **Scroll & Snap** — Scroll in your target window, then press **SPACE** (or click Snap Frame) after each scroll position
4. **Stitch & Save** — Combines all frames into one long PNG

---

## ⚙ Settings

| Setting      | Description                                      |
|--------------|--------------------------------------------------|
| Direction    | Vertical (↕) or Horizontal (↔) stitching         |
| Overlap      | Pixels to crop from frame edges to avoid seams   |
| Auto-Snap    | Automatically snap a frame every 1 second        |

---

## 💡 Tips

- Keep overlap around **15–30px** for smooth joins
- Use **Auto-Snap** for smooth scrolling at a consistent speed
- You can **delete bad frames** by clicking ✕ on any thumbnail
- Works with any app: browsers, PDF viewers, code editors, terminals, etc.

---

## 📦 Dependencies

| Package | Purpose                         |
|---------|---------------------------------|
| pillow  | Image processing & stitching    |
| mss     | Fast cross-platform screenshots |
| tkinter | GUI (built into Python)         |
=======
# ScrollSnap
>>>>>>> 43bc5bf33a4ce5d4f80211aa3ce0d7af3386b78c
