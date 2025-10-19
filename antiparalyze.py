"""
antiparalyze.py

Lee una región de pantalla (x1, y1, x2, y2) en bucle; si detecta una imagen dentro
de esa región, envía una hotkey para quitar paralyze (o cualquier acción similar).

Dependencias: pip install pyautogui keyboard pillow opencv-python

Uso básico (como módulo):
    from antiparalyze import run_antiparalyze
    run_antiparalyze(
        region=(1746, 279, 1858, 300),
        image_path="img/paralyze2.png",
        hotkey="f2"
    )

Uso como script (prueba rápida):
    python antiparalyze.py
"""
from __future__ import annotations
import time
from typing import Iterable, Optional, Tuple

import keyboard
import pyautogui as pg

# Opcional: si tienes OpenCV instalado, pyautogui usará cv2 para locate* con 'confidence'
# Requiere: pip install opencv-python

pg.FAILSAFE = False
pg.PAUSE = 0.0

# -------------------------------
# Helpers
# -------------------------------

def _rect_to_region_xywh(x1: int, y1: int, x2: int, y2: int) -> Tuple[int, int, int, int]:
    """Convierte (x1,y1,x2,y2) a (x, y, w, h) asegurando valores no negativos."""
    return (x1, y1, max(0, x2 - x1), max(0, y2 - y1))


def _is_target_window_active(prefixes: Iterable[str]) -> bool:
    """Devuelve True si la ventana activa empieza con alguno de los prefijos dados."""
    try:
        title = pg.getActiveWindowTitle()
        if not title or not isinstance(title, str):
            return False
        return any(title.startswith(pref) for pref in prefixes)
    except Exception:
        return False


# -------------------------------
# Core loop
# -------------------------------

def run_antiparalyze(
    region: Tuple[int, int, int, int],
    image_path: str,
    hotkey: str,
    *,
    confidence: float = 0.85,
    poll_sleep: float = 0.10,
    press_cooldown: float = 0.70,
    active_window_prefixes: Tuple[str, ...] = ("Tibia -", "Tibia"),
    until_time: Optional[float] = None,
) -> None:
    """
    Bucle simple: busca 'image_path' dentro de 'region' y si aparece, pulsa 'hotkey'.

    Args:
        region: (x1, y1, x2, y2) zona donde buscar la imagen.
        image_path: ruta del PNG/JPG a detectar (por ejemplo, icono de Paralyze).
        hotkey: tecla/hotkey a enviar cuando se detecte la imagen.
        confidence: umbral de coincidencia (0-1). Requiere OpenCV.
        poll_sleep: pausa entre iteraciones del loop (segundos).
        press_cooldown: tiempo mínimo entre dos pulsaciones consecutivas.
        active_window_prefixes: prefijos válidos del título de ventana (para actuar solo en Tibia).
        until_time: si se especifica (epoch seconds), termina el loop al llegar a esa hora.

    Comportamiento:
        - Solo hace algo cuando la ventana activa coincide con los prefijos dados.
        - Si la imagen se detecta y ha pasado el cooldown, envía la hotkey.
        - Se puede interrumpir con Ctrl+C.
    """
    if not hotkey or not hotkey.strip():
        print("[AntiParalyze] HOTKEY vacío; no hay nada que pulsar. Saliendo.")
        return

    x1, y1, x2, y2 = region
    region_xywh = _rect_to_region_xywh(x1, y1, x2, y2)

    print("[AntiParalyze] Iniciado")
    print(f"  Región: (x1={x1}, y1={y1}, x2={x2}, y2={y2}) → XYWH={region_xywh}")
    print(f"  Imagen: {image_path} | Conf={confidence}")
    print(f"  Hotkey: {hotkey} | Cooldown={press_cooldown:.2f}s | Poll={poll_sleep:.2f}s")

    last_press = 0.0
    try:
        while True:
            if until_time is not None and time.time() >= until_time:
                print("[AntiParalyze] Tiempo límite alcanzado; fin.")
                break

            # Solo operar si la ventana objetivo está activa
            if not _is_target_window_active(active_window_prefixes):
                time.sleep(poll_sleep)
                continue

            try:
                found = pg.locateOnScreen(image_path, region=region_xywh, confidence=confidence)
            except Exception:
                found = None

            now = time.monotonic()
            if found and (now - last_press) >= press_cooldown:
                keyboard.press_and_release(hotkey)
                print(f"[AntiParalyze] Detectado '{image_path}'. Hotkey '{hotkey}' enviada.")
                last_press = now

            time.sleep(poll_sleep)
    except KeyboardInterrupt:
        print("\n[AntiParalyze] Interrumpido por el usuario (Ctrl+C). Bye.")


# Ejecución directa para pruebas rápidas
if __name__ == "__main__":
    # Valores de ejemplo; ajusta a tu HUD
    DEMO_REGION = (1746, 279, 1858, 300)  # x1,y1,x2,y2
    DEMO_IMAGE  = "img/paralyze2.png"
    DEMO_HOTKEY = "f2"

    run_antiparalyze(
        region=DEMO_REGION,
        image_path=DEMO_IMAGE,
        hotkey=DEMO_HOTKEY,
        confidence=0.85,
        poll_sleep=0.10,
        press_cooldown=0.70,
    )