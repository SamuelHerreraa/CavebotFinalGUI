"""
function_zoom.py — Click por imagen en región dedicada (zoom)
Solo editas en tu main: ZOOM_RECT_X1Y1X2Y2, ZOOM_CONFIDENCE, ZOOM_CLICK_DELAY.
"""
import time
from typing import Tuple, Optional
import pyautogui as pg

def _rect_to_region_xywh(x1, y1, x2, y2):
    return (x1, y1, max(0, x2 - x1), max(0, y2 - y1))

def do_zoom_click(
    target_img_path: str,
    region_rect_x1y1x2y2: Tuple[int, int, int, int],
    confidence: float,
    click_delay_s: float
) -> bool:
    """
    Busca 'target_img_path' SOLO en 'region_rect_x1y1x2y2'. Si lo encuentra, hace click y duerme 'click_delay_s'.
    Devuelve True si clickeó, False si no encontró.
    """
    region = _rect_to_region_xywh(*region_rect_x1y1x2y2)
    try:
        pt: Optional[pg.Point] = pg.locateCenterOnScreen(
            target_img_path, region=region, confidence=float(confidence)
        )
    except Exception:
        pt = None

    if pt:
        pg.moveTo(pt.x, pt.y, duration=0.05)
        pg.click()
        time.sleep(max(0.0, float(click_delay_s)))
        return True
    return False