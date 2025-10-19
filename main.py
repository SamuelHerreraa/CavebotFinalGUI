# main.py
# Requisitos: pip install keyboard pyautogui opencv-python pillow pygetwindow pywin32
# Carpetas/archivos: transparency.py, antiparalyze.py, ./marcas/wp1.png..., ./img/utitoon.png
# Módulos externos en carpeta: functions/
# Windows 11, 1920x1080 @ 100%

# =============================================================
# ===============  BLOQUE DE CONFIGURACIÓN ÚNICO  =============
# === SOLO editas hotkeys, intentos, delays, regiones, imgs ===
# =============================================================

# --- Salida sin búfer y en UTF-8 para la GUI ---
import sys, json
try:
    # En Py3.7+ permite line_buffering; si no, no pasa nada.
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
except Exception:
    pass

def GUI_ROUTE_LOG(tab: str, idx: int, name=None, action=None, label=None, phase=None):
    """
    Emite un log que la GUI sabe parsear para actualizar el 'Inicio: ...'
    y (si se puede) el highlight. Siempre con flush inmediato.
    """
    rec = {"route": {"tab": str(tab), "idx": int(idx)}}
    if name is not None:   rec["name"]   = str(name)
    if action is not None: rec["action"] = str(action)
    if label is not None:  rec["label"]  = str(label)
    if phase is not None:  rec["phase"]  = str(phase)
    print("[ROUTE] " + json.dumps(rec, ensure_ascii=False), flush=True)


# --- Ventana/estado general ---
HK_TOGGLE_PAUSE   = "home"
HK_QUIT           = "-"
TARGET_WINDOW_PREFIXES = ("Tibia -", "Tibia")

# Rendimiento / ciclos
LOOP_SLEEP_S      = 0.01
NOT_ACTIVE_SLEEP  = 0.25

# --- Coordenadas clave del juego ---
PLAYER_CENTER_MINIMAP = (1807, 82)
PLAYER_CENTER_SCREEN  = (862, 453)

# --- Ruta y Waypoints ---
ROUTE = ["wp1", "wp2", "wp3", "wp4"]
WAYPOINTS = [f"./marcas/{name}.png" for name in ROUTE]
# Acciones soportadas: "rope", "shovel", "stairs", "lure", "zoom", "none", "ignore", "goto"
ROUTE_ACTIONS = ["none", "none", "none", "none"]

# Tiempos de flujo de ruta (defaults)
WAIT_AFTER_ARRIVAL_S   = 0.0
WAIT_BEFORE_NEXT_WP_S  = 0.0

# --- Lure (defaults) ---
LURE_MAX_TRIES   = 10
LURE_PAUSE_KEY   = "esc"
LURE_PAUSE_SEC   = 1.5
LURE_RESUME_SEC  = 1.5

# --- Food / Auto-Eat ---
HK_FOOD = "5"
EAT_EVERY_S       = 180.0
EAT_PRESSES       = 2
EAT_PRESS_DELAY_S = 0.25
EAT_JITTER_S      = 0.25

# --- Ataque / Loot entre kills ---
ATTACK_UNTIL_ARRIVED_MODE = "x"
LOOT_AFTER_KILL_MODE      = "x"
LOOT_BETWEEN_KILLS_DELAY  = 0.50

# ======== DROP VIALS ========
dropvials = "x"

# ======================== HEALING ==========================
HK_HIGH_HEALING = "f3"
HK_LOW_HEALING  = "f5"
HK_MANA_POTION  = "f6"

HIGH_HEAL_POS = (1845, 308); HIGH_HEAL_RGB = (218, 79, 79)
LOW_HEAL_POS  = (1811, 307); LOW_HEAL_RGB  = (191, 64, 64)
MANA_POS      = (1840, 322); MANA_RGB      = (101, 98, 239)

HEAL_TOLERANCE = 90
POTION_COOLDOWN_S      = 1.0
HIGH_HEAL_MIN_INTERVAL = 0.45
HEAL_POLL_SLEEP        = 0.03

# =================== ROTACIÓN DE ATAQUE ====================
HK_EXORI_GRAN = "1"
HK_EXORI      = "2"
HK_EXORI_MAS  = "3"
HK_EXORI_HUR  = ""
HK_EXORI_ICO  = ""
SMART_TARGET_ROTATION = ""

# =================== UMBRALES DE ATAQUE (N+) ====================
USE_EXORI_MIN_PLUS       = "1+"
USE_EXORIGRAN_MIN_PLUS   = "1+"
USE_EXORIMAS_MIN_PLUS    = "1+"
USE_EXORIHUR_MIN_PLUS    = ""
USE_EXORICO_MIN_PLUS     = ""

SPELL_ROTATION_COOLDOWN    = 2.1
SPELL_ROTATION_START_DELAY = 1.5
ATTACK_PRESS_REPEAT        = 2
ATTACK_PRESS_INTERVAL      = 0.25

# ================== ROTACIÓN DE SOPORTE ====================
HK_EXETARES     = "f1"
HK_BOOST        = ""
HK_EXETAAMPRES  = ""

SUPPORT_COOLDOWN     = 2.0
SUPPORT_START_DELAY  = 1.0
SUPPORT_ROTATION     = ["boost", "res", "ampres"]

EXETARES_PERIOD_S    = 4.0
EXETAAMPRES_PERIOD_S = 4.0

# Barra superior / buffs
PARALYZEBAR_RECT_X1Y1X2Y2 = (1746, 279, 1858, 300)
UTITOOON_IMG_PATH         = "img/utitoon.png"
UTITOOON_CONFIDENCE       = 0.85

# BOOST anti-spam por pixel
BOOST_REQUIRE_PIXEL = True
BOOST_COLOR_POS     = (1831, 322)
BOOST_COLOR_RGB     = (101, 98, 239)
BOOST_COLOR_TOL     = 20
BOOST_HUE_MIN_DEG   = 220
BOOST_HUE_MAX_DEG   = 260
BOOST_MIN_S         = 0.35
BOOST_MIN_V         = 0.20

# ============ Navegación por imagen / centrado ============
CONFIDENCE               = 0.87
MAX_TRIES_PER_WP         = 30
SLEEP_AFTER_CLICK        = 0.05
CENTER_TOLERANCE_PX      = 6
LURE_CENTER_TOLERANCE_PX = 2
ATTEMPT_LOOP_IDLE_SLEEP  = 0.05

# Skip rápido
SKIP_IF_NOT_VISIBLE    = "x"
SKIP_NOT_VISIBLE_AFTER = 3

# =================== ACCIONES rope/shovel/stairs ===========
HK_ROPE = "f10"
ROPE_ATTEMPTS = 1
ROPE_CAST_DELAY = 1.0
ROPE_CLICK_DELAY = 1.0

HK_SHOVEL = "f11"
SHOVEL_ATTEMPTS = 1
SHOVEL_CAST_DELAY = 1.0
SHOVEL_CLICK_DELAY = 1.0

STAIRS_POST_RIGHT_CLICK_SLEEP = 1.0

# ================== EQUIPO (amulet/ring) ==================
HK_AMULET = ""
AMULET_POLL_SLEEP = 0.20
AMULET_PRESS_COOLDOWN = 0.60
AMULET_IMG_PATH = "./img/emptyamulet.png"
AMULET_REGION_X1Y1X2Y2 = (1745, 148, 1860, 282)
AMULET_CONFIDENCE = 0.87

HK_RING = ""
RING_POLL_SLEEP = 0.20
RING_PRESS_COOLDOWN = 0.60
RING_IMG_PATH = "./img/emptyring.png"
RING_REGION_X1Y1X2Y2 = (1745, 148, 1860, 282)
RING_CONFIDENCE = 0.87

# ========================= LOOT ============================
HK_LOOT     = "add"
LOOT_REPEAT = 1
LOOT_DELAY  = 0.18

# ===================== CREATURE CHECK ======================
CREATURE_XY_START       = (1594, 103)
CREATURE_ROW_DY         = 23
CREATURE_MAX_ROWS       = 8
CREATURE_COLOR          = (0, 0, 0)
CREATURE_POLL_SLEEP     = 0.15
CREATURE_LOG_COOLDOWN   = 1.0

IGNORE_CREATURES_AT_MOST = "1"

CREATURE_DEAD_CHECK_POS = (1626, 103)
CREATURE_DEAD_CHECK_RGB = (60, 60, 60)
CREATURE_DEAD_CHECK_TOL = 12

# =================== BATTLELIST (franja) ===================
BATTLELIST_RECT_X1Y1X2Y2 = (1568, 80, 1594, 109)
RUN_MIN_SAMPLES          = 10
ROW_SCAN_STEP            = 2
RED_SAMPLE_STEP          = 2
BATTLELIST_DEBUG_COOLDOWN= 1.0

# Targeting / prime loop
HK_TARGET                = "9"
TARGET_RETRY_SLEEP       = 0.25
TARGET_MIN_INTERVAL      = 0.6
TARGET_NEED_NORED_STREAK = 3
TARGET_MAX_BURST         = 3
TARGET_BACKOFF_S         = 1.0

# ================= EXIT-on-POT =============================
exit_when_no_pots       = "x"
POTION_CHECK_MANA_IMG   = "smp.png"
POTION_CHECK_HEALTH_IMG = ""
CHECK_MANA_ON           = "x"
CHECK_HEALTH_ON         = ""
EXIT_REGION_HEALTH_X1Y1X2Y2 = (916, 843, 949, 880)
EXIT_REGION_MANA_X1Y1X2Y2   = (876, 837, 912, 879)
EXIT_REGION_EXIT_X1Y1X2Y2   = (1081, 569, 1135, 603)
EXIT_IMG_PATH                    = "img/Exit.png"
EXIT_INTERVAL_S                  = 1.0
EXIT_CONFIDENCE_POTION           = 0.50
EXIT_CONFIDENCE_EXIT             = 0.80
EXIT_DELAY_AFTER_MOVE_TOPRIGHT_S = 1.0
EXIT_DELAY_BEFORE_EXIT_SEARCH_S  = 1.5

HEAL_STABLE_HOLD_S = 0.8

# =================== Anti-Paralyze =========================
HK_REMOVE_PARALYZE    = "f2"
PARALYZE_IMG_PATH     = "img/paralyze2.png"
PARALYZE_CONFIDENCE   = 0.85
PARALYZE_POLL_SLEEP   = 0.10
PARALYZE_PRESS_COOLDOWN = 0.70

# ========================= ZOOM ============================
ZOOM_RECT_X1Y1X2Y2 = (0, 0, 0, 0)
ZOOM_CONFIDENCE    = 0.99
ZOOM_CLICK_DELAY   = 1.5

# ======================== RETRY LOGIC ======================
RETRY_SAME_WP_ONLY_IF_COMBAT = True

# --- OVERRIDES generados por la GUI (runtime_cfg.py) ---
# IMPORTA AL FINAL para que NO se pisen los valores del perfil.
try:
    from runtime_cfg import *   # ← sobreescribe variables si existen

    # ========= ROUTE helpers (tabs, goto, attach) =========
    def _route_get_tab_data(tab_name: str):
        tabs = globals().get("ROUTE_TABS") or {}
        if not isinstance(tabs, dict):
            return None
        return tabs.get(tab_name)

    def _route_find_label_index(tab_name: str, label: str) -> int:
        td = _route_get_tab_data(tab_name)
        if not td:
            return -1
        labels = td.get("ROUTE_LABELS") or []
        try:
            return int(labels.index(label))
        except Exception:
            return -1

    def _route_arrays_for_tab(tab_name: str):
        td = _route_get_tab_data(tab_name)
        if not td:
            return [], [], [], []
        route   = list(td.get("ROUTE") or [])
        actions = list(td.get("ROUTE_ACTIONS") or [])
        labels  = list(td.get("ROUTE_LABELS") or [])
        gotos   = list(td.get("ROUTE_GOTO") or [])
        L = max(len(route), len(actions), len(labels), len(gotos))
        while len(route)   < L: route.append("")
        while len(actions) < L: actions.append("none")
        while len(labels)  < L: labels.append("")
        while len(gotos)   < L: gotos.append("")
        return route, actions, labels, gotos

    def run_route_engine(click_wp_fn=None, do_action_fn=None):
        """
        Recorre la ruta respetando tabs, GOTO y punto de arranque opcional (ROUTE_ATTACH).
        Emite logs que la GUI usa para resaltar fila/tab en vivo.

        - click_wp_fn(tab_name, index, wp_name, action) -> bool (True si llegó)
        - do_action_fn(tab_name, index, action, wp_name) -> None
        Si no pasas funciones, solo hace sleeps y logs.
        """
        active_tab = globals().get("ROUTE_ACTIVE_TAB", "hunt")

        attach = globals().get("ROUTE_ATTACH", {"tab": "", "index": -1})
        try:
            attach_idx = int(attach.get("index", -1))
        except Exception:
            attach_idx = -1
        attach_tab = str(attach.get("tab", "") or "").strip()
        if attach_idx >= 0 and attach_tab:
            active_tab = attach_tab
            start_index = attach_idx
        else:
            start_index = 0

        print(f"[ROUTE] start tab={active_tab} i={start_index}")

        while True:
            route, actions, labels, gotos = _route_arrays_for_tab(active_tab)
            if not route:
                print(f"[ROUTE] empty tab='{active_tab}' → done")
                break

            i = start_index
            start_index = 0

            while i < len(route):
                wp_name  = str(route[i] or "").strip()
                action   = str(actions[i] or "none").strip().lower()
                label    = str(labels[i] or "").strip()
                goto_str = str(gotos[i] or "").strip()

                # Log para GUI
                print(f"[ROUTE] tab={active_tab} i={i} wp={wp_name or f'wp{i+1}'} action={action}")

                # Esperas (si existen en runtime_cfg)
                try:
                    if WAIT_BEFORE_NEXT_WP_S:
                        time.sleep(float(WAIT_BEFORE_NEXT_WP_S))
                except Exception:
                    pass

                # Click/movimiento al waypoint (si nos dan callback)
                arrived = True
                if callable(click_wp_fn):
                    try:
                        arrived = bool(click_wp_fn(active_tab, i, wp_name, action))
                    except Exception:
                        arrived = True

                if arrived:
                    try:
                        if WAIT_AFTER_ARRIVAL_S:
                            time.sleep(float(WAIT_AFTER_ARRIVAL_S))
                    except Exception:
                        pass

                # Acción complementaria
                if callable(do_action_fn):
                    try:
                        do_action_fn(active_tab, i, action, wp_name)
                    except Exception:
                        pass

                # ¿GOTO?
                if action == "goto" and goto_str and ":" in goto_str:
                    to_tab, to_label = [s.strip() for s in goto_str.split(":", 1)]
                    j = _route_find_label_index(to_tab, to_label)
                    print(f"[ROUTE] goto → tab={to_tab} label={to_label} index={j}")
                    if j >= 0:
                        active_tab = to_tab
                        start_index = j
                        break
                    else:
                        print(f"[ROUTE] goto destino no encontrado: {to_tab}:{to_label} → continuar")

                i += 1
            else:
                print(f"[ROUTE] tab '{active_tab}' completed → done")
                break
    print("[main] runtime_cfg importado (override).")
except Exception as e:
    print(f"[main] runtime_cfg opcional ausente: {e}")

# Re-derivar dependientes tras el override (por si ROUTE cambió)
try:
    WAYPOINTS = [f"./marcas/{name}.png" for name in ROUTE]
except Exception:
    pass

# ======= SOPORTE DE TABS + GOTO (NUEVO) =======
def _pad_arrays(route, actions, labels, gotos):
    L = max(len(route), len(actions), len(labels), len(gotos))
    route   = list(route)   + [""]    * (L - len(route))
    actions = list(actions) + ["none"]* (L - len(actions))
    labels  = list(labels)  + [""]    * (L - len(labels))
    gotos   = list(gotos)   + [""]    * (L - len(gotos))
    return route, actions, labels, gotos

def _build_tabs_from_cfg():
    tabs = {}
    try:
        # Si existe ROUTE_TABS (multi-tab)
        if isinstance(ROUTE_TABS, dict) and ROUTE_TABS:
            for tab_name, data in ROUTE_TABS.items():
                r  = data.get("ROUTE", [])
                a  = data.get("ROUTE_ACTIONS", [])
                lb = data.get("ROUTE_LABELS", [])
                gt = data.get("ROUTE_GOTO", [])
                r, a, lb, gt = _pad_arrays(r, a, lb, gt)
                tabs[str(tab_name)] = {"route": r, "actions": a, "labels": lb, "gotos": gt}
            return tabs
    except Exception:
        pass

    # Compat: solo arrays planos
    r  = globals().get("ROUTE", []) or []
    a  = globals().get("ROUTE_ACTIONS", []) or []
    lb = globals().get("ROUTE_LABELS", []) or []
    gt = globals().get("ROUTE_GOTO", []) or []
    r, a, lb, gt = _pad_arrays(r, a, lb, gt)
    tabs["hunt"] = {"route": r, "actions": a, "labels": lb, "gotos": gt}
    return tabs

def _tab_arrays(tabs, tab_name):
    d = tabs.get(tab_name) or {}
    return d.get("route", []), d.get("actions", []), d.get("labels", []), d.get("gotos", [])

def _label_index(labels, route):
    """
    Mapa etiqueta->índice (primera aparición). Fallback:
    si no hay etiqueta, acepta nombre exacto del WP como 'etiqueta'.
    """
    idx = {}
    for i, lab in enumerate(labels):
        s = str(lab or "").strip()
        if s and s not in idx:
            idx[s] = i
    # fallback: permitir 'label' == nombre del wp
    for i, name in enumerate(route):
        s = str(name or "").strip()
        if s and s not in idx:
            idx[s] = i
    return idx

# Log breve para verificar tiempos/tries cargados del perfil
try:
    print(
        f"[cfg] WAIT_AFTER_ARRIVAL_S={WAIT_AFTER_ARRIVAL_S} | "
        f"WAIT_BEFORE_NEXT_WP_S={WAIT_BEFORE_NEXT_WP_S} | "
        f"SLEEP_AFTER_CLICK={SLEEP_AFTER_CLICK} | MAX_TRIES_PER_WP={MAX_TRIES_PER_WP} | "
        f"LURE_MAX_TRIES={LURE_MAX_TRIES} | LURE_PAUSE_SEC={LURE_PAUSE_SEC} | LURE_RESUME_SEC={LURE_RESUME_SEC}"
    )
except Exception:
    pass

# =============================================================
# =================== CÓDIGO DEL PROGRAMA =====================
# =============================================================

import re
import time
import signal
import sys
import random
import colorsys
from threading import Event, Thread, Lock

import keyboard
import pyautogui as pg

from transparency import run as run_transparency
from functions.function_rope import do_rope
from functions.function_shovel import do_shovel
from functions.function_stairs import do_stairs
from functions.function_amulet import run_amulet_watcher
from functions.function_ring import run_ring_watcher
from functions.function_loot import do_loot
from functions.function_zoom import do_zoom_click
from functions.function_food import run_food_worker
from functions.function_dropvials import drop_vials
from antiparalyze import run_antiparalyze

pg.FAILSAFE = False
pg.PAUSE = 0.0

# ========================================================

# ===================== ESTADO GLOBAL =======================
try:
    PAUSED
except NameError:
    PAUSED = True

_STOP_EVENT = Event()
last_action_used = "none"
retry_same_wp_once = False
_pot_watcher_thread = None

EXIT_TAKING_CONTROL = Event()

SOFT_PAUSED = PAUSED
HARD_PAUSED = False

def _handle_signal(signum, frame):
    print("\n[main] Señal recibida, saliendo…")
    sys.exit(0)

for _sig in (signal.SIGINT, signal.SIGTERM):
    try:
        signal.signal(_sig, _handle_signal)
    except Exception:
        pass

def _is_tibia_active() -> bool:
    try:
        title = pg.getActiveWindowTitle()
        if not title or not isinstance(title, str):
            return False
        return any(title.startswith(pref) for pref in TARGET_WINDOW_PREFIXES)
    except Exception:
        return False

# ---------- Pausas ----------
def is_soft_paused() -> bool:
    return bool(SOFT_PAUSED) or _STOP_EVENT.is_set()

def is_hard_paused() -> bool:
    return bool(HARD_PAUSED) or _STOP_EVENT.is_set()

def is_paused() -> bool:
    return is_soft_paused() or is_hard_paused()

def _toggle_soft_pause():
    global SOFT_PAUSED, PAUSED
    SOFT_PAUSED = not SOFT_PAUSED
    PAUSED = SOFT_PAUSED
    state = "PAUSA SUAVE (HOME)" if SOFT_PAUSED else "RUN"
    print(f"[STATE] {state}")

def _toggle_hard_pause():
    global HARD_PAUSED, SOFT_PAUSED, PAUSED
    HARD_PAUSED = not HARD_PAUSED
    if HARD_PAUSED:
        SOFT_PAUSED = True
        PAUSED = True
        print("[STATE] PAUSA DURA (END) ACTIVADA: teclado y ratón bloqueados.")
    else:
        PAUSED = SOFT_PAUSED
        print("[STATE] PAUSA DURA (END) DESACTIVADA.")

def _request_stop():
    print("[STATE] STOP solicitado (hotkey). Cerrando…")
    _STOP_EVENT.set()

# ---------- Helpers geom / screen ----------
def region_from_center(cx, cy, half=60):
    return (cx - half, cy - half, half * 2, half * 2)

def _rect_to_region_xywh(x1, y1, x2, y2):
    return (x1, y1, max(0, x2 - x1), max(0, y2 - y1))

def find_center(img_path, region_xywh, confidence):
    try:
        return pg.locateCenterOnScreen(img_path, region=region_xywh, confidence=confidence)
    except Exception:
        return None

def is_centered(pt, region_center, tol_px):
    return abs(pt.x - region_center[0]) <= tol_px and abs(pt.y - region_center[1]) <= tol_px

def click_point(pt):
    pg.moveTo(pt.x, pt.y, duration=0.05)
    pg.click()

# --- Pixel/color utils ---
def _get_pixel_rgb(x: int, y: int):
    try:
        r, g, b = pg.pixel(x, y)
        return (int(r), int(g), int(b))
    except Exception:
        return None

def _color_matches(c1, c2) -> bool:
    return (c1 is not None) and (c1[0] == c2[0] and c1[1] == c2[1] and c1[2] == c2[2])

def _color_close(c1, c2, tol=0):
    if c1 is None: return False
    return (abs(c1[0]-c2[0]) <= tol and abs(c1[1]-c2[1]) <= tol and abs(c1[2]-c2[2]) <= tol)

def _pixel_differs_from_ref(pos_xy, ref_rgb, tol):
    col = _get_pixel_rgb(pos_xy[0], pos_xy[1])
    return not _color_close(col, ref_rgb, tol)

# ========== MONKEYPATCH GUARDS DE PAUSA ==========
try:
    _ORIG_KB_PRESS_AND_RELEASE = keyboard.press_and_release
    def _kb_press_guard(hk):
        if is_hard_paused() or not _is_tibia_active():
            return
        return _ORIG_KB_PRESS_AND_RELEASE(hk)
    keyboard.press_and_release = _kb_press_guard

    _ORIG_MOVE_TO = pg.moveTo
    _ORIG_CLICK   = pg.click
    def _move_to_guard(*args, **kwargs):
        if is_paused() or EXIT_TAKING_CONTROL.is_set():
            return
        return _ORIG_MOVE_TO(*args, **kwargs)
    def _click_guard(*args, **kwargs):
        if is_paused() or EXIT_TAKING_CONTROL.is_set():
            return
        return _ORIG_CLICK(*args, **kwargs)
    pg.moveTo = _move_to_guard
    pg.click  = _click_guard
    pg._RAW_MOVE_TO = _ORIG_MOVE_TO
    pg._RAW_CLICK   = _ORIG_CLICK
    print("[PAUSE] Guards instalados: ratón bloqueado en HOME/END, teclado bloqueado en END.")
except Exception as e:
    print(f"[PAUSE] No se pudo instalar guard global: {e}")

# --------- Sistema de criaturas ---------
def _creature_pos(n: int) -> tuple[int, int]:
    x0, y0 = CREATURE_XY_START
    return (x0, y0 + (n - 1) * CREATURE_ROW_DY)

def _creature_slot_has_color(n: int, rgb: tuple[int,int,int]) -> bool:
    x, y = _creature_pos(n)
    col = _get_pixel_rgb(x, y)
    return _color_matches(col, rgb)

def get_creature_count(max_rows: int = None) -> int:
    if max_rows is None:
        max_rows = CREATURE_MAX_ROWS
    cnt = 0
    for i in range(1, max_rows + 1):
        if _creature_slot_has_color(i, CREATURE_COLOR):
            cnt += 1
        else:
            break
    return cnt

def has_at_least(n: int) -> bool:
    return get_creature_count() >= n

def is_single_creature_low_hp(tol: int = None) -> bool:
    if get_creature_count() != 1:
        return False
    if tol is None:
        tol = CREATURE_DEAD_CHECK_TOL
    col = _get_pixel_rgb(CREATURE_DEAD_CHECK_POS[0], CREATURE_DEAD_CHECK_POS[1])
    return _color_close(col, CREATURE_DEAD_CHECK_RGB, tol)

def parse_min_plus(s: str, default: int = 1) -> int:
    if not s:
        return default
    s = s.strip()
    if s.endswith('+'):
        s = s[:-1]
    try:
        n = int(s)
        return max(1, min(n, CREATURE_MAX_ROWS))
    except Exception:
        return default
    
def parse_min_plus_nullable(s: str):
    """
    Devuelve:
      - int >=1 si hay un valor válido ("1", "2+", etc.)
      - None si está vacío o inválido → para ignorar la magia
    """
    if s is None:
        return None
    s = str(s).strip()
    if not s:
        return None
    if s.endswith('+'):
        s = s[:-1]
    try:
        n = int(s)
        return max(1, min(n, CREATURE_MAX_ROWS))
    except Exception:
        return None


# ===================== HEALING THREADS =====================
_potion_lock = Lock()
_last_potion_ts = 0.0

def _healing_high_worker():
    last_cast = 0.0
    while not _STOP_EVENT.is_set():
        if is_hard_paused() or not _is_tibia_active():
            time.sleep(NOT_ACTIVE_SLEEP); continue
        if HK_HIGH_HEALING and _pixel_differs_from_ref(HIGH_HEAL_POS, HIGH_HEAL_RGB, HEAL_TOLERANCE):
            now = time.monotonic()
            if (now - last_cast) >= HIGH_HEAL_MIN_INTERVAL:
                keyboard.press_and_release(HK_HIGH_HEALING)
                print("[Heal:High] Magia enviada.")
                last_cast = now
        time.sleep(HEAL_POLL_SLEEP)

def _healing_low_worker():
    global _last_potion_ts
    while not _STOP_EVENT.is_set():
        if is_hard_paused() or not _is_tibia_active():
            time.sleep(NOT_ACTIVE_SLEEP); continue
        need_low = HK_LOW_HEALING and _pixel_differs_from_ref(LOW_HEAL_POS, LOW_HEAL_RGB, HEAL_TOLERANCE)
        if need_low:
            now = time.monotonic()
            with _potion_lock:
                if (now - _last_potion_ts) >= POTION_COOLDOWN_S:
                    keyboard.press_and_release(HK_LOW_HEALING)
                    print("[Heal:Low] Poción de VIDA enviada (PRIORIDAD).")
                    _last_potion_ts = now
        time.sleep(HEAL_POLL_SLEEP)

def _healing_mana_worker():
    global _last_potion_ts
    while not _STOP_EVENT.is_set():
        if is_hard_paused() or not _is_tibia_active():
            time.sleep(NOT_ACTIVE_SLEEP); continue
        if not HK_MANA_POTION:
            time.sleep(0.2); continue
        low_needed_now = HK_LOW_HEALING and _pixel_differs_from_ref(LOW_HEAL_POS, LOW_HEAL_RGB, HEAL_TOLERANCE)
        if low_needed_now:
            time.sleep(HEAL_POLL_SLEEP); continue
        need_mana = _pixel_differs_from_ref(MANA_POS, MANA_RGB, HEAL_TOLERANCE)
        if need_mana:
            now = time.monotonic()
            with _potion_lock:
                low_needed_now_lock = HK_LOW_HEALING and _pixel_differs_from_ref(LOW_HEAL_POS, LOW_HEAL_RGB, HEAL_TOLERANCE)
                if low_needed_now_lock:
                    pass
                elif (now - _last_potion_ts) >= POTION_COOLDOWN_S:
                    keyboard.press_and_release(HK_MANA_POTION)
                    print("[Heal:Mana] Poción de MANA enviada.")
                    _last_potion_ts = now
        time.sleep(HEAL_POLL_SLEEP)

# ========================= SUPPORT =========================
def _image_visible_in_rect(img_path, rect_x1y1x2y2, confidence=0.85) -> bool:
    try:
        region = _rect_to_region_xywh(*rect_x1y1x2y2)
        box = pg.locateOnScreen(img_path, region=region, confidence=confidence)
        return box is not None
    except Exception:
        return False

def _boost_pixel_ok():
    col = _get_pixel_rgb(BOOST_COLOR_POS[0], BOOST_COLOR_POS[1])
    if col is None:
        return False
    if not _color_close(col, BOOST_COLOR_RGB, BOOST_COLOR_TOL):
        return False
    r, g, b = col
    h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
    hue_deg = h * 360.0
    if not (BOOST_HUE_MIN_DEG <= hue_deg <= BOOST_HUE_MAX_DEG): return False
    if s < BOOST_MIN_S or v < BOOST_MIN_V: return False
    return True

def can_cast_boost(now: float, last_support_cast_ts: float, verbose: bool = True) -> bool:
    if not HK_BOOST:
        if verbose: print("[Boost] HK vacío."); return False
    if (now - last_support_cast_ts) < SUPPORT_COOLDOWN:
        if verbose: print("[Boost] Cooldown."); return False
    icon_visible = _image_visible_in_rect(UTITOOON_IMG_PATH, PARALYZEBAR_RECT_X1Y1X2Y2, UTITOOON_CONFIDENCE)
    if icon_visible:
        if verbose: print("[Boost] Buff activo."); return False
    if BOOST_REQUIRE_PIXEL and not _boost_pixel_ok():
        if verbose: print("[Boost] Pixel/umbral no cumple."); return False
    return True

def _cast_support(spell: str, now: float, sup_last_cast: float,
                  res_next_ts: float, ampres_next_ts: float):
    s = spell.lower().strip()
    if s == "boost" and HK_BOOST:
        if can_cast_boost(now, sup_last_cast):
            keyboard.press_and_release(HK_BOOST)
            print("[Support] Boost")
            sup_last_cast = now
            return True, sup_last_cast, res_next_ts, ampres_next_ts
        return False, sup_last_cast, res_next_ts, ampres_next_ts
    if s == "res" and HK_EXETARES:
        if (now - sup_last_cast) >= SUPPORT_COOLDOWN and now >= res_next_ts:
            keyboard.press_and_release(HK_EXETARES)
            print("[Support] Exeta Res")
            sup_last_cast = now
            res_next_ts   = now + EXETARES_PERIOD_S
            return True, sup_last_cast, res_next_ts, ampres_next_ts
        return False, sup_last_cast, res_next_ts, ampres_next_ts
    if s == "ampres" and HK_EXETAAMPRES:
        if (now - sup_last_cast) >= SUPPORT_COOLDOWN and now >= ampres_next_ts:
            keyboard.press_and_release(HK_EXETAAMPRES)
            print("[Support] Exeta Amp Res")
            sup_last_cast  = now
            ampres_next_ts = now + EXETAAMPRES_PERIOD_S
            return True, sup_last_cast, res_next_ts, ampres_next_ts
        return False, sup_last_cast, res_next_ts, ampres_next_ts
    return False, sup_last_cast, res_next_ts, ampres_next_ts

# ========================= COMBATE =========================
def _is_red_combined(rgb_tuple):
    if rgb_tuple is None: return False
    r, g, b = rgb_tuple[:3]
    rgb_dom = (r >= 150) and (r - max(g, b) >= 45)
    h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
    hue_deg = h * 360.0
    hsv_ok  = ((hue_deg <= 18.0 or hue_deg >= 342.0) and s >= 0.50 and v >= 0.30)
    return rgb_dom or hsv_ok

def battlelist_has_red_stripe() -> bool:
    try:
        region = _rect_to_region_xywh(*BATTLELIST_RECT_X1Y1X2Y2)
        img = pg.screenshot(region=region)
        px = img.load()
        w, h = img.size
        for y in range(0, h, ROW_SCAN_STEP):
            run = 0
            for x in range(0, w, RED_SAMPLE_STEP):
                if _is_red_combined(px[x, y]):
                    run += 1
                    if run >= RUN_MIN_SAMPLES:
                        return True
                else:
                    run = 0
        now = time.monotonic()
        if not hasattr(battlelist_has_red_stripe, "_last_dbg"):
            battlelist_has_red_stripe._last_dbg = 0.0
        if now - battlelist_has_red_stripe._last_dbg >= BATTLELIST_DEBUG_COOLDOWN:
            print(f"[BL Debug] sin racha >= {RUN_MIN_SAMPLES}")
            battlelist_has_red_stripe._last_dbg = now
        return False
    except Exception:
        return False

RED_COUNT_MIN = 30

def battlelist_has_red_count() -> bool:
    try:
        region = _rect_to_region_xywh(*BATTLELIST_RECT_X1Y1X2Y2)
        img = pg.screenshot(region=region)
        px = img.load()
        w, h = img.size
        cnt = 0
        for y in range(0, h, ROW_SCAN_STEP):
            for x in range(0, w, RED_SAMPLE_STEP):
                if _is_red_combined(px[x, y]):
                    cnt += 1
                    if cnt >= RED_COUNT_MIN:
                        return True
        return False
    except Exception:
        return False

def battlelist_maybe_has_enemies() -> bool:
    if battlelist_has_red_stripe(): return True
    if battlelist_has_red_count():  return True
    return has_at_least(1)

def battlelist_engaged_now() -> bool:
    try:
        if battlelist_has_red_stripe(): return True
        if battlelist_has_red_count():  return True
    except Exception:
        pass
    return False

def engage_until_no_creatures():
    last_log = 0.0

        # --- ROTACIÓN DE ATAQUE (ignora magias con N+ vacío) ---
    attack_rotation_raw = [
        (HK_EXORI_GRAN, parse_min_plus_nullable(USE_EXORIGRAN_MIN_PLUS)),
        (HK_EXORI,      parse_min_plus_nullable(USE_EXORI_MIN_PLUS)),
        (HK_EXORI_MAS,  parse_min_plus_nullable(USE_EXORIMAS_MIN_PLUS)),
        (HK_EXORI_HUR,  parse_min_plus_nullable(USE_EXORIHUR_MIN_PLUS)),
        (HK_EXORI_ICO,  parse_min_plus_nullable(USE_EXORICO_MIN_PLUS)),
    ]
    # Incluye solo las que tengan hotkey y umbral definido
    attack_rotation = [(hk, nplus) for (hk, nplus) in attack_rotation_raw if hk and (nplus is not None)]

    if not attack_rotation:
        print("[Magic] Rotación VACÍA (no hay hotkeys de ataque configuradas o N+ vacíos).")


    atk_idx   = 0
    atk_last  = 0.0
    start_ts  = time.monotonic()
    atk_ready = False

    has_res    = bool(HK_EXETARES)
    has_boost  = bool(HK_BOOST)
    has_ampres = bool(HK_EXETAAMPRES)

    support_order = [s for s in SUPPORT_ROTATION if s in ("boost", "res", "ampres")]
    if not has_boost:  support_order = [s for s in support_order if s != "boost"]
    if not has_res:    support_order = [s for s in support_order if s != "res"]
    if not has_ampres: support_order = [s for s in support_order if s != "ampres"]

    sup_last_cast  = 0.0
    sup_ready      = False
    sup_start_ts   = start_ts
    res_next_ts    = 0.0
    ampres_next_ts = 0.0

    last_target_ts = 0.0
    last_red = battlelist_has_red_stripe()

    # Loot entre kills por *caída de conteo*
    prev_creatures = None
    did_kill_loot_this_tick = False

    # IGNORE ≤ N
    try:
        _ign_at_most = int(IGNORE_CREATURES_AT_MOST) if str(IGNORE_CREATURES_AT_MOST).strip() else None
    except Exception:
        _ign_at_most = None

    while True:
        if is_paused():
            time.sleep(LOOP_SLEEP_S); continue
        if not _is_tibia_active():
            time.sleep(NOT_ACTIVE_SLEEP); continue

        creatures_now = get_creature_count()
        if creatures_now < 1:
            return

        # ---------- LOOT + RETARGET al detectar KILL (conteo ↓) ----------
        did_kill_loot_this_tick = False
        if prev_creatures is not None and creatures_now < prev_creatures:
            if "x" not in str(LOOT_AFTER_KILL_MODE).lower():
                time.sleep(0.08)
                if HK_LOOT:
                    print("[Loot] Kill detectada (conteo ↓) → looteando…")
                    _do_loot()
                    did_kill_loot_this_tick = True
                    deadline = time.monotonic() + LOOT_BETWEEN_KILLS_DELAY
                    while time.monotonic() < deadline:
                        if is_paused() or not _is_tibia_active(): break
                        time.sleep(0.02)
                if HK_TARGET:
                    keyboard.press_and_release(HK_TARGET)
                    print(f"[Target] Retarget por conteo: {prev_creatures}→{creatures_now} (HK='{HK_TARGET}')")

        # ---------- IGNORE ≤ N (sale del combate) ----------
        if _ign_at_most is not None and creatures_now <= _ign_at_most:
            if creatures_now == 1 and is_single_creature_low_hp():
                print("[Creature] 1 criatura casi muerta → rematar (no ignorar)…")
            else:
                print(f"[Creature] {creatures_now} ≤ {_ign_at_most}: ignorar (loot si aplica) y salir de combate…")
                if HK_LOOT and not did_kill_loot_this_tick:
                    _do_loot()
                return

        now = time.monotonic()
        if now - last_log >= CREATURE_LOG_COOLDOWN:
            print(f"[Creature] Detectadas: {creatures_now}")
            last_log = now

        # -------- Soporte (boost/res/ampres) con su propio cooldown --------
        if not sup_ready and (now - sup_start_ts >= SUPPORT_START_DELAY):
            sup_ready = True

        if sup_ready and support_order:
            for spell in support_order:
                did, sup_last_cast, res_next_ts, ampres_next_ts = _cast_support(
                    spell, now, sup_last_cast, res_next_ts, ampres_next_ts
                )
                if did: break

        # -------- Targeting: SOLO cuando no hay franja roja --------
        red_now = battlelist_has_red_stripe()
        if not red_now and HK_TARGET and (now - last_target_ts) >= TARGET_RETRY_SLEEP:
            keyboard.press_and_release(HK_TARGET)
            print(f"[Target] Insistiendo HK_TARGET='{HK_TARGET}' (cond: no red)")
            last_target_ts = now

        # -------- ATAQUE: start delay + cooldown, con diagnósticos --------
        if not atk_ready:
            if (now - start_ts) >= SPELL_ROTATION_START_DELAY:
                atk_ready = True
            elif (now - start_ts) > (SPELL_ROTATION_START_DELAY + 0.5):
                pass

        if atk_ready and attack_rotation:
            remain = SPELL_ROTATION_COOLDOWN - (now - atk_last)
            if remain <= 0.0:
                key, minreq = attack_rotation[atk_idx]
                creatures_now = get_creature_count()  # refresco antes de decidir
                if creatures_now >= minreq:
                    rep = max(1, int(ATTACK_PRESS_REPEAT))
                    for i in range(rep):
                        keyboard.press_and_release(key)
                        if i + 1 < rep:
                            time.sleep(max(0.0, float(ATTACK_PRESS_INTERVAL)))
                    print(f"[Magic] Rotación: {key} (min {minreq}+, hay {creatures_now})")
                    atk_last = time.monotonic()
                else:
                    print(f"[Magic] Saltado {key}: requiere {minreq}+ y hay {creatures_now}")
                    atk_last = time.monotonic()
                atk_idx  = (atk_idx + 1) % len(attack_rotation)

        # -------- Loot alternativo por franja apagada --------
        if ("x" not in str(LOOT_AFTER_KILL_MODE).lower()) and last_red and not red_now and not did_kill_loot_this_tick:
            if HK_LOOT:
                print("[Loot] Criatura eliminada (franja OFF) → looteando…")
                _do_loot()
                deadline = time.monotonic() + LOOT_BETWEEN_KILLS_DELAY
                while time.monotonic() < deadline:
                    if is_paused() or not _is_tibia_active(): break
                    time.sleep(0.02)

        last_red = red_now
        prev_creatures = creatures_now
        time.sleep(CREATURE_POLL_SLEEP)


# ---------- Combate ESTRICTO (NO respeta IGNORE ≤ N) ----------
def engage_until_no_creatures_strict():
    """Mata todo, sin salir por IGNORE_CREATURES_AT_MOST."""
    last_log = 0.0

        # --- ROTACIÓN DE ATAQUE (ignora magias con N+ vacío) ---
    attack_rotation_raw = [
        (HK_EXORI_GRAN, parse_min_plus_nullable(USE_EXORIGRAN_MIN_PLUS)),
        (HK_EXORI,      parse_min_plus_nullable(USE_EXORI_MIN_PLUS)),
        (HK_EXORI_MAS,  parse_min_plus_nullable(USE_EXORIMAS_MIN_PLUS)),
        (HK_EXORI_HUR,  parse_min_plus_nullable(USE_EXORIHUR_MIN_PLUS)),
        (HK_EXORI_ICO,  parse_min_plus_nullable(USE_EXORICO_MIN_PLUS)),
    ]
    attack_rotation = [(hk, nplus) for (hk, nplus) in attack_rotation_raw if hk and (nplus is not None)]
    atk_idx   = 0
    atk_last  = 0.0
    start_ts  = time.monotonic()
    atk_ready = False

    has_res    = bool(HK_EXETARES)
    has_boost  = bool(HK_BOOST)
    has_ampres = bool(HK_EXETAAMPRES)
    support_order = [s for s in SUPPORT_ROTATION if s in ("boost", "res", "ampres")]
    if not has_boost:  support_order = [s for s in support_order if s != "boost"]
    if not has_res:    support_order = [s for s in support_order if s != "res"]
    if not has_ampres: support_order = [s for s in support_order if s != "ampres"]
    sup_last_cast  = 0.0
    sup_start_ts   = start_ts
    res_next_ts    = 0.0
    ampres_next_ts = 0.0
    last_target_ts = 0.0
    last_red = battlelist_has_red_stripe()

    while True:
        if is_paused():
            time.sleep(LOOP_SLEEP_S); continue
        if not _is_tibia_active():
            time.sleep(NOT_ACTIVE_SLEEP); continue

        creatures_now = get_creature_count()
        if creatures_now < 1:
            return

        now = time.monotonic()
        if now - last_log >= CREATURE_LOG_COOLDOWN:
            print(f"[Creature] (STRICT) Detectadas: {creatures_now}")
            last_log = now

        # Soporte
        if (now - sup_start_ts) >= SUPPORT_START_DELAY and support_order:
            for spell in support_order:
                did, sup_last_cast, res_next_ts, ampres_next_ts = _cast_support(
                    spell, now, sup_last_cast, res_next_ts, ampres_next_ts
                )
                if did: break

        red_now = battlelist_has_red_stripe()

        # Retarget agresivo cuando no hay franja
        if not red_now and HK_TARGET and (now - last_target_ts) >= TARGET_RETRY_SLEEP:
            keyboard.press_and_release(HK_TARGET)
            print(f"[Target] (STRICT) HK_TARGET='{HK_TARGET}'")
            last_target_ts = now

        # Rotación de spells (misma idea que tuya)
        if not atk_ready and (now - start_ts >= SPELL_ROTATION_START_DELAY):
            atk_ready = True
        if atk_ready and attack_rotation and (now - atk_last) >= SPELL_ROTATION_COOLDOWN:
            key, minreq = attack_rotation[atk_idx]
            creatures_now = get_creature_count()
            if creatures_now >= minreq:
                rep = max(1, int(ATTACK_PRESS_REPEAT))
                for i in range(rep):
                    keyboard.press_and_release(key)
                    if i + 1 < rep:
                        time.sleep(max(0.0, float(ATTACK_PRESS_INTERVAL)))
                print(f"[Magic] (STRICT) {key} (min {minreq}+, hay {creatures_now})")
                atk_last = now
            else:
                atk_last = now
            atk_idx  = (atk_idx + 1) % len(attack_rotation)

        last_red = red_now
        time.sleep(CREATURE_POLL_SLEEP)

# ------------- Helpers healing/exit -------------
_heal_stable_since_ts = 0.0

def _healing_need_flags():
    need_high = bool(HK_HIGH_HEALING) and _pixel_differs_from_ref(HIGH_HEAL_POS, HIGH_HEAL_RGB, HEAL_TOLERANCE)
    need_low  = bool(HK_LOW_HEALING)  and _pixel_differs_from_ref(LOW_HEAL_POS,  LOW_HEAL_RGB,  HEAL_TOLERANCE)
    need_mana = _pixel_differs_from_ref(MANA_POS, MANA_RGB, HEAL_TOLERANCE)
    return (need_high, need_low, need_mana)

def _healing_is_stable(min_hold: float = HEAL_STABLE_HOLD_S) -> bool:
    global _heal_stable_since_ts
    need_high, need_low, need_mana = _healing_need_flags()
    if need_high or need_low or need_mana:
        _heal_stable_since_ts = 0.0
        return False
    now = time.monotonic()
    if _heal_stable_since_ts == 0.0:
        _heal_stable_since_ts = now
        return False
    return (now - _heal_stable_since_ts) >= float(min_hold)

def _exit_trigger_visible() -> bool:
    """Devuelve True si la imagen de potions está presente en su región."""
    try:
        saw = False
        if str(CHECK_MANA_ON).lower() == "x" and POTION_CHECK_MANA_IMG:
            mana_img = POTION_CHECK_MANA_IMG if "/" in POTION_CHECK_MANA_IMG else f"img/{POTION_CHECK_MANA_IMG}"
            region = _rect_to_region_xywh(*EXIT_REGION_MANA_X1Y1X2Y2)
            pt = pg.locateCenterOnScreen(mana_img, region=region, confidence=EXIT_CONFIDENCE_POTION)
            saw = saw or (pt is not None)
        if str(CHECK_HEALTH_ON).lower() == "x" and POTION_CHECK_HEALTH_IMG:
            health_img = POTION_CHECK_HEALTH_IMG if "/" in POTION_CHECK_HEALTH_IMG else f"img/{POTION_CHECK_HEALTH_IMG}"
            region = _rect_to_region_xywh(*EXIT_REGION_HEALTH_X1Y1X2Y2)
            pt = pg.locateCenterOnScreen(health_img, region=region, confidence=EXIT_CONFIDENCE_POTION)
            saw = saw or (pt is not None)
        return saw
    except Exception as e:
        print(f"[ExitSync] Error buscando potiones: {e}")
        return False

# ============= EXIT: flujo completo SAFE (kill→loot→heal→exit) =============
def _exit_single_pass_if_trigger() -> bool:
    """
    - Si NO hay trigger, retorna False (no hace nada).
    - Si hay trigger:
        1) Si hay criaturas → combate ESTRICTO hasta 0.
        2) Loot.
        3) Esperar a que el healing esté estable (HEAL_STABLE_HOLD_S).
        4) Abrir menú y hacer EXIT (click).
    - Retorna True si ejecutó la secuencia de EXIT.
    """
    if not _exit_trigger_visible():
        return False

    print("[ExitSync] Trigger de EXIT visible. Preparando salida segura…")

    # 1) Matar TODO si aún hay criaturas (sin ignore ≤ N)
    if battlelist_maybe_has_enemies() or get_creature_count() > 0:
        print("[ExitSync] Aún hay criaturas → combate estricto hasta limpiar…")
        engage_until_no_creatures_strict()

    # 2) Loot post-combate
    if HK_LOOT:
        print("[ExitSync] Loot post-combate…")
        _do_loot()
        # pequeña ventana de animaciones
        deadline = time.monotonic() + LOOT_BETWEEN_KILLS_DELAY
        while time.monotonic() < deadline and _is_tibia_active() and not is_paused():
            time.sleep(0.02)

    # 3) Esperar healing estable
    print("[ExitSync] Esperando healing estable…")
    heal_start_deadline = time.monotonic() + 8.0  # seguridad (opcional)
    while not _healing_is_stable() and _is_tibia_active() and not is_paused():
        if time.monotonic() > heal_start_deadline:
            # no bloquear infinito: si después de 8s no estabiliza, seguimos de todos modos
            print("[ExitSync] Aviso: healing no estabilizó en ventana; continuando con EXIT.")
            break
        time.sleep(0.05)

    # Verificar que el trigger siga (por si se solucionó solo)
    if not _exit_trigger_visible():
        print("[ExitSync] El trigger ya no está visible. Cancelo EXIT.")
        return False

    # 4) Hacer EXIT
    print("[ExitSync] Ejecutando EXIT síncrono.")
    try:
        keyboard.press_and_release("esc")
        time.sleep(0.15)
    except Exception as e:
        print(f"[ExitSync] No pude enviar ESC: {e}")

    EXIT_TAKING_CONTROL.set()
    try:
        try:
            w, _ = pg.size()
            pg._RAW_MOVE_TO(w - 1, 0)
            print(f"[ExitSync] mouse -> top-right ({w-1}, 0)")
            time.sleep(max(0.0, float(EXIT_DELAY_AFTER_MOVE_TOPRIGHT_S)))
            pg._RAW_CLICK()
            print("[ExitSync] click esquina superior derecha")
        except Exception as e:
            print(f"[ExitSync] Fallo en top-right click: {e}")

        time.sleep(max(0.0, float(EXIT_DELAY_BEFORE_EXIT_SEARCH_S)))
        try:
            region_exit = _rect_to_region_xywh(*EXIT_REGION_EXIT_X1Y1X2Y2)
            pos = pg.locateCenterOnScreen(EXIT_IMG_PATH, region=region_exit, confidence=EXIT_CONFIDENCE_EXIT)
        except Exception as e:
            print(f"[ExitSync] Error buscando EXIT: {e}")
            pos = None

        if pos:
            try:
                pg._RAW_MOVE_TO(pos.x, pos.y)
                pg._RAW_CLICK()
                print(f"[ExitSync] EXIT encontrado y clic en ({pos.x}, {pos.y})")
            except Exception as e:
                print(f"[ExitSync] Click EXIT falló: {e}")
        else:
            print("[ExitSync] EXIT no encontrado en región.")

    finally:
        _request_stop()
        EXIT_TAKING_CONTROL.clear()

    return True

# ======================= PERFORM ACTION ====================
def perform_action(action_name: str):
    if not action_name: return
    name = action_name.lower().strip()
    if name == "none":   print("[Action:none] pass."); return
    if name == "ignore": print("[Action:ignore] pass."); return
    if name == "lure":   print("[Action:lure] llegada confirmada."); return
    if name == "zoom":   print("[Action:zoom] manejado en el bloque especial."); return
    if name == "goto":   print("[Action:goto] manejado en el controlador de goto."); return

    if name == "rope":
        do_rope(HK_ROPE, ROPE_ATTEMPTS, ROPE_CAST_DELAY, ROPE_CLICK_DELAY,
                PLAYER_CENTER_SCREEN, _is_tibia_active, is_paused, _STOP_EVENT); return

    if name == "shovel":
        do_shovel(HK_SHOVEL, SHOVEL_ATTEMPTS, SHOVEL_CAST_DELAY, SHOVEL_CLICK_DELAY,
                  PLAYER_CENTER_SCREEN, _is_tibia_active, is_paused, _STOP_EVENT); return

    if name == "stairs":
        do_stairs(PLAYER_CENTER_SCREEN, STAIRS_POST_RIGHT_CLICK_SLEEP,
                  _is_tibia_active, is_paused, _STOP_EVENT); return

    print(f"[Action] Acción desconocida: {action_name}.")

# ===================== OTROS HELPERS =======================
def _do_loot():
    if not HK_LOOT or is_paused():
        return
    do_loot(HK_LOOT, LOOT_REPEAT, LOOT_DELAY)

# ======================= Recentrado estricto ========================
def _recenter_strict_before_action(target_img, search_region, region_center,
                                   strict_tol_px=2, max_tries=8):
    tries = 0
    while tries < max_tries and not is_paused() and _is_tibia_active():
        if battlelist_maybe_has_enemies():
            print("[ActionGuard] Enemigos detectados antes de acción. Combatiendo…")
            engage_until_no_creatures()
            if HK_LOOT:
                print("[ActionGuard] Loot post-combate…")
                _do_loot()

        check = find_center(target_img, search_region, CONFIDENCE)
        if check and is_centered(check, region_center, strict_tol_px):
            print(f"[ActionGuard] Centrado estricto OK (±{strict_tol_px}px).")
            return True

        pt = find_center(target_img, search_region, CONFIDENCE)
        if pt:
            print(f"[ActionGuard] Recentrando (estricto ±{strict_tol_px}px). Intento {tries+1}/{max_tries}")
            click_point(pt)
            time.sleep(SLEEP_AFTER_CLICK)
        else:
            print("[ActionGuard] No veo el WP para recentrar; reintento suave…")
            time.sleep(ATTEMPT_LOOP_IDLE_SLEEP)

        tries += 1

    print(f"[ActionGuard] No se logró centrar estrictamente en {max_tries} intentos.")
    return False

# =========================== MAIN ==========================
def main():
    global SOFT_PAUSED, HARD_PAUSED, PAUSED, last_action_used, retry_same_wp_once

    # ---- Construir tabs/arrays y normalizar ----
    tabs = _build_tabs_from_cfg()
    if not tabs:
        print("[ERROR] No hay tabs/route válidos. Revisa tu configuración.")
        time.sleep(3); sys.exit(1)

    # ---------- Punto de arranque ----------
    # 1) Si existe ROUTE_ATTACH válido: arrancar allí.
    # 2) Si no, SIEMPRE reset al primer tab: 'hunt' si existe; si no, primer nombre alfabético. Índice 0.
    attach = globals().get("ROUTE_ATTACH", {"tab": "", "index": -1})
    attach_tab = str(attach.get("tab", "") or "").strip()
    try:
        attach_idx = int(attach.get("index", -1))
    except Exception:
        attach_idx = -1

    if (attach_tab in tabs):
        r, a, lb, gt = _tab_arrays(tabs, attach_tab)
        if 0 <= attach_idx < len(r):
            current_tab = attach_tab
            wp_index = int(attach_idx)
            print(f"[ROUTE] start tab={current_tab} i={wp_index} (attach)")
        else:
            # attach inválido -> reset
            current_tab = "hunt" if "hunt" in tabs else sorted(tabs.keys())[0]
            wp_index = 0
            print(f"[ROUTE] start tab={current_tab} i={wp_index} (reset)")
    else:
        current_tab = "hunt" if "hunt" in tabs else sorted(tabs.keys())[0]
        wp_index = 0
        print(f"[ROUTE] start tab={current_tab} i={wp_index} (reset)")

    # Verificación de longitudes por tab
    for tname, d in tabs.items():
        r, a, lb, gt = d["route"], d["actions"], d["labels"], d["gotos"]
        if not (len(r) == len(a) == len(lb) == len(gt)):
            print(f"[WARN] Tab '{tname}' con longitudes disparejas. Normalizando.")
            r, a, lb, gt = _pad_arrays(r, a, lb, gt)
            d["route"], d["actions"], d["labels"], d["gotos"] = r, a, lb, gt

    print("[main] Aplicando transparencia una sola vez…")
    run_transparency(
        interval_sec=1.0,
        title_substr=TARGET_WINDOW_PREFIXES,
        active_alpha=1,
        inactive_alpha=1,
        run_once=True
    )
    print("[main] Listo. Continuando…\n")

    # === Healing threads ===
    Thread(target=_healing_high_worker, daemon=True).start()
    Thread(target=_healing_low_worker,  daemon=True).start()
    Thread(target=_healing_mana_worker, daemon=True).start()

    # === Food thread ===
    Thread(
        target=run_food_worker,
        kwargs=dict(
            hotkey=HK_FOOD,
            interval_s=EAT_EVERY_S,
            presses=EAT_PRESSES,
            press_delay_s=EAT_PRESS_DELAY_S,
            jitter_s=EAT_JITTER_S,
            is_active=_is_tibia_active,
            stop_event=_STOP_EVENT,
        ),
        daemon=True
    ).start()

    # === Anti-Paralyze ===
    if HK_REMOVE_PARALYZE:
        Thread(
            target=run_antiparalyze,
            kwargs=dict(
                region=PARALYZEBAR_RECT_X1Y1X2Y2,
                image_path=PARALYZE_IMG_PATH,
                hotkey=HK_REMOVE_PARALYZE,
                confidence=PARALYZE_CONFIDENCE,
                poll_sleep=PARALYZE_POLL_SLEEP,
                press_cooldown=PARALYZE_PRESS_COOLDOWN,
                active_window_prefixes=TARGET_WINDOW_PREFIXES,
            ),
            daemon=True
        ).start()

    # === Amulet / Ring watchers ===
    if HK_AMULET:
        Thread(
            target=run_amulet_watcher,
            kwargs=dict(
                hotkey=HK_AMULET,
                poll_sleep=AMULET_POLL_SLEEP,
                press_cooldown=AMULET_PRESS_COOLDOWN,
                is_active=_is_tibia_active,
                stop_event=_STOP_EVENT,
                image_path=globals().get("AMULET_IMG_PATH", "./img/emptyamulet.png"),
                region=globals().get("AMULET_REGION_X1Y1X2Y2", (1745,148,1860,282)),
                confidence=globals().get("AMULET_CONFIDENCE", 0.87),
            ),
            daemon=True
        ).start()

    if HK_RING:
        Thread(
            target=run_ring_watcher,
            kwargs=dict(
                hotkey=HK_RING,
                poll_sleep=RING_POLL_SLEEP,
                press_cooldown=RING_PRESS_COOLDOWN,
                is_active=_is_tibia_active,
                stop_event=_STOP_EVENT,
                image_path=globals().get("RING_IMG_PATH", "./img/emptyring.png"),
                region=globals().get("RING_REGION_X1Y1X2Y2", (1745,148,1860,282)),
                confidence=globals().get("RING_CONFIDENCE", 0.87),
            ),
            daemon=True
        ).start()

    # Hotkeys
    if HK_TOGGLE_PAUSE:
        keyboard.add_hotkey(HK_TOGGLE_PAUSE, _toggle_soft_pause, suppress=False)
    keyboard.add_hotkey("end", _toggle_hard_pause, suppress=False)
    if HK_QUIT:
        keyboard.add_hotkey(HK_QUIT, _request_stop, suppress=False)

    print("=== Cavebot Base (ruta por imágenes + acciones + creature-check) ===")
    print(f"- Arranca en PAUSA SUAVE. [{HK_TOGGLE_PAUSE}] Pausa/Run suave, [END] Pausa DURA, [{HK_QUIT}] Salir")
    print("- Solo corre cuando la ventana activa es 'Tibia' / 'Tibia -'.")

    search_region = region_from_center(*PLAYER_CENTER_MINIMAP, half=60)
    region_center = PLAYER_CENTER_MINIMAP

    try:
        while not _STOP_EVENT.is_set():
            if is_paused():
                time.sleep(LOOP_SLEEP_S); continue
            if not _is_tibia_active():
                time.sleep(NOT_ACTIVE_SLEEP); continue

            # Arrays del TAB actual
            route, actions, labels, gotos = _tab_arrays(tabs, current_tab)
            if not route:
                print(f"[Cavebot] Tab '{current_tab}' sin route. Saliendo…")
                break
            CURR_WP_IMGS = [f"./marcas/{name}.png" for name in route]
            # Wrap protección por si cambió de tamaño entre iteraciones
            if wp_index >= len(route):
                wp_index = 0

            action_for_wp = str(actions[wp_index]).lower().strip()
            target_img    = CURR_WP_IMGS[wp_index]

            # ---- Feedback estándar para resaltar en GUI ----
            try:
                wp_name = (route[wp_index] or f"wp{wp_index+1}")
            except Exception:
                wp_name = f"wp{wp_index+1}"
            GUI_ROUTE_LOG(current_tab, wp_index, name=wp_name, action=action_for_wp, phase="before")
            print(f"[ROUTE] tab={current_tab} idx={wp_index} name={wp_name} action={action_for_wp} phase=before")


            print(f"[Cavebot] TAB={current_tab}  idx={wp_index+1}/{len(route)}  Objetivo: {target_img} | Acción: {action_for_wp}")

            # ======= EXIT antes de movernos al WP =======
            if _exit_single_pass_if_trigger():
                break

            # ======= GOTO inmediato (sin buscar imagen) =======
            if action_for_wp == "goto":
                spec = (gotos[wp_index] if wp_index < len(gotos) else "").strip()
                if ":" in spec:
                    dst_tab, dst_label = [s.strip() for s in spec.split(":", 1)]
                    if dst_tab in tabs:
                        d_route, d_actions, d_labels, d_gotos = _tab_arrays(tabs, dst_tab)
                        lab_idx = _label_index(d_labels, d_route)
                        if d_route and (dst_label in lab_idx):
                            new_idx = lab_idx[dst_label]
                            print(f"[GOTO] {current_tab}[{wp_index}] → {dst_tab}:{dst_label} (idx={new_idx})")
                            current_tab = dst_tab
                            wp_index = new_idx
                            GUI_ROUTE_LOG(current_tab, wp_index, phase="goto")
                            print(f"[ROUTE] tab={current_tab} idx={wp_index} phase=goto")
                            last_action_used = "goto"
                            retry_same_wp_once = False
                            continue
                        else:
                            print(f"[GOTO] Etiqueta '{dst_label}' no encontrada en tab '{dst_tab}'. Avanzo al siguiente WP.")
                    else:
                        print(f"[GOTO] Tab destino '{dst_tab}' no existe. Avanzo al siguiente WP.")
                else:
                    print("[GOTO] Especificación vacía/incorrecta. Formato: tab:etiqueta — avanzo al siguiente WP.")

                wp_index = (wp_index + 1) % len(route)
                time.sleep(WAIT_BEFORE_NEXT_WP_S)
                continue

            # --- CASO ESPECIAL: 'zoom' ---
            if action_for_wp == "zoom":
                print(f"[Cavebot] Acción 'zoom' para {target_img}. Buscaré en ZOOM_RECT_X1Y1X2Y2.")
                did_zoom = False
                for attempt in range(1, MAX_TRIES_PER_WP + 1):
                    if is_paused() or not _is_tibia_active():
                        time.sleep(LOOP_SLEEP_S); continue
                    did_zoom = do_zoom_click(
                        target_img_path=target_img,
                        region_rect_x1y1x2y2=ZOOM_RECT_X1Y1X2Y2,
                        confidence=ZOOM_CONFIDENCE,
                        click_delay_s=ZOOM_CLICK_DELAY
                    )
                    if did_zoom:
                        print(f"[Cavebot] Zoom OK ({target_img}) en intento {attempt}.")
                        break
                    time.sleep(ATTEMPT_LOOP_IDLE_SLEEP)

                last_action_used = "zoom"
                print(f"[Cavebot] {'Zoom OK' if did_zoom else 'Zoom no encontrado'} → siguiente WP.")
                if _exit_single_pass_if_trigger():
                    break
                wp_index = (wp_index + 1) % len(route)
                time.sleep(WAIT_BEFORE_NEXT_WP_S)
                continue

            movement_action = "lure" if last_action_used == "lure" else "none"
            tries_for_this_wp = (LURE_MAX_TRIES if movement_action == "lure" else MAX_TRIES_PER_WP)

            arrived = False
            not_visible_streak = 0
            skipped_due_to_not_visible = False

            for attempt in range(1, tries_for_this_wp + 1):
                if is_paused():
                    time.sleep(LOOP_SLEEP_S); continue
                if not _is_tibia_active():
                    time.sleep(NOT_ACTIVE_SLEEP); continue

                enemies_now = battlelist_maybe_has_enemies()
                if "x" not in str(ATTACK_UNTIL_ARRIVED_MODE).lower():
                    if enemies_now:
                        print("[Cavebot] Enemigos detectados en ruta. Combatiendo…")
                        engage_until_no_creatures()
                        if HK_LOOT:
                            print("[Loot] Ejecutando loot…")
                            _do_loot()
                        time.sleep(0.10)

                pt = find_center(target_img, search_region, CONFIDENCE)

                if pt is None:
                    not_visible_streak += 1
                    print(f"[Cavebot] Intento {attempt}: no veo {target_img} (streak={not_visible_streak}).")
                    if str(SKIP_IF_NOT_VISIBLE).lower() == "x" and not_visible_streak >= int(SKIP_NOT_VISIBLE_AFTER):
                        print(f"[Cavebot] Skip temprano: {target_img} no visible → siguiente WP.")
                        skipped_due_to_not_visible = True
                        break
                    time.sleep(ATTEMPT_LOOP_IDLE_SLEEP)
                    continue
                else:
                    not_visible_streak = 0

                if movement_action == "lure":
                    print(f"[Cavebot] Click → corre {LURE_PAUSE_SEC:.2f}s → ESC → espera {LURE_RESUME_SEC:.2f}s → verificar centrado.")
                    click_point(pt)
                    time.sleep(LURE_PAUSE_SEC)
                    keyboard.press_and_release(LURE_PAUSE_KEY)
                    time.sleep(LURE_RESUME_SEC)
                    check = find_center(target_img, search_region, CONFIDENCE)
                    tol = LURE_CENTER_TOLERANCE_PX
                    if check and is_centered(check, region_center, tol):
                        print(f"[Cavebot] LLEGADA (LURE) confirmada (±{tol}px).")
                        # --- AÑADE ESTO ---
                        GUI_ROUTE_LOG(current_tab, wp_index, name=wp_name, action=action_for_wp, phase="arrived")
                        print(f"[ROUTE] tab={current_tab} idx={wp_index} name={wp_name} phase=arrived")
                        # -------------------
                        arrived = True
                        break
                    else:
                        print(f"[Cavebot] Aún no centrado (±{tol}px), reintento...")
                else:
                    print(f"[Cavebot] Click → espera {SLEEP_AFTER_CLICK:.2f}s → verificar centrado.")
                    click_point(pt)
                    time.sleep(SLEEP_AFTER_CLICK)
                    check = find_center(target_img, search_region, CONFIDENCE)
                    tol = CENTER_TOLERANCE_PX
                    if check and is_centered(check, region_center, tol):
                        print(f"[Cavebot] LLEGADA confirmada (±{tol}px).")
                        # --- AÑADE ESTO ---
                        GUI_ROUTE_LOG(current_tab, wp_index, name=wp_name, action=action_for_wp, phase="arrived")
                        print(f"[ROUTE] tab={current_tab} idx={wp_index} name={wp_name} phase=arrived")
                        # -------------------
                        arrived = True
                        break
                    else:
                        print(f"[Cavebot] Aún no centrado (±{tol}px), reintento...")

                time.sleep(ATTEMPT_LOOP_IDLE_SLEEP)

            if arrived:
                if action_for_wp not in ("lure", "ignore"):
                    engage_until_no_creatures()
                    if HK_LOOT:
                        print("[Loot] Ejecutando loot…")
                        _do_loot()
                else:
                    print("[Creature] Acción es 'lure' o 'ignore': no se revisa criatura ni se hace loot.")

                print(f"[Cavebot] Esperando {WAIT_AFTER_ARRIVAL_S:.2f}s tras combate/loot…")
                time.sleep(WAIT_AFTER_ARRIVAL_S)

                # Chequeo EXIT post-actividad
                if _exit_single_pass_if_trigger():
                    break

                if str(dropvials).lower() == "x":
                    drop_vials(
                        center_xy=PLAYER_CENTER_SCREEN,
                        is_active=_is_tibia_active,
                        is_paused=is_paused,
                        stop_event=_STOP_EVENT,
                    )

                if action_for_wp in ("rope", "shovel", "stairs"):
                    print("[Cavebot] Acción delicada: verificando centrado estricto…")
                    ok_center = _recenter_strict_before_action(
                        target_img=target_img,
                        search_region=search_region,
                        region_center=region_center,
                        strict_tol_px=LURE_CENTER_TOLERANCE_PX,
                        max_tries=8
                    )
                    if not ok_center:
                        print("[Cavebot] No centrado estricto. No ejecuto la acción y reintento este WP.")
                        continue

                print(f"[Cavebot] Ejecutando acción: {action_for_wp}")
                perform_action(action_for_wp)
                last_action_used = action_for_wp

                print(f"[Cavebot] Esperando {WAIT_BEFORE_NEXT_WP_S:.2f}s antes de avanzar al siguiente WP…")
                time.sleep(WAIT_BEFORE_NEXT_WP_S)

                # EXTRA: chequeo EXIT justo antes de avanzar
                if _exit_single_pass_if_trigger():
                    break

            else:
                if skipped_due_to_not_visible:
                    print("[Cavebot] Skip por no visible: avanzar al siguiente WP.")
                    if _exit_single_pass_if_trigger():
                        break
                    retry_same_wp_once = False
                    wp_index = (wp_index + 1) % len(route)
                    time.sleep(WAIT_BEFORE_NEXT_WP_S)
                    continue

                print(f"[Cavebot] No pude centrar {target_img} en {tries_for_this_wp} intentos.")
                engaged = False

                if battlelist_maybe_has_enemies():
                    print("[Cavebot] Enemigos detectados. Combatiendo…")
                    engage_until_no_creatures()
                    engaged = True
                else:
                    TARGET_PRIME_TIMEOUT_S = 2.0
                    prime_deadline = time.monotonic() + TARGET_PRIME_TIMEOUT_S
                    last_prime_ts = 0.0
                    print(f"[Cavebot] Prime loop {TARGET_PRIME_TIMEOUT_S:.1f}s con HK_TARGET…")
                    while time.monotonic() < prime_deadline and not is_paused() and _is_tibia_active():
                        now = time.monotonic()
                        if HK_TARGET and (now - last_prime_ts) >= TARGET_RETRY_SLEEP:
                            keyboard.press_and_release(HK_TARGET)
                            last_prime_ts = now
                        if battlelist_maybe_has_enemies():
                            print("[Cavebot] Enemigos durante prime → combate…")
                            engage_until_no_creatures()
                            engaged = True
                            break
                        time.sleep(ATTEMPT_LOOP_IDLE_SLEEP)

                if engaged:
                    if action_for_wp != "lure" and HK_LOOT:
                        print("[Loot] Ejecutando loot…")
                        _do_loot()
                    print(f"[Cavebot] Combate terminado. Esperando {WAIT_BEFORE_NEXT_WP_S:.2f}s…")
                    time.sleep(WAIT_BEFORE_NEXT_WP_S)
                    if _exit_single_pass_if_trigger():
                        break
                else:
                    print("[Cavebot] Sin criaturas tras prime. Avanzando…")
                    print(f"[Cavebot] Esperando {WAIT_BEFORE_NEXT_WP_S:.2f}s…")
                    time.sleep(WAIT_BEFORE_NEXT_WP_S)
                    if _exit_single_pass_if_trigger():
                        break

            if arrived:
                retry_same_wp_once = False
                wp_index = (wp_index + 1) % len(route)
            else:
                if RETRY_SAME_WP_ONLY_IF_COMBAT:
                    if not retry_same_wp_once and 'engaged' in locals() and engaged:
                        retry_same_wp_once = True
                        print("[Cavebot] Fallé al llegar PERO hubo combate. Reintento este WP una vez…")
                    else:
                        retry_same_wp_once = False
                        print("[Cavebot] Fallé (sin combate o ya reintentado). Avanzo al siguiente WP.")
                        if _exit_single_pass_if_trigger():
                            break
                        wp_index = (wp_index + 1) % len(route)
                else:
                    if not retry_same_wp_once:
                        retry_same_wp_once = True
                        print("[Cavebot] Fallé al llegar. Reintentaré este WP una vez…")
                    else:
                        retry_same_wp_once = False
                        print("[Cavebot] Fallé tras reintento. Avanzo al siguiente WP.")
                        if _exit_single_pass_if_trigger():
                            break
                        wp_index = (wp_index + 1) % len(route)

    except KeyboardInterrupt:
        print("\n[STATE] KeyboardInterrupt capturado. Saliendo…")
    finally:
        print("[STATE] Bye.")

# =========================== ENTRY =========================
if __name__ == "__main__":
    main()
