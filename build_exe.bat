@echo off
setlocal
cd /d "%~dp0"

REM Activa tu venv existente
call .venv\Scripts\activate

REM Limpia artefactos previos
rd /s /q build 2>nul
rd /s /q dist 2>nul
del /f /q CavebotGUI.spec 2>nul

REM Ruta a plugins de Qt (ajusta si tienes otra versión de Python)
set PYSIDE_PLUGINS=%USERPROFILE%\AppData\Local\Programs\Python\Python310\Lib\site-packages\PySide6\plugins

REM Build final: SOLO GUI (sin consola)
pyinstaller ^
  --noconfirm --clean ^
  --name CavebotGUI ^
  --windowed ^
  --hidden-import cv2 ^
  --hidden-import PIL ^
  --hidden-import mss ^
  --hidden-import keyboard ^
  --hidden-import pyautogui ^
  --hidden-import pydirectinput ^
  --hidden-import pygetwindow ^
  --hidden-import mouseinfo ^
  --hidden-import pyscreeze ^
  --hidden-import pyrect ^
  --hidden-import pytweening ^
  --hidden-import win32gui ^
  --hidden-import win32con ^
  --hidden-import win32api ^
  --add-data "config;config" ^
  --add-data "core;core" ^
  --add-data "creatures;creatures" ^
  --add-data "functions;functions" ^
  --add-data "gui;gui" ^
  --add-data "img;img" ^
  --add-data "marcas;marcas" ^
  --add-data "profiles;profiles" ^
  --add-data "styles.qss;." ^
  --add-data "runtime_cfg.py;." ^
  --add-data "transparency.py;." ^
  --add-data "antiparalyze.py;." ^
  --add-data "firebase.json;." ^
  --add-data "%PYSIDE_PLUGINS%\platforms;PySide6/plugins/platforms" ^
  --add-data "%PYSIDE_PLUGINS%\imageformats;PySide6/plugins/imageformats" ^
  app.py

echo.
echo Listo: dist\CavebotGUI\CavebotGUI.exe (solo GUI)
pause
