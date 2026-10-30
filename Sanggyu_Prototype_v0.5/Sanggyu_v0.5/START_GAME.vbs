Option Explicit
Dim sh, fs, folder, q, cmd
Set sh = CreateObject("WScript.Shell")
Set fs = CreateObject("Scripting.FileSystemObject")
folder = fs.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = folder
q = Chr(34)
cmd = "cmd /c " & q & "where pyw >nul 2>nul && (start " & q & q & " pyw -3 main.pyw) || (start " & q & q & " pythonw main.pyw)" & q
sh.Run cmd, 0, False
