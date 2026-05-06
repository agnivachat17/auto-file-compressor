# PDF Auto-Compressor 📄→📦
### A beginner-friendly Windows background automation tool

Watches a folder for new PDF files, compresses them with high visual quality,
and saves them to an output folder — automatically, silently, forever.

---

## ✨ What It Does

```
FolderA/                        FolderB/
  ├── report.pdf      ──────►   ├── comp_report.pdf      (compressed ✔)
  ├── invoice.pdf     ──────►   ├── comp_invoice.pdf     (compressed ✔)
  ├── comp_old.pdf    (skip)    └── ...
  └── notes.txt       (skip)
```

- **Monitors Folder A** continuously using OS-level file events (no polling loop)
- **Processes existing PDFs** in Folder A on startup
- **Waits for file transfers** to finish before compressing
- **Compresses** embedded images to JPEG quality 85 (visually excellent)
- **Renames** output as `comp_<originalname>.pdf`
- **Saves** to Folder B, leaving originals untouched
- **Ignores** non-PDFs and files starting with `comp_` silently
- **Logs** everything to `logs/watcher.log`
- **Uses ~0% CPU** while idle (event-driven, not polling)

---

## 📁 Project Structure

```
pdf_watcher/
│
├── watcher.py          ← Main program (monitoring + compression logic)
├── config.py           ← YOUR settings (edit folder paths here)
├── requirements.txt    ← Python package dependencies
│
├── run.bat             ← Launch with a visible terminal window (easy debugging)
├── run_silent.pyw      ← Launch silently in background (no window)
├── stop.bat            ← Stop the background process
├── startup.vbs         ← Drop in Windows Startup folder for autostart on boot
│
├── build_exe.spec      ← Optional: build a standalone .exe with PyInstaller
│
└── logs/
    └── watcher.log     ← All activity and errors are logged here
```

---

## 🚀 Setup (Step-by-Step)

### Step 1 — Install Python

1. Go to **https://www.python.org/downloads/**
2. Click the big yellow "Download Python 3.x.x" button
3. Run the installer
4. ⚠️ **Important:** Check ✅ "Add Python to PATH" at the bottom of the first screen
5. Click "Install Now"

To verify it worked, open Command Prompt (`Win+R` → type `cmd` → Enter) and run:
```
python --version
```
You should see something like `Python 3.12.3`.

---

### Step 2 — Download / Place the Project

Save the entire `pdf_watcher` folder somewhere permanent, for example:
```
C:\Users\YourName\Documents\pdf_watcher\
```

---

### Step 3 — Edit config.py

Open `config.py` in Notepad (right-click → Open With → Notepad).

Change these two lines to your actual folder paths:

```python
FOLDER_A = r"C:\Users\YourName\Documents\FolderA"   # watch this folder
FOLDER_B = r"C:\Users\YourName\Documents\FolderB"   # save compressed files here
```

**Tips:**
- Use `r"..."` (note the `r` before the quote) to avoid issues with backslashes
- Both folders must exist before running (Folder B is auto-created if missing)
- You can use any folder paths, including network drives like `r"\\server\share\pdfs"`

Optionally adjust compression quality (default 85 is excellent):
```python
JPEG_QUALITY = 85    # 75 = smaller files, 92 = near-lossless
```

---

### Step 4 — Install Dependencies

Double-click `run.bat` — it will automatically install all required packages
the first time you run it.

**Or** install manually via Command Prompt:
```
cd C:\Users\YourName\Documents\pdf_watcher
pip install -r requirements.txt
```

This installs:
| Package | Purpose |
|---------|---------|
| `watchdog` | Efficient OS-level folder monitoring |
| `pypdf` | Pure-Python PDF manipulation |
| `Pillow` | Image recompression within PDFs |

---

### Step 5 — Run It!

**Option A — With a terminal window (recommended for first use):**
Double-click `run.bat`

You'll see live output like:
```
2024-01-15 10:30:00  [INFO]  PDF Auto-Compressor starting up
2024-01-15 10:30:00  [INFO]  Watching : C:\Users\You\Documents\FolderA
2024-01-15 10:30:00  [INFO]  Output   : C:\Users\You\Documents\FolderB
2024-01-15 10:30:00  [INFO]  → Detected: quarterly_report.pdf
2024-01-15 10:30:01  [INFO]    ✔ Compressed: 4.2 MB → 1.8 MB (57.1% smaller)
2024-01-15 10:30:01  [INFO]  Watching for new PDFs... (press Ctrl+C to stop)
```

**Option B — Silent background (no window):**
Double-click `run_silent.pyw`

Nothing visible happens — the program runs quietly in the background.
Check `logs/watcher.log` to confirm it's working.

---

## 🔄 Run Automatically on Windows Startup

To start the compressor automatically every time you log into Windows:

1. Press `Win+R`, type `shell:startup`, press Enter
   → A folder opens (this is your Startup folder)

2. Open `startup.vbs` in Notepad and change this line:
   ```vbscript
   SCRIPT_PATH = "C:\Users\YourName\Documents\pdf_watcher\run_silent.pyw"
   ```
   to match where you saved the project.

3. Copy `startup.vbs` into the Startup folder that opened in step 1.

4. **Test it:** Double-click `startup.vbs` — the watcher should start silently.
   Check `logs/watcher.log` to confirm.

5. On next login, it starts automatically. ✅

**To remove autostart:** Delete `startup.vbs` from the Startup folder.

**To stop the background process:** Double-click `stop.bat`

---

## 📦 Optional: Build a Standalone .exe

If you want to share this tool with someone who doesn't have Python installed,
you can build a single self-contained executable.

### Install PyInstaller:
```
pip install pyinstaller
```

### Build:
```
cd C:\Users\YourName\Documents\pdf_watcher
pyinstaller build_exe.spec
```

### Result:
```
dist\PDFAutoCompressor\PDFAutoCompressor.exe
```

Share the entire `dist\PDFAutoCompressor\` folder. The recipient just needs to:
1. Edit `config.py` inside the folder with their paths
2. Double-click `PDFAutoCompressor.exe`

No Python installation required on their machine. ✅

---

## 📋 Logs

All activity is saved to `logs/watcher.log`.

Example log output:
```
2024-01-15 09:00:00  [INFO]  ============================
2024-01-15 09:00:00  [INFO]  PDF Auto-Compressor starting
2024-01-15 09:00:00  [INFO]  Watching : C:\...\FolderA
2024-01-15 09:00:00  [INFO]  → Detected: contract.pdf
2024-01-15 09:00:01  [INFO]    ✔ Compressed: contract.pdf  8.3 MB → 2.1 MB (74.7% smaller)
2024-01-15 09:05:12  [INFO]  → Detected: scan.pdf
2024-01-15 09:05:13  [INFO]    ✔ Compressed: scan.pdf  12.0 MB → 3.4 MB (71.7% smaller)
```

The log file never grows unbounded — rotate it manually or let it grow (it's text, very compact).

---

## 🛠 Troubleshooting

| Problem | Solution |
|---------|----------|
| `python` not found | Re-install Python and check "Add to PATH" |
| `pip install` fails | Run Command Prompt as Administrator |
| File not being detected | Check Folder A path in config.py is correct |
| Output looks wrong | Raise JPEG_QUALITY in config.py to 92 |
| No size reduction | PDF may contain vector art only (no images to compress) — this is fine, the file is still losslessly optimised |
| Process won't stop | Open Task Manager → Details tab → find `pythonw.exe` → End Task |

---

## ⚙️ How the Compression Works

The tool uses a two-stage approach for maximum quality-to-size ratio:

**Stage 1 — Image recompression**
Each page's embedded images are extracted, decoded, re-encoded as JPEG at the configured quality level (default 85/100), and put back. Images are only replaced if the result is actually smaller. Vector graphics, text, and page structure are untouched.

**Stage 2 — Lossless structural optimisation**
Duplicate PDF objects are merged, orphan objects are removed, and streams are compressed. This is always lossless and costs nothing in visual quality.

**What's NOT changed:**
- Text content
- Vector graphics / diagrams
- Page structure and layout
- Fonts
- Metadata (author, title, etc.)
- Original file (always kept)

---

## 📦 Dependencies

| Package | Version | License | Why |
|---------|---------|---------|-----|
| watchdog | 4.0.1 | Apache 2.0 | OS-level folder monitoring |
| pypdf | 4.3.1 | BSD | PDF read/write, object deduplication |
| Pillow | 10.3.0 | HPND | JPEG image recompression |

All are permissively licensed and safe for personal and commercial use.

---

*Built with Python 3.10+ • Tested on Windows 10/11*
