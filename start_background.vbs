' ===========================================================================
'  Start the camera streamer silently (no console window).
'  Double-click this file, or let Windows run it at startup.
' ===========================================================================
Option Explicit

Dim fso, sh, dir, pyw, cmd
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")

' Folder this script lives in (works no matter where it is launched from)
dir = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = dir

' Prefer the real interpreter path so a broken PATH cannot stop the stream
pyw = "C:\Users\user\AppData\Local\Programs\Python\Python314\pythonw.exe"
If Not fso.FileExists(pyw) Then pyw = "pythonw.exe"

cmd = """" & pyw & """ """ & dir & "\streamer.py"""

' 0 = hidden window, False = do not wait
sh.Run cmd, 0, False
