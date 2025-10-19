"""
function_food.py — Auto-Eat periódico
Solo editas en tu main: HK_FOOD, EAT_EVERY_S, EAT_PRESSES, EAT_PRESS_DELAY_S, EAT_JITTER_S.
Este worker:
- Corre en loop hasta que stop_event esté activo.
- Se ejecuta solo si 'hotkey' NO está vacío y la ventana objetivo está activa.
- Ignora PAUSED (igual que los healers).
"""
from typing import Callable
import time
import random
import keyboard


def run_food_worker(
    hotkey: str,
    interval_s: float,
    presses: int,
    press_delay_s: float,
    jitter_s: float,
    is_active: Callable[[], bool],
    stop_event,
) -> None:
    # Pequeño yield para no chocar con otros hilos al inicio
    time.sleep(0.5)

    base_int = max(0.1, float(interval_s))
    next_ts = time.monotonic() + base_int

    while not stop_event.is_set():
        # Si no hay hotkey configurado, duerme y reintenta
        if not hotkey or not hotkey.strip():
            time.sleep(1.0)
            continue

        # Solo cuando Tibia está activa
        if not is_active():
            time.sleep(0.25)
            continue

        now = time.monotonic()
        if now >= next_ts:
            rep = max(1, int(presses))
            delay = max(0.0, float(press_delay_s))
            for i in range(rep):
                keyboard.press_and_release(hotkey)
                if i + 1 < rep and delay > 0:
                    time.sleep(delay)
            print(f"[Food] HK='{hotkey}' x{rep} (cada {interval_s:.2f}s)")

            jitter = random.uniform(-jitter_s, jitter_s) if jitter_s > 0 else 0.0
            next_ts = now + max(0.1, float(interval_s) + jitter)

        time.sleep(0.05)