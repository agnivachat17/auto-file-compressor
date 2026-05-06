"""
PDF Auto-Compressor — watcher.py
=================================
Monitors Folder A for new PDF files, compresses them with high visual quality,
and saves them as comp_<original>.pdf into Folder B.

Tech stack:
  - watchdog   : cross-platform filesystem event monitoring
  - Ghostscript: primary compression engine (much stronger than pure-Python)
  - pypdf      : fallback compression if Ghostscript is not installed
  - Pillow     : used by the pypdf fallback path
  - logging    : built-in structured log output

Compression engine priority:
  1. Ghostscript  — industry-standard, 50-80 % typical reduction, visually lossless
  2. pypdf+Pillow — pure-Python fallback, works without any external install
"""

import sys
import time
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

# winreg is built into Python on Windows — used to locate Ghostscript in the registry
try:
    import winreg
    _WINREG_AVAILABLE = True
except ImportError:
    _WINREG_AVAILABLE = False   # non-Windows environment (graceful degradation)

# ── Third-party ──────────────────────────────────────────────────────────────
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import pypdf
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject
from PIL import Image
import io

# ── Load user config ──────────────────────────────────────────────────────────
import config

# ── Logging setup ─────────────────────────────────────────────────────────────
LOG_FILE = Path(__file__).parent / "logs" / "watcher.log"
LOG_FILE.parent.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),   # log to file
        logging.StreamHandler(sys.stdout),                  # and to terminal
    ],
)
log = logging.getLogger(__name__)


# ── Helper: wait for file write to finish ─────────────────────────────────────
def wait_for_file_ready(path: Path, timeout: int = 30, poll: float = 0.5) -> bool:
    """
    Poll the file until its size stops growing (i.e., copy/write is complete).
    Returns True if file is ready, False if timeout was hit.
    """
    last_size = -1
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            current_size = path.stat().st_size
        except FileNotFoundError:
            return False  # file disappeared mid-copy — skip it
        if current_size == last_size and current_size > 0:
            return True   # size stable → file ready
        last_size = current_size
        time.sleep(poll)
    log.warning(f"Timeout waiting for file to stabilise: {path.name}")
    return False


# ── Ghostscript discovery ─────────────────────────────────────────────────────
def _find_ghostscript() -> str | None:
    """
    Return the full path to the Ghostscript executable (gswin64c.exe or
    gswin32c.exe), or None if Ghostscript is not installed.

    Search order:
      1. Windows registry  (covers standard Ghostscript installer)
      2. Common hard-coded paths  (covers manual / portable installs)
      3. PATH  (covers anything the user added themselves)
    """
    # ── 1. Registry lookup ────────────────────────────────────────────────
    if _WINREG_AVAILABLE:
        for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            for subkey in (
                r"SOFTWARE\Artifex\GPL Ghostscript",
                r"SOFTWARE\WOW6432Node\Artifex\GPL Ghostscript",
            ):
                try:
                    with winreg.OpenKey(root, subkey) as key:
                        # Each version is a sub-key; grab the first (highest) one
                        version, _ = winreg.EnumKey(key, 0), None
                        with winreg.OpenKey(key, version) as vkey:
                            gs_dir, _ = winreg.QueryValueEx(vkey, "GS_DLL")
                            # GS_DLL points to the DLL; exe is in the same bin/ dir
                            gs_dir = Path(gs_dir).parent
                            for exe in ("gswin64c.exe", "gswin32c.exe"):
                                candidate = gs_dir / exe
                                if candidate.exists():
                                    return str(candidate)
                except (OSError, FileNotFoundError, winreg.error):
                    continue

    # ── 2. Hard-coded common locations ────────────────────────────────────
    common_roots = [
        Path(r"C:\Program Files\gs"),
        Path(r"C:\Program Files (x86)\gs"),
    ]
    for root in common_roots:
        if root.exists():
            # Root contains version folders like gs10.03.1 — check all of them
            for version_dir in sorted(root.iterdir(), reverse=True):
                for exe in ("gswin64c.exe", "gswin32c.exe"):
                    candidate = version_dir / "bin" / exe
                    if candidate.exists():
                        return str(candidate)

    # ── 3. PATH fallback ──────────────────────────────────────────────────
    for exe in ("gswin64c.exe", "gswin32c.exe", "gs"):
        found = shutil.which(exe)
        if found:
            return found

    return None   # Ghostscript not found


# Run once at import time so the result is cached for the entire session
_GS_EXE = _find_ghostscript()


# ── Ghostscript compression ───────────────────────────────────────────────────
def _compress_with_ghostscript(src: Path, dst: Path) -> bool:
    """
    Compress a PDF using Ghostscript's ebook/printer distiller pipeline.

    Ghostscript setting used: -dPDFSETTINGS=/ebook
      • Downsamples colour images to 150 dpi  (imperceptible on screen)
      • Downsamples grey images to 150 dpi
      • Keeps monochrome images at 1200 dpi (crisp text/lines)
      • Subsetting and embedding fonts
      • Removes embedded thumbnails, comments, private data

    Why /ebook over /screen or /printer?
      /screen   → 72 dpi  — too blurry for anything but tiny previews
      /ebook    → 150 dpi — excellent quality, major size reduction  ← we use this
      /printer  → 300 dpi — near-original quality, moderate reduction
      /prepress → 300 dpi + colour profiles — largest output

    Returns True on success, False on any Ghostscript error.
    """
    cmd = [
        _GS_EXE,
        "-sDEVICE=pdfwrite",          # output device: write a PDF
        "-dPDFSETTINGS=/ebook",       # quality/compression preset (see above)
        "-dNOPAUSE",                  # don't pause between pages
        "-dBATCH",                    # exit when done (don't wait for input)
        "-dQUIET",                    # suppress informational messages
        "-dSAFER",                    # sandbox: disable %pipe%, delete, rename
        "-dCompatibilityLevel=1.6",   # PDF 1.6 output (Acrobat 7+)
        # — font handling —
        "-dEmbedAllFonts=true",       # embed all fonts so file is self-contained
        "-dSubsetFonts=true",         # only embed the glyphs actually used
        # — colour handling —
        "-dColorImageDownsampleType=/Bicubic",   # high-quality downsampling
        "-dGrayImageDownsampleType=/Bicubic",
        # — suppress pdfmark warnings that appear in some scanned PDFs —
        "-dNOPSICC",
        "-dPrinted=false",
        f"-sOutputFile={dst}",        # output path
        str(src),                     # input path
    ]

    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=300,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        if result.returncode != 0:
            # Log Ghostscript's own error message to help the user diagnose problems
            gs_err = result.stderr.decode("utf-8", errors="replace").strip()
            log.error(f"  Ghostscript error (code {result.returncode}): {gs_err[:400]}")
            return False

        return True

    except subprocess.TimeoutExpired:
        log.error(f"  Ghostscript timed out after 5 minutes: {src.name}")
        return False
    except Exception as e:
        log.error(f"  Ghostscript subprocess error: {e}")
        return False


# ── pypdf + Pillow fallback compression ───────────────────────────────────────
def _compress_with_pypdf(src: Path, dst: Path) -> bool:
    """
    Pure-Python fallback used when Ghostscript is not installed.
    Re-compresses embedded images with JPEG quality from config.JPEG_QUALITY,
    then deduplicates PDF objects losslessly.

    This is the original engine — kept intact as a reliable fallback.
    """
    try:
        reader = PdfReader(str(src))
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        for page_num, page in enumerate(writer.pages, start=1):
            if "/Resources" not in page:
                continue
            resources = page["/Resources"]
            if "/XObject" not in resources:
                continue
            xobjects = resources["/XObject"].get_object()

            for obj_name in list(xobjects.keys()):
                xobj = xobjects[obj_name].get_object()

                if xobj.get("/Subtype") != "/Image":
                    continue

                current_filter = xobj.get("/Filter", "")
                if current_filter in ("/JPXDecode", "/CCITTFaxDecode"):
                    continue

                try:
                    raw_data = xobj.get_data()
                    width  = int(xobj["/Width"])
                    height = int(xobj["/Height"])
                    cs     = xobj.get("/ColorSpace", "/DeviceRGB")

                    if cs == "/DeviceRGB":
                        mode, num_components = "RGB", 3
                    elif cs == "/DeviceGray":
                        mode, num_components = "L", 1
                    elif cs == "/DeviceCMYK":
                        mode, num_components = "CMYK", 4
                    else:
                        continue

                    if len(raw_data) != width * height * num_components:
                        continue

                    img = Image.frombytes(mode, (width, height), raw_data)

                    if mode == "CMYK":
                        img = img.convert("RGB")

                    buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=config.JPEG_QUALITY, optimize=True)
                    compressed_bytes = buf.getvalue()

                    if len(compressed_bytes) < len(raw_data):
                        xobj._data = compressed_bytes
                        xobj[NameObject("/Filter")] = NameObject("/DCTDecode")
                        xobj[NameObject("/Length")] = pypdf.generic.NumberObject(len(compressed_bytes))
                        if "/DecodeParms" in xobj:
                            del xobj["/DecodeParms"]

                except Exception as img_err:
                    log.debug(f"  Skipped image on page {page_num}: {img_err}")
                    continue

        writer.compress_identical_objects(remove_identicals=True, remove_orphans=True)

        with open(dst, "wb") as f:
            writer.write(f)

        return True

    except Exception as e:
        log.error(f"  pypdf fallback error for {src.name}: {e}")
        if dst.exists():
            dst.unlink()
        return False


# ── Core compression logic (engine dispatcher) ────────────────────────────────
def compress_pdf(src: Path, dst: Path) -> bool:
    """
    Compress src → dst.

    Tries Ghostscript first (much stronger compression).
    Falls back to pypdf+Pillow if Ghostscript is not installed.
    Reports file size reduction regardless of which engine was used.

    Returns True on success, False on any error.
    """
    src_kb = src.stat().st_size / 1024

    if _GS_EXE:
        # ── Primary: Ghostscript ──────────────────────────────────────────
        log.debug(f"  Engine: Ghostscript ({_GS_EXE})")
        success = _compress_with_ghostscript(src, dst)

        if not success:
            # Ghostscript failed mid-way — clean up and try fallback
            if dst.exists():
                dst.unlink()
            log.warning(f"  Ghostscript failed, trying pypdf fallback...")
            success = _compress_with_pypdf(src, dst)
            engine_label = "pypdf fallback"
        else:
            engine_label = "Ghostscript"
    else:
        # ── Fallback: pypdf + Pillow ──────────────────────────────────────
        log.debug("  Engine: pypdf+Pillow (Ghostscript not found)")
        success = _compress_with_pypdf(src, dst)
        engine_label = "pypdf"

    if not success:
        if dst.exists():
            dst.unlink()
        log.error(f"  ✘ Compression failed for {src.name}")
        return False

    # ── Report results ────────────────────────────────────────────────────
    dst_kb  = dst.stat().st_size / 1024
    saving  = (1 - dst_kb / src_kb) * 100 if src_kb > 0 else 0
    log.info(
        f"  ✔ Compressed [{engine_label}]: {src.name}  "
        f"{src_kb:.1f} KB → {dst_kb:.1f} KB  "
        f"({saving:.1f}% smaller)"
    )
    return True


# ── Process a single PDF file ─────────────────────────────────────────────────
def process_pdf(src_path: Path, folder_b: Path) -> None:
    """
    Full pipeline for one PDF:
      1. Validate (is PDF? already compressed? exists?)
      2. Wait for file to be fully written
      3. Compress
      4. Save as comp_<name>.pdf in Folder B
    """
    name = src_path.name

    # Skip non-PDFs (belt-and-suspenders guard, event handler already filters)
    if src_path.suffix.lower() != ".pdf":
        return

    # Skip already-compressed files
    if name.lower().startswith("comp_"):
        log.debug(f"  Skipping already-compressed file: {name}")
        return

    log.info(f"→ Detected: {name}")

    # Wait for the file to finish being written/copied
    if not wait_for_file_ready(src_path):
        log.error(f"  File never became stable, skipping: {name}")
        return

    # Destination path
    dst_name = f"comp_{name}"
    dst_path = folder_b / dst_name

    # Don't re-compress if output already exists (e.g. watcher restarted)
    if dst_path.exists():
        log.info(f"  Output already exists, skipping: {dst_name}")
        return

    compress_pdf(src_path, dst_path)


# ── Watchdog event handler ────────────────────────────────────────────────────
class PDFHandler(FileSystemEventHandler):
    """
    Receives filesystem events from watchdog.
    Only reacts to file creation/move events for PDF files in Folder A.
    """
    def __init__(self, folder_b: Path):
        super().__init__()
        self.folder_b = folder_b

    def _handle(self, event_path: str) -> None:
        path = Path(event_path)
        if path.suffix.lower() == ".pdf" and not path.name.lower().startswith("comp_"):
            process_pdf(path, self.folder_b)

    def on_created(self, event):
        """Fired when a new file appears (including drag-and-drop, download, copy)."""
        if not event.is_directory:
            self._handle(event.src_path)

    def on_moved(self, event):
        """Fired when a file is moved/renamed into the watched folder."""
        if not event.is_directory:
            self._handle(event.dest_path)


# ── Startup scan (process files already in Folder A) ─────────────────────────
def scan_existing(folder_a: Path, folder_b: Path) -> None:
    """
    On startup, process any PDFs already sitting in Folder A
    that haven't been compressed yet.
    """
    log.info("Scanning Folder A for existing PDFs...")
    pdfs = sorted(folder_a.glob("*.pdf"))
    if not pdfs:
        log.info("  No existing PDFs found.")
        return
    for pdf in pdfs:
        if not pdf.name.lower().startswith("comp_"):
            process_pdf(pdf, folder_b)


# ── Main entry point ──────────────────────────────────────────────────────────
def main():
    log.info("=" * 60)
    log.info("PDF Auto-Compressor starting up")
    log.info("=" * 60)

    # ── Resolve and validate folders ──────────────────────────────────────
    folder_a = Path(config.FOLDER_A).expanduser().resolve()
    folder_b = Path(config.FOLDER_B).expanduser().resolve()

    if not folder_a.exists():
        log.error(f"Folder A does not exist: {folder_a}")
        log.error("Please edit config.py and set the correct path.")
        sys.exit(1)

    folder_b.mkdir(parents=True, exist_ok=True)  # auto-create Folder B if needed

    log.info(f"Watching : {folder_a}")
    log.info(f"Output   : {folder_b}")
    log.info(f"Quality  : JPEG {config.JPEG_QUALITY}/100")
    log.info("-" * 60)

    # ── Process files already present ─────────────────────────────────────
    scan_existing(folder_a, folder_b)

    # ── Set up watchdog observer ───────────────────────────────────────────
    handler  = PDFHandler(folder_b)
    observer = Observer()
    # recursive=False → only watch the top level of Folder A (not sub-folders)
    observer.schedule(handler, str(folder_a), recursive=False)
    observer.start()

    log.info("Watching for new PDFs... (press Ctrl+C to stop)")

    try:
        while True:
            time.sleep(1)   # very low CPU usage — just sleeping between polls
    except KeyboardInterrupt:
        log.info("Shutdown requested.")
    finally:
        observer.stop()
        observer.join()
        log.info("PDF Auto-Compressor stopped.")


if __name__ == "__main__":
    main()