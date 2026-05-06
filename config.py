"""
config.py — User Configuration
================================
Edit FOLDER_A and FOLDER_B below to match your system.
Everything else is optional.
"""

# ── REQUIRED: Set your folder paths here ──────────────────────────────────────
#
#   Use raw strings (r"...") or forward slashes to avoid escape issues.
#   Examples:
#       r"C:\Users\YourName\Documents\Inbox"
#       "C:/Users/YourName/Downloads/PDFs"

FOLDER_A = r"E:\INPUT"
FOLDER_B = r"E:\OUTPUT"


# ── OPTIONAL: Compression quality ─────────────────────────────────────────────
#
#   JPEG quality for re-compressing embedded images.
#   Range: 1 (worst) – 95 (best). Default: 85
#   85 gives excellent visual quality with meaningful size reduction.
#   Raise to 92 for near-lossless. Lower to 75 for more aggressive compression.

JPEG_QUALITY = 85
