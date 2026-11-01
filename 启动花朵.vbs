Option Explicit

Dim fso, shell, appDir
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

appDir = fso.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = appDir

If CommandExists("pyw.exe") Then
  shell.Run "pyw.exe -3 serve.py", 0, False
ElseIf CommandExists("pythonw.exe") Then
  shell.Run "pythonw.exe serve.py", 0, False
ElseIf CommandExists("py.exe") Then
  shell.Run "py.exe -3 serve.py", 0, False
ElseIf CommandExists("python.exe") Then
  shell.Run "python.exe serve.py", 0, False
Else
  MsgBox "未找到 Python 3。请把 Python 安装到 D: 或 E:，并勾选 Add Python to PATH。", 16, "指尖花"
End If

Function CommandExists(commandName)
  Dim process
  Set process = shell.Exec("cmd.exe /c where " & commandName)
  Do While process.Status = 0
    WScript.Sleep 25
  Loop
  CommandExists = (process.ExitCode = 0)
End Function
