# transparency.py
import time
import signal
import sys
import win32gui
import win32con
import pygetwindow as gw
from typing import Iterable, Tuple, Union

# Estado original para restaurar (si usas modo continuo)
_original_hwnd = None

def _set_transparency(hwnd, alpha: int):
    """Cambia la transparencia de la ventana (0 = invisible, 255 = opaco)."""
    win32gui.SetWindowLong(
        hwnd,
        win32con.GWL_EXSTYLE,
        win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED
    )
    win32gui.SetLayeredWindowAttributes(hwnd, 0, int(alpha), win32con.LWA_ALPHA)

def _restore_window(hwnd):
    """Restaura la ventana a 100% visible."""
    if hwnd:
        _set_transparency(hwnd, 255)

def _signal_handler(sig, frame):
    """Restaura transparencia al cerrar con CTRL+C o kill (modo continuo)."""
    global _original_hwnd
    if _original_hwnd:
        _restore_window(_original_hwnd)
    sys.exit(0)

def _normalize_patterns(title_substr: Union[str, Iterable[str]]) -> Tuple[str, ...]:
    """Convierte title_substr en una tupla de patrones."""
    if isinstance(title_substr, str):
        return (title_substr,)
    try:
        return tuple(title_substr)
    except TypeError:
        return (str(title_substr),)

def _find_first_window(patterns: Tuple[str, ...]):
    """Devuelve la primera ventana cuyo título contiene cualquiera de los patrones."""
    for pat in patterns:
        wins = gw.getWindowsWithTitle(pat)
        if wins:
            return wins[0]
    return None

def run(
    interval_sec: float = 1.0,
    title_substr: Union[str, Iterable[str]] = "Tibia -",
    active_alpha: int = 0,
    inactive_alpha: int = 255,
    run_once: bool = False
):
    """
    Si la ventana (cuyo título contenga cualquiera de los patrones) está activa -> aplica active_alpha.
    Si no está activa -> aplica inactive_alpha.
    Si no existe -> avisa por consola.

    Si run_once=True, hace una sola pasada y regresa (NO restaura al salir).
    Si run_once=False, repite cada interval_sec segundos (y restaura en señales).
    """
    global _original_hwnd

    # Capturar señales (útil en modo continuo para restaurar)
    try:
        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)
    except Exception:
        pass

    patterns = _normalize_patterns(title_substr)

    def _apply_once():
        global _original_hwnd   # ← CORRECCIÓN: usar global, no nonlocal
        tibia = _find_first_window(patterns)
        if tibia:
            hwnd = tibia._hWnd
            if tibia.isActive:
                _set_transparency(hwnd, active_alpha)
                if _original_hwnd is None:
                    _original_hwnd = hwnd
            else:
                _set_transparency(hwnd, inactive_alpha)
        else:
            print(f"⚠️ No se encontró ninguna ventana con títulos que contengan: {patterns}")

    if run_once:
        # One-shot: aplica y termina, sin restaurar
        _apply_once()
        return

    # Modo continuo
    try:
        while True:
            _apply_once()
            time.sleep(interval_sec)
    finally:
        # En modo continuo puedes decidir restaurar al cerrar el loop si quieres
        if _original_hwnd:
            _restore_window(_original_hwnd)
