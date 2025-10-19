"""
function_loot.py — Acción de LOOT inmediata
Solo editas en tu main: HK_LOOT, LOOT_REPEAT, LOOT_DELAY.
"""
import time
import keyboard

def do_loot(hotkey: str, repeat: int, delay_s: float) -> None:
    """
    Envía el hotkey de loot 'repeat' veces con 'delay_s' entre pulsos.
    No hace nada si 'hotkey' viene vacío.
    """
    if not hotkey:
        # Silencioso: si no hay hotkey configurado, simplemente no se ejecuta.
        return
    rep = max(1, int(repeat))
    delay = max(0.0, float(delay_s))
    for _ in range(rep):
        keyboard.press_and_release(hotkey)
        if delay > 0:
            time.sleep(delay)
