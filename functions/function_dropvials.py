"""
function_dropvials.py — Drag & drop de viales vacíos al centro de pantalla.

Uso típico (desde main, justo después de la espera post-llegada al WP):
    from functions.function_dropvials import drop_vials
    drop_vials(PLAYER_CENTER_SCREEN, _is_tibia_active, is_paused, _STOP_EVENT)

Notas:
- Sin límite por pasada: arrastra TODO lo que encuentre hasta que ya no haya más.
- Respeta 'paused' y que Tibia esté activa.
- Por simplicidad, busca en pantalla completa; puedes pasar una región opcional si quieres.
"""

from typing import Callable, Iterable, Tuple, Optional
import time
import pyautogui as pg

# Defaults internos (no toques aquí si quieres centralizar todo en main)
_DEFAULT_IMAGES: Tuple[str, ...] = (
    "img/100emptygreatvial.png",
    "img/100emptystrongvial.png",
    "img/100emptyvial.png",
)
_DEFAULT_CONFIDENCE: float = 0.97
_DEFAULT_MOVE_DURATION_S: float = 0.15   # suavidad del movimiento del mouse
_DEFAULT_BETWEEN_DRAGS_S: float = 1.0   # pausa entre cada drag&drop
_DEFAULT_SEARCH_REGION: Optional[Tuple[int, int, int, int]] = None  # (x1,y1,x2,y2) o None

def _rect_to_region_xywh(x1: int, y1: int, x2: int, y2: int):
    return (x1, y1, max(0, x2 - x1), max(0, y2 - y1))

def drop_vials(
    center_xy: Tuple[int, int],
    is_active: Callable[[], bool],
    is_paused: Callable[[], bool],
    stop_event,
    images: Iterable[str] = _DEFAULT_IMAGES,
    confidence: float = _DEFAULT_CONFIDENCE,
    move_duration_s: float = _DEFAULT_MOVE_DURATION_S,
    between_drags_s: float = _DEFAULT_BETWEEN_DRAGS_S,
    search_region: Optional[Tuple[int, int, int, int]] = _DEFAULT_SEARCH_REGION,
) -> None:
    """
    Arrastra cada icono de la lista 'images' hacia 'center_xy' hasta que ya no
    se encuentren más en pantalla/region. No retorna nada.
    """
    if stop_event.is_set():
        return
    if is_paused() or not is_active():
        return

    region_xywh = None
    if search_region and len(search_region) == 4:
        region_xywh = _rect_to_region_xywh(*search_region)

    moved_total = 0

    # Repetimos pasadas completas mientras sigamos encontrando algo.
    while not stop_event.is_set() and not is_paused() and is_active():
        moved_this_pass = 0

        for path in images:
            if stop_event.is_set() or is_paused() or not is_active():
                break

            # Bucle: mientras siga encontrando ESTE tipo de vial, lo arrastro
            while not stop_event.is_set() and not is_paused() and is_active():
                try:
                    pt = pg.locateCenterOnScreen(path, region=region_xywh, confidence=confidence)
                except Exception:
                    pt = None

                if not pt:
                    break  # pasa a siguiente imagen

                # Drag & drop
                try:
                    pg.moveTo(pt.x, pt.y, duration=move_duration_s)
                    pg.mouseDown(button="left")
                    pg.moveTo(center_xy[0], center_xy[1], duration=move_duration_s)
                    pg.mouseUp(button="left")
                    moved_total += 1
                    moved_this_pass += 1
                    print(f"[DropVials] {path} → arrastrado al centro (total: {moved_total}).")
                except Exception as e:
                    print(f"[DropVials] Error durante drag&drop: {e}")
                    break

                # pequeña pausa entre arrastres
                time.sleep(between_drags_s)

        # Si en la pasada completa no movimos nada, ya no hay más; salimos
        if moved_this_pass == 0:
            break

    if moved_total > 0:
        print(f"[DropVials] Finalizado. Viales movidos: {moved_total}.")
