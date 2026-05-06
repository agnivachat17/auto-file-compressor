"""
run_silent.pyw — Silent background launcher
=============================================
Run this file with pythonw.exe (it has a .pyw extension, so Windows
does this automatically) to start the watcher with NO visible window.
The process runs silently in the background.

All output still goes to:  logs/watcher.log

To stop:  open Task Manager → find pythonw.exe → End Task.
          Or use the stop.bat helper script.
"""

# Simply import and run the main watcher — no window is created because
# .pyw files are executed by pythonw.exe (the windowless Python interpreter).
import watcher
watcher.main()
