# app.py
import sys
from pathlib import Path
import platform
import threading
import time as _t
import sys as _sys

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox
from functions.auth_utils import parse_pyrebase_error, log_auth_error
from core.licensing import set_active_session, mark_heartbeat_thread_started


# --- Directorio base del proyecto ---
BASE_DIR = Path(__file__).parent.resolve()

# Asegura que el proyecto esté en sys.path
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Comprobaciones rápidas de estructura
GUI_DIR  = BASE_DIR / "gui"
CORE_DIR = BASE_DIR / "core"
CFG_FILE = CORE_DIR / "config_manager.py"

missing = []
if not GUI_DIR.exists():    missing.append(str(GUI_DIR))
if not CORE_DIR.exists():   missing.append(str(CORE_DIR))
if missing:
    print("[E] Faltan carpetas requeridas:", ", ".join(missing))
if not CFG_FILE.exists():
    print(f"[E] Falta el archivo requerido: {CFG_FILE}")

# --- Imports del proyecto ---
try:
    from core.config_manager import ConfigManager
    from core.controller import Controller
    from gui.main_window import MainWindow
except ModuleNotFoundError as e:
    print("[E] Import fallido:", e)
    raise


def main():
    # --- Asegurar carpetas base del proyecto ---
    (BASE_DIR / "profiles").mkdir(parents=True, exist_ok=True)
    (BASE_DIR / "img").mkdir(parents=True, exist_ok=True)
    (BASE_DIR / "marcas").mkdir(parents=True, exist_ok=True)
    (BASE_DIR / "config").mkdir(parents=True, exist_ok=True)

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

    # ================= LOGIN + LICENCIA =================
    try:
        from gui.login_dialog import LoginDialog
        from core.licensing import (
            sign_in, refresh_id_token, check_license_details,
            compute_device_id, acquire_session, heartbeat, release_session
        )
    except Exception as e:
        QMessageBox.critical(None, "Inicio", f"Faltan módulos de licencias: {e}")
        return

    # Preferencias (recordar email)
    settings = QSettings("Cavebot", "CavebotGUI")
    saved_email    = settings.value("login/email", "", str)
    saved_remember = settings.value("login/remember", False, bool)

    dlg = LoginDialog(saved_email=saved_email, saved_remember=saved_remember)
    while True:
        if dlg.exec() != QDialog.Accepted:
            print("[App] Login cancelado.")
            return

        email, password, remember = dlg.get_credentials()

        try:
            uid, id_token, state = sign_in(email, password)
            print(f"[Lic] Login OK UID={uid}")

            ok, details, msg = check_license_details(state["db"], uid, id_token)
            if not ok:
                dlg.set_error(msg)
                continue

            # Guarda preferencias
            if remember:
                settings.setValue("login/email", email)
                settings.setValue("login/remember", True)
            else:
                settings.remove("login/email")
                settings.setValue("login/remember", False)

            # Info de licencia
            plan = details.get("plan", "—")
            days = details.get("days_remaining", 0)
            QMessageBox.information(None, "Licencia validada",
                                    f"Plan: {plan}\nDías restantes: {days}")
            print(f"[Lic] {msg}")
            break

        except Exception as e:
            user_msg, tech = parse_pyrebase_error(e)
            # Guardamos detalle técnico en un log (junto al .exe)
            log_auth_error(tech, Path("auth_error.log"))
            # Mostramos solo un mensaje limpio al usuario
            dlg.set_error(user_msg)
            continue
    # ================= FIN LOGIN + LICENCIA =================

    # -------- Single-login: adquirir sesión exclusiva --------
    device_id = compute_device_id()
    device_name = platform.node()

    # refresca antes de escribir en /sessions
    id_token = refresh_id_token(state)

    ok_session, token_or_msg = acquire_session(
        state["db"], uid, id_token, device_id, device_name,
        timeout_s=120, strict_single=True
    )

    if not ok_session:
        QMessageBox.critical(None, "Cuenta en uso", token_or_msg)
        return

    # ya tenemos sesión: guarda el token y comparte el contexto con licensing
    session_token = token_or_msg
    refresh_token = state.get("refreshToken", "")

    set_active_session(
        uid=uid,
        id_token=id_token,
        refresh_token=refresh_token,
        db=state["db"],
        session_token=session_token,
        device_id=device_id,
        device_name=device_name,
    )
    if not ok_session:
        QMessageBox.critical(None, "Cuenta en uso", token_or_msg)
        return
    session_token = token_or_msg

    # Heartbeat + refresh + recheck en background
    def _license_watcher():
        nonlocal id_token
        last_refresh = 0.0
        beat = 0
        while True:
            _t.sleep(30)  # intervalo de pulso
            try:
                beat += 1
                # Cada 3° pulso, validamos con lectura (seguro).
                do_full_check = (beat % 3 == 0)

                if do_full_check:
                    # heartbeat "completo" (lee y valida token)
                    hb_ok = heartbeat(state["db"], uid, id_token, session_token, timeout_s=5)
                    if not hb_ok:
                        QMessageBox.critical(None, "Sesión cerrada",
                                            "Otra instancia tomó la cuenta o tu sesión expiró.")
                        try:
                            release_session(state["db"], uid, id_token, session_token)
                        finally:
                            _sys.exit(0)
                else:
                    # heartbeat "ligero": solo escribe lastHeartbeat para no perder la sesión
                    now = int(_t.time())
                    # escritura directa sin leer toda la sesión
                    state["db"].child(f"sessions/{uid}/lastHeartbeat").set(now, id_token)

                # Refresh de idToken cada ~10 min
                if _t.time() - last_refresh >= 600:
                    id_token = refresh_id_token(state)
                    last_refresh = _t.time()
                    # Revalidar licencia tras refresh
                    ok2, _details, _ = check_license_details(state["db"], uid, id_token)
                    if not ok2:
                        QMessageBox.critical(None, "Licencia", "Licencia inválida o expirada.")
                        release_session(state["db"], uid, id_token, session_token)
                        _sys.exit(0)

            except Exception as e:
                print("[Lic] Watcher error:", e)
                # reintenta en el siguiente ciclo

    threading.Thread(target=_license_watcher, daemon=True).start()
    try:
        mark_heartbeat_thread_started(True)
    except Exception:
        pass

    # Limpieza de sesión al salir
    def _cleanup():
        try:
            release_session(state["db"], uid, id_token, session_token)
        except Exception:
            pass
    app.aboutToQuit.connect(_cleanup)

    # --- Controller + GUI ---
    cfg_mgr = ConfigManager(BASE_DIR)

    try:
        controller = Controller(config_manager=cfg_mgr)
    except TypeError:
        controller = Controller()
        setattr(controller, "config_manager", cfg_mgr)

    if not hasattr(controller, "base_dir"):
        controller.base_dir = BASE_DIR

    win = MainWindow(controller)
    win.resize(810, 630)
    win.setMinimumSize(640, 380)
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
