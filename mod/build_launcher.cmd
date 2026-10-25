@echo off
rem 重新编译启动器（改了 src\Launcher.cs 之后运行）
setlocal
set CSC=%WINDIR%\Microsoft.NET\Framework64\v4.0.30319\csc.exe
if not exist "%CSC%" set CSC=%WINDIR%\Microsoft.NET\Framework\v4.0.30319\csc.exe
"%CSC%" /nologo /target:winexe /platform:x86 /optimize+ /codepage:65001 /out:"%~dp0WitE2CN.exe" /r:System.dll /r:System.Core.dll /r:System.Windows.Forms.dll /r:System.Drawing.dll /r:System.Web.Extensions.dll "%~dp0src\Launcher.cs"
if errorlevel 1 (echo BUILD FAILED) else (echo BUILD OK)
pause
