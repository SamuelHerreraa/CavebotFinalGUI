"""
function_stairs.py — Acción de STAIRS
Solo edita en tu main: delay después del click derecho.
"""
from typing import Callable, Tuple
import time
import pyautogui as pg


def do_stairs(
    center_xy: Tuple[int, int],
    post_right_click_sleep_s: float,
    is_active: Callable[[], bool],
    is_paused: Callable[[], bool],
    stop_event,
) -> None:
    while True:
        if stop_event.is_set():
            break
        if is_paused():
            time.sleep(0.05)
            continue
        if not is_active():
            time.sleep(0.25)
            continue
        pg.click(center_xy[0], center_xy[1], button="right")
        time.sleep(max(0.0, float(post_right_click_sleep_s)))
        print("[stairs] click derecho + espera completados")
        break