# app.py
import sys
from pathlib import Path

# --- Directorio base del proyecto ---
BASE_DIR = Path(__file__).parent.resolve()

# Asegura que el proyecto esté en sys.path
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Comprobaciones rápidas de estructura
GUI_DIR  = BASE_DIR / "gui"
CORE_DIR = BASE_DIR / "core"
CFG_FILE = CORE_DIR / "config_manager.py"   # <- AHORA en core/

missing = []
if not GUI_DIR.exists():    missing.append(str(GUI_DIR))
if not CORE_DIR.exists():   missing.append(str(CORE_DIR))
if missing:
    print("[E] Faltan carpetas requeridas:", ", ".join(missing))
if not CFG_FILE.exists():
    print(f"[E] Falta el archivo requerido: {CFG_FILE}")

# ----- Imports (con el path ya ajustado) -----
from PySide6.QtWidgets import QApplication

# IMPORTS CORRECTOS: desde 'core'
try:
    from core.config_manager import ConfigManager
except ModuleNotFoundError:
    print("[E] No se pudo importar core.config_manager. "
          "Asegúrate de tener la carpeta 'core' con 'config_manager.py'.")
    raise

try:
    from core.controller import Controller
except ModuleNotFoundError:
    print("[E] No se pudo importar core.controller. "
          "Asegúrate de tener la carpeta 'core' con 'controller.py'.")
    raise

try:
    from gui.main_window import MainWindow
except ModuleNotFoundError:
    print("[E] No se pudo importar gui.main_window. "
          "Asegúrate de tener la carpeta 'gui' con 'main_window.py'.")
    raise


def main():
    # --- Asegurar carpetas base del proyecto ---
    (BASE_DIR / "profiles").mkdir(parents=True, exist_ok=True)
    (BASE_DIR / "img").mkdir(parents=True, exist_ok=True)
    (BASE_DIR / "marcas").mkdir(parents=True, exist_ok=True)
    (BASE_DIR / "config").mkdir(parents=True, exist_ok=True)  # opcional para otros ajustes

    # --- Gestor de configuración ---
    cfg_mgr = ConfigManager(BASE_DIR)

    # --- Qt App ---
    app = QApplication(sys.argv)

    # --- Cargar tema QSS si existe ---
    qss_path = BASE_DIR / "styles.qss"
    if qss_path.exists():
        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())
            print(f"[QSS] Cargado: {qss_path}")
        except Exception as e:
            print(f"[QSS] No se pudo cargar styles.qss: {e}")
    else:
        print("[QSS] styles.qss no encontrado (continuo sin tema).")

    # --- Controller + inyección de ConfigManager ---
    # Compatibilidad: si tu Controller tiene firma distinta, caemos con fallback.
    try:
        controller = Controller(config_manager=cfg_mgr)
    except TypeError:
        controller = Controller()
        setattr(controller, "config_manager", cfg_mgr)

    # Base dir para el controller (si no lo expone en el ctor)
    if not hasattr(controller, "base_dir"):
        controller.base_dir = BASE_DIR

    # --- Ventana principal ---
    win = MainWindow(controller)
    # Tamaño compacto (aprox. mitad de 1366x768)
    win.resize(810, 630)
    win.setMinimumSize(640, 380)
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
