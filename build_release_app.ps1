# build_release_app.ps1 — PowerShell puro (release con app.py)

# 0) Ir a la carpeta del script
Set-Location -Path $PSScriptRoot

# 1) Limpieza de artefactos de build (NO borramos .venv)
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
Remove-Item -Force CavebotGUI.spec -ErrorAction SilentlyContinue

# 2) Crear venv solo si no existe y activarlo
if (-not (Test-Path ".\.venv")) {
    python -m venv .venv
}

# Permitir scripts para esta sesión y activar venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
. .\.venv\Scripts\Activate.ps1

# 3) Pip al día
python -m pip install -U pip

# 4) Instalar dependencias (incluye Firebase y sus libs)
pip install -U `
  pyinstaller PySide6 opencv-python pillow mss keyboard `
  pyautogui pydirectinput pygetwindow mouseinfo pyscreeze pyrect pytweening `
  pywin32 `
  pyrebase4 sseclient-py requests requests_toolbelt python_jwt `
  oauth2client googleapis-common-protos

# (por si acaso, aseguramos que NO haya PyQt5 en este venv)
pip uninstall -y PyQt5 PyQt5-Qt5 PyQt5-sip qtpy | Out-Null

# 5) Verificación rápida de pyrebase en este venv (debe imprimir ruta OK)
python -c "import pyrebase, sys; print('pyrebase OK ->', pyrebase.__file__); print('PY ->', sys.executable)"

# 6) Ruta a plugins de Qt DENTRO del venv
$PYSIDE_PLUGINS = Join-Path $PWD ".venv\Lib\site-packages\PySide6\plugins"

# 7) Build (SOLO GUI, sin consola) usando PyInstaller del venv
.\.venv\Scripts\python.exe -m PyInstaller `
  --noconfirm --clean `
  --name CavebotGUI `
  --windowed `
  --exclude-module PyQt5 `
  --exclude-module PyQt5.QtCore `
  --exclude-module PyQt5.QtGui `
  --exclude-module PyQt5.QtWidgets `
  --exclude-module qtpy `
  --hidden-import cv2 `
  --hidden-import PIL `
  --hidden-import mss `
  --hidden-import keyboard `
  --hidden-import pyautogui `
  --hidden-import pydirectinput `
  --hidden-import pygetwindow `
  --hidden-import mouseinfo `
  --hidden-import pyscreeze `
  --hidden-import pyrect `
  --hidden-import pytweening `
  --hidden-import win32gui `
  --hidden-import win32con `
  --hidden-import win32api `
  --hidden-import pyrebase `
  --hidden-import sseclient `
  --hidden-import oauth2client `
  --hidden-import googleapis.common_protos `
  --collect-all pyrebase `
  --add-data "config;config" `
  --add-data "core;core" `
  --add-data "creatures;creatures" `
  --add-data "functions;functions" `
  --add-data "gui;gui" `
  --add-data "img;img" `
  --add-data "marcas;marcas" `
  --add-data "profiles;profiles" `
  --add-data "styles.qss;." `
  --add-data "runtime_cfg.py;." `
  --add-data "transparency.py;." `
  --add-data "antiparalyze.py;." `
  --add-data "firebase.json;." `
  --add-data "$PYSIDE_PLUGINS\platforms;PySide6/plugins/platforms" `
  --add-data "$PYSIDE_PLUGINS\imageformats;PySide6/plugins/imageformats" `
  app.py

Write-Host "`nListo: dist\CavebotGUI\CavebotGUI.exe (solo GUI)" -ForegroundColor Green
