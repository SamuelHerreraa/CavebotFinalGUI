# functions/function_pelar.py
from __future__ import annotations
import time, random
from typing import Tuple, Callable, Literal
import keyboard
import pyautogui as pg

pg.FAILSAFE = False

OrderMode = Literal["fixed", "shuffle", "random_start_clockwise", "random_start_counter"]

def do_pelar(
    hotkey: str,
    center_xy: Tuple[int, int],
    sqm_size: int = 30,
    is_active: Callable[[], bool] = lambda: True,
    is_paused: Callable[[], bool] = lambda: False,
    stop_event=None,
    press_delay_s: float = 0.03,
    click_delay_s: float = 0.04,
    between_sqm_sleep_s: float = 0.06,
    order_mode: OrderMode = "shuffle",          # ← MODO por defecto: aleatorio
    jitter_s: float = 0.02,                     # ← variación aleatoria ±jitter_s a cada delay
    rng: random.Random | None = None,           # ← por si quieres inyectar un RNG fijo en tests
) -> bool:
    """
    'Pelar' en las 8 casillas alrededor del jugador (centro).
    Recorre cada SQM exactamente una vez según order_mode:
      - "fixed":         N, NE, E, SE, S, SW, W, NW (tu orden original)
      - "shuffle":       orden totalmente aleatorio
      - "random_start_clockwise":   inicio aleatorio, sentido horario
      - "random_start_counter":     inicio aleatorio, sentido antihorario

    Añade jitter aleatorio a los delays para humanizar.
    Devuelve True si ejecutó al menos un intento.
    """
    if not hotkey or not center_xy or sqm_size <= 0:
        return False
    if stop_event and stop_event.is_set():
        return False
    if is_paused():
        return False
    if not is_active():
        return False

    r = rng or random
    cx, cy = int(center_xy[0]), int(center_xy[1])
    d = int(sqm_size)

    # Orden base (horario) sin incluir centro
    base_offsets = [
        (0, -d),   # N
        (d, -d),   # NE
        (d, 0),    # E
        (d, d),    # SE
        (0, d),    # S
        (-d, d),   # SW
        (-d, 0),   # W
        (-d, -d),  # NW
    ]

    # Construir el recorrido según el modo
    if order_mode == "fixed":
        offsets = list(base_offsets)
    elif order_mode == "shuffle":
        offsets = base_offsets[:]  # copia
        r.shuffle(offsets)
    elif order_mode == "random_start_clockwise":
        start = r.randrange(len(base_offsets))
        offsets = base_offsets[start:] + base_offsets[:start]
    elif order_mode == "random_start_counter":
        start = r.randrange(len(base_offsets))
        ccw = list(reversed(base_offsets))
        # ajustar el índice de inicio equivalente en CCW
        offsets = ccw[start:] + ccw[:start]
    else:
        # fallback seguro
        offsets = base_offsets[:]

    def _j(x: float) -> float:
        """Aplica jitter simétrico ±jitter_s, clamp a >=0."""
        if jitter_s > 0:
            x = x + r.uniform(-jitter_s, jitter_s)
        return max(0.0, x)

    did_any = False

    for dx, dy in offsets:
        if stop_event and stop_event.is_set():
            break
        if is_paused() or not is_active():
            break

        tx, ty = cx + dx, cy + dy

        # mover
        try:
            pg.moveTo(tx, ty, duration=0.05)
        except Exception:
            break

        # usar herramienta
        try:
            keyboard.press_and_release(hotkey)
        except Exception:
            pass
        time.sleep(_j(press_delay_s))

        # click
        try:
            pg.click()
        except Exception:
            pass

        did_any = True
        time.sleep(_j(click_delay_s + between_sqm_sleep_s))

    return did_any
