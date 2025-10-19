"""
function_amulet.py — Watcher de AMULET
Solo edita en tu main: HK, poll_sleep y press_cooldown.
Región, imagen y confidence tienen defaults internos.
"""
from typing import Callable, Tuple
import time
import pyautogui as pg
import keyboard

# Defaults internos (ajústalos aquí si alguna vez cambias tu UI)
_DEFAULT_IMAGE = "./img/emptyamulet.png"
_DEFAULT_REGION = (1745, 148, 1860, 282)  # x1,y1,x2,y2
_DEFAULT_CONFIDENCE = 0.87


def run_amulet_watcher(
    hotkey: str,
    poll_sleep: float,
    press_cooldown: float,
    is_active: Callable[[], bool],
    stop_event,
    image_path: str = _DEFAULT_IMAGE,
    region: Tuple[int, int, int, int] = _DEFAULT_REGION,
    confidence: float = _DEFAULT_CONFIDENCE,
) -> None:
    if not hotkey:
        print("[amulet] HK vacío; watcher no iniciado.")
        return

    def _rect_to_region_xywh(x1, y1, x2, y2):
        return (x1, y1, max(0, x2 - x1), max(0, y2 - y1))

    last_press = 0.0
    region_xywh = _rect_to_region_xywh(*region)

    while not stop_event.is_set():
        if not is_active():
            time.sleep(poll_sleep)
            continue
        try:
            found = pg.locateOnScreen(image_path, region=region_xywh, confidence=confidence)
        except Exception:
            found = None
        now = time.monotonic()
        if found and (now - last_press) >= press_cooldown:
            keyboard.press_and_release(hotkey)
            last_press = now
            print(f"[amulet] Equip hotkey '{hotkey}' enviado.")
        time.sleep(poll_sleep)