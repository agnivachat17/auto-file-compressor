# build_exe.spec — PyInstaller configuration
# Build a standalone .exe with:
#   pip install pyinstaller
#   pyinstaller build_exe.spec
#
# Output: dist\PDFAutoCompressor\PDFAutoCompressor.exe
# The entire dist\PDFAutoCompressor\ folder is self-contained —
# share it with anyone, no Python installation needed.

block_cipher = None

a = Analysis(
    ['watcher.py'],                   # main entry point
    pathex=['.'],
    binaries=[],
    datas=[
        ('config.py', '.'),           # bundle config alongside the exe
    ],
    hiddenimports=[
        'watchdog.observers.read_directory_changes',  # Windows-specific observer
        'PIL._imaging',
        'PIL.JpegImagePlugin',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'matplotlib', 'numpy', 'scipy',   # not needed, keeps exe small
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PDFAutoCompressor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                         # compress the exe with UPX if available
    console=True,                     # True = shows a terminal window (easy debugging)
    # Set console=False for a fully silent exe (use startup.vbs to launch)
    icon=None,                        # add an .ico file path here if you have one
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PDFAutoCompressor',
)
