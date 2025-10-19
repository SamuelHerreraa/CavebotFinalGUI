"""
function_shovel.py — Acción de SHOVEL
Solo edita en tu main: HK, attempts, cast_delay, click_delay.
"""
from typing import Callable, Tuple
import time
import keyboard
import pyautogui as pg


def do_shovel(
    hotkey: str,
    attempts: int,
    cast_delay: float,
    click_delay: float,
    center_xy: Tuple[int, int],
    is_active: Callable[[], bool],
    is_paused: Callable[[], bool],
    stop_event,
) -> None:
    if not hotkey:
        print("[shovel] HK vacío, no se ejecuta.")
        return

    attempts = max(1, int(attempts))
    for i in range(attempts):
        if stop_event.is_set():
            break
        if is_paused():
            time.sleep(0.05)
            continue
        if not is_active():
            time.sleep(0.25)
            continue

        keyboard.press_and_release(hotkey)
        time.sleep(max(0.0, float(cast_delay)))
        pg.click(center_xy[0], center_xy[1], button="left")
        time.sleep(max(0.0, float(click_delay)))
        print(f"[shovel] intento {i+1}/{attempts}")