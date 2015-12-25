@ECHO OFF
pyinstaller.exe --upx-dir=upx updater.spec
REM C:\Python\3.4\Scripts\pyinstaller.exe -F -w -i resource\favicon.ico updater.py
PAUSE