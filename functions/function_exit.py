# functions/function_exit.py
# Requisitos: pip install pyautogui opencv-python pillow keyboard
# - Toma EXACTAMENTE 1 captura antes de ejecutar el Exit (con esperas de 1.5s antes y después de la foto).
# - Usa funciones RAW de pyautogui (si existen) para saltar guards en el main.
# - Crea la carpeta de capturas si no existe.

import time
import os
from datetime import datetime
import pyautogui as pg
import keyboard

pg.FAILSAFE = False
pg.PAUSE = 0.0  # sin pausa implícita entre acciones

# ===== Regiones por defecto (x1, y1, x2, y2) =====
REGION_HealthPotion_DEFAULT = (162, 573, 198, 609)
REGION_ManaPotion_DEFAULT   = (195, 571, 235, 610)
# Región amplia para ubicar el botón Exit; afínala luego a tu UI real.
REGION_Exit_DEFAULT         = (600, 300, 1320, 780)

# ===== Delays/Confianza por defecto =====
INTERVAL_DEFAULT                 = 1.0
CONFIDENCE_POTION_DEFAULT        = 0.50
CONFIDENCE_EXIT_DEFAULT          = 0.80
DELAY_AFTER_MOVE_TOPRIGHT_DEF    = 0.6
DELAY_BEFORE_EXIT_SEARCH_DEF     = 0.8

# ================= Helpers base ==================
def xyxy_to_xywh(x1, y1, x2, y2):
    """Convierte (x1,y1,x2,y2) a (x,y,w,h) sin permitir tamaños negativos."""
    return (x1, y1, max(0, x2 - x1), max(0, y2 - y1))

def find_image(region_xyxy, image_path, confidence=0.8):
    """Devuelve el centro (x,y) si encuentra la imagen en la región; None si falla o hay error."""
    try:
        x1, y1, x2, y2 = region_xyxy
        region = xyxy_to_xywh(x1, y1, x2, y2)
        return pg.locateCenterOnScreen(image_path, region=region, confidence=confidence)
    except Exception as e:
        print(f"[find_image] Error con {image_path}: {e}")
        return None

# ====== RAW controls ======
def _raw_move_to(x, y, **kwargs):
    fn = getattr(pg, "_RAW_MOVE_TO", None)
    if callable(fn):
        return fn(x, y, **kwargs)
    return pg.moveTo(x, y, **kwargs)

def _raw_click(**kwargs):
    fn = getattr(pg, "_RAW_CLICK", None)
    if callable(fn):
        return fn(**kwargs)
    return pg.click(**kwargs)

# ====== Screenshots ======
def _ensure_dir(path: str):
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as e:
        print(f"[snap] No se pudo crear carpeta '{path}': {e}")

def _timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def _take_screenshot(
    out_dir: str,
    prefix: str = "exit_",
    tag: str = "before",
    region_xyxy: tuple | None = None
) -> str | None:
    """
    Toma captura (pantalla completa o región). Devuelve ruta del archivo o None si falla.
    """
    try:
        _ensure_dir(out_dir)
        fname = f"{prefix}{_timestamp()}_{tag}.png"
        path = os.path.join(out_dir, fname)
        if region_xyxy:
            x1, y1, x2, y2 = region_xyxy
            region_xywh = xyxy_to_xywh(x1, y1, x2, y2)
            img = pg.screenshot(region=region_xywh)
        else:
            img = pg.screenshot()
        img.save(path)
        print(f"[snap] Captura guardada: {path}")
        return path
    except Exception as e:
        print(f"[snap] Error al guardar captura: {e}")
        return None

# ============ Secuencia Exit ============
def _do_sequence_topright_then_exit(
    region_exit, img_exit, confidence_exit,
    delay_after_move=DELAY_AFTER_MOVE_TOPRIGHT_DEF,
    delay_before_exit_search=DELAY_BEFORE_EXIT_SEARCH_DEF,
    prekey=None
):
    """
    1) prekey (opcional, ej. 'esc')
    2) mouse a top-right + click
    3) buscar sprite 'Exit' y click
    """
    # 0) Tecla previa
    if prekey:
        try:
            keyboard.press_and_release(prekey)
            print(f"[seq] prekey '{prekey}' enviada")
            time.sleep(0.15)
        except Exception as e:
            print(f"[seq] no pude enviar prekey '{prekey}': {e}")

    # 1) Mover al top-right
    try:
        w, _ = pg.size()
        _raw_move_to(w - 1, 0)
        print(f"[seq] mouse -> top-right ({w-1}, 0)")
        time.sleep(delay_after_move)
    except Exception as e:
        print(f"[seq] moveTo top-right falló: {e}")

    # 2) Click
    try:
        _raw_click()
        print("[seq] click en esquina superior derecha")
    except Exception as e:
        print(f"[seq] click top-right falló: {e}")

    # 3) Buscar Exit
    time.sleep(delay_before_exit_search)
    exit_pos = find_image(region_exit, img_exit, confidence_exit)

    if exit_pos:
        try:
            _raw_move_to(exit_pos[0], exit_pos[1])
            _raw_click()
            print(f"[seq] EXIT encontrado y clic en {exit_pos}")
            return True
        except Exception as e:
            print(f"[seq] click EXIT falló: {e}")
            return False
    else:
        print(f"[seq] EXIT no encontrado en región {region_exit} con conf={confidence_exit}")
        return False

# ============ Loop principal del watcher ============
def run_exit_sequence_on_potion(
    # Qué imagen revisar (elige 1 para mana, 1 para health)
    check_manapotion="manapotion.png",              # ej: "strongmanapotion.png"
    check_healthpotion="stronghealthpotion.png",    # ej: "healthpotion.png"

    # Activar/desactivar revisión por tipo ("x" = sí, "" = no)
    checkmanapotion="x",
    checkhealthpotion="",

    # Rutas base (si solo pones nombre, asume carpeta img/)
    base_dir="img",

    # Regiones
    region_shp=REGION_HealthPotion_DEFAULT,
    region_smp=REGION_ManaPotion_DEFAULT,
    region_exit=REGION_Exit_DEFAULT,

    # Imagen de EXIT
    img_exit="img/Exit.png",

    # Tiempos y confianza
    interval=INTERVAL_DEFAULT,
    confidence_potion=CONFIDENCE_POTION_DEFAULT,
    confidence_exit=CONFIDENCE_EXIT_DEFAULT,
    delay_after_move_topright=DELAY_AFTER_MOVE_TOPRIGHT_DEF,
    delay_before_exit_search=DELAY_BEFORE_EXIT_SEARCH_DEF,

    # Secuencia previa / control / salida
    prekey=None,                # p.ej., "esc" para abrir menú
    on_take_control=None,       # callback -> el main puede setear un flag para bloquear su loop
    on_release_control=None,    # callback -> liberar ese flag
    on_exit=None,               # callback -> notificar al main (e.g., _request_stop)
    use_os_exit=False,          # si True, mata el proceso entero con os._exit(0)

    # ===== Captura única =====
    snapshot_dir="exit",        # carpeta donde guardar capturas
    snapshot_mode="full",       # "full" | "exit_region" | tuple(x1,y1,x2,y2)
    snapshot_prefix="exit_",    # prefijo de archivo
    snapshot_wait_before=1.5,   # esperar ANTES de tomar la foto
    snapshot_wait_after=1.5,    # esperar DESPUÉS de tomar la foto (antes de mover el mouse)
):
    """
    ORDEN EXACTO (según tu requerimiento):
      1) Llega WP → combate → loot → comprueba pociones (esto lo decide el main).
      2) Si se detecta la imagen (trigger):
         a) Espera 1.5s (snapshot_wait_before)
         b) Toma **1** foto (y la guarda en snapshot_dir)
         c) Espera 1.5s (snapshot_wait_after)
         d) Toma control, mueve mouse al norte-derecha, click, busca/clica Exit
         e) Cierra el main (on_exit) o termina el proceso (use_os_exit)
    """

    # Normaliza rutas si te pasan solo el nombre
    mana_img   = check_manapotion   if "/" in check_manapotion   else f"{base_dir}/{check_manapotion}"
    health_img = check_healthpotion if "/" in check_healthpotion else f"{base_dir}/{check_healthpotion}"

    enable_mana   = (checkmanapotion.lower() == "x")
    enable_health = (checkhealthpotion.lower() == "x")

    # Mensaje de modo
    if enable_mana and not enable_health:
        print(f"[look] Modo: SOLO MANA ({mana_img})")
    elif enable_health and not enable_mana:
        print(f"[look] Modo: SOLO HEALTH ({health_img})")
    elif enable_mana and enable_health:
        print(f"[look] Modo: AMBAS (cualquiera dispara)")
        print(f"[look] Mana img: {mana_img} | Health img: {health_img}")
    else:
        print("[look] Ningún tipo activado (checkmanapotion='' y checkhealthpotion=''). No hay nada que comprobar.")
        return False

    # Resolver región para la captura si aplica
    def _resolve_snapshot_region():
        if snapshot_mode == "full":
            return None
        if snapshot_mode == "exit_region":
            return region_exit
        if isinstance(snapshot_mode, (tuple, list)) and len(snapshot_mode) == 4:
            return tuple(snapshot_mode)
        return None

    while True:
        mana_seen = False
        health_seen = False

        if enable_mana:
            mana_seen = find_image(region_smp, mana_img, confidence_potion) is not None
        if enable_health:
            health_seen = find_image(region_shp, health_img, confidence_potion) is not None

        mana_log = "NO VISTA" if not enable_mana else ("VISTA" if mana_seen else "NO VISTA")
        health_log = "NO VISTA" if not enable_health else ("VISTA" if health_seen else "NO VISTA")
        print(f"[look] MANA: {mana_log} | HEALTH: {health_log}")

        trigger = (enable_mana and mana_seen) or (enable_health and health_seen)

        if trigger:
            print("[look] Trigger → preparando secuencia de EXIT con captura única...")

            # a) Espera antes de la foto
            time.sleep(max(0.0, float(snapshot_wait_before)))

            # b) Toma la ÚNICA foto (pantalla completa o región)
            region_for_snap = _resolve_snapshot_region()
            _take_screenshot(
                out_dir=snapshot_dir,
                prefix=snapshot_prefix,
                tag="before",
                region_xyxy=region_for_snap
            )

            # c) Espera post-foto antes de mover el mouse
            time.sleep(max(0.0, float(snapshot_wait_after)))

            # d) Avisa al main que tomas control del mouse
            if callable(on_take_control):
                try:
                    on_take_control()
                except Exception as e:
                    print(f"[look] on_take_control err: {e}")

            try:
                clicked_exit = _do_sequence_topright_then_exit(
                    region_exit, img_exit, confidence_exit,
                    delay_after_move=delay_after_move_topright,
                    delay_before_exit_search=delay_before_exit_search,
                    prekey=prekey
                )
            finally:
                # Libera control aunque falle
                if callable(on_release_control):
                    try:
                        on_release_control()
                    except Exception as e:
                        print(f"[look] on_release_control err: {e}")

            if clicked_exit:
                print("[look] EXIT clickeado.")
                # e) Cerrar main o terminar proceso
                if callable(on_exit):
                    try:
                        on_exit()
                    except Exception as e:
                        print(f"[look] on_exit lanzó excepción: {e}")
                if use_os_exit:
                    print("[look] use_os_exit=True → os._exit(0)")
                    os._exit(0)
                return True

        time.sleep(interval)
