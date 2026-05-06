' startup.vbs — Add this to Windows Startup folder for autostart
' This launches run_silent.pyw with NO terminal window using pythonw.exe.
'
' HOW TO USE:
'   1. Press Win+R, type:  shell:startup  → press Enter
'   2. Copy THIS file (startup.vbs) into that Startup folder
'   3. Edit the SCRIPT_PATH line below to match where you saved the project
'   4. Reboot (or double-click the .vbs file to test it now)
'
' To stop autostart: delete this .vbs file from the Startup folder.

' ── EDIT THIS PATH ────────────────────────────────────────────────────────────
Dim SCRIPT_PATH
SCRIPT_PATH = "E:\SmartCompress\run_silent.pyw"
' ─────────────────────────────────────────────────────────────────────────────

Dim WShell
Set WShell = CreateObject("WScript.Shell")

' Run pythonw (windowless) with the script path, in the script's own directory
WShell.Run "pythonw """ & SCRIPT_PATH & """", 0, False
' The  0  = no window, False = don't wait for it to finish

Set WShell = Nothing
