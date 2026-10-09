' 书与笔 (MC Notepad) · 免控制台启动器
' 双击本文件即可运行，不会闪出黑色命令行窗口。
' 优先启动 dist\MC Notepad\MC Notepad.exe；exe 不在了才退回系统 Python 跑源码。
Option Explicit
Dim fso, sh, base, exe, pyw, script
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")
base    = fso.GetParentFolderName(WScript.ScriptFullName)
exe     = base & "\dist\MC Notepad\MC Notepad.exe"
script  = base & "\MC Notepad.py"
' 用环境变量拼，不写死 C:\Users\<谁>\... —— 这份是要开源上传的
pyw     = sh.ExpandEnvironmentStrings("%LOCALAPPDATA%\Programs\Python\Python310\pythonw.exe")

If fso.FileExists(exe) Then
    sh.CurrentDirectory = base & "\dist\MC Notepad"
    sh.Run """" & exe & """", 0, False
    WScript.Quit 0
End If

If Not fso.FileExists(pyw) Then
    MsgBox "找不到 MC Notepad.exe，也找不到 Python：" & vbCrLf & pyw & vbCrLf & vbCrLf & _
           "请重新生成 exe，或确认系统 Python 3.10 已安装。", 16, "MC Notepad"
    WScript.Quit 1
End If

sh.CurrentDirectory = base
sh.Run """" & pyw & """ """ & script & """", 0, False
