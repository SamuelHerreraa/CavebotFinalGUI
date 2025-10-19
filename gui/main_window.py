# gui/main_window.py
from __future__ import annotations

from pathlib import Path
import sys
import json
import ctypes
from ctypes import wintypes
from typing import Dict, Any
from collections import deque

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTabWidget, QFileDialog, QMessageBox, QGroupBox, QFormLayout, QGridLayout,
    QScrollArea, QTextEdit
)
from PySide6.QtCore import Qt, QTimer, QAbstractNativeEventFilter, QCoreApplication
from PySide6.QtGui import QAction, QKeySequence, QShortcut

from gui.widgets.led import Led
from gui.widgets.log_console import LogConsole
from gui.widgets.regions_panel import RegionsPanel
from gui.widgets.pixels_panel import PixelsPanel
from gui.widgets.hotkeys_panel import HotkeysPanel
from gui.widgets.route_panel import RoutePanel
from gui.widgets.settings_panel import SettingsPanel
from gui.widgets.flags_panel import FlagsPanel

# ----------------- Fallback nativo Windows: RegisterHotKey -----------------
class _WinHotkeyFilter(QAbstractNativeEventFilter):
    """Captura WM_HOTKEY y llama a las callbacks dadas."""
    WM_HOTKEY = 0x0312

    def __init__(self, on_home, on_end, ids_home: tuple[int, ...], ids_end: tuple[int, ...]):
        super().__init__()
        self.on_home = on_home
        self.on_end = on_end
        self.ids_home = set(ids_home or ())
        self.ids_end  = set(ids_end  or ())

    def nativeEventFilter(self, eventType, message):
        if eventType == "windows_generic_MSG":
            try:
                msg = wintypes.MSG.from_address(int(message))
                if msg.message == self.WM_HOTKEY:
                    wid = int(msg.wParam)
                    if wid in self.ids_home:
                        QTimer.singleShot(0, self.on_home)
                        return True, 1
                    if wid in self.ids_end:
                        QTimer.singleShot(0, self.on_end)
                        return True, 1
            except Exception:
                pass
        return False, 0


class MainWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("Cavebot GUI")
        self.resize(820, 500)

        # Atajo: Guardar perfil + actualizar runtime_cfg.py (Ctrl+S)

        # --- Barra de estado para feedback ---
        self.statusBar().showMessage("Listo.")

        # --- Controles superiores ---
        top = QWidget(self)
        top_lay = QHBoxLayout(top)
        top_lay.setContentsMargins(8, 8, 8, 4)
        top_lay.setSpacing(10)

        self.btn_start = QPushButton("Start")
        self.btn_pause = QPushButton("Pause/Resume")
        self.btn_stop  = QPushButton("Stop")
        for b in (self.btn_start, self.btn_pause, self.btn_stop):
            b.setCursor(Qt.PointingHandCursor)
        top_lay.addWidget(self.btn_start)
        top_lay.addWidget(self.btn_pause)
        top_lay.addWidget(self.btn_stop)

        # LEDs (Global, Cavebot, Healing, Food, Anti)
        self.led_global   = Led("Global")
        self.led_cavebot  = Led("Cavebot")
        self.led_healing  = Led("Healing")
        self.led_food     = Led("Food")
        self.led_anti     = Led("Anti")
        for led in (self.led_global, self.led_cavebot, self.led_healing, self.led_food, self.led_anti):
            top_lay.addWidget(led)

        # Tabs
        self.tabs = QTabWidget(self)
        self.tab_general  = QWidget()
        self.tab_logs     = QWidget()

        # Paneles (resto de tabs)
        self.regions_panel  = RegionsPanel(controller=self.controller)
        self.pixels_panel   = PixelsPanel(controller=self.controller)
        self.hotkeys_panel  = HotkeysPanel(controller=self.controller)
        self.route_panel    = RoutePanel(controller=self.controller)
        self.settings_panel = SettingsPanel(controller=self.controller)
        self.flags_panel    = FlagsPanel(controller=self)

        # ================== GENERAL (Dashboard scrollable) ==================
        gen_outer = QVBoxLayout(self.tab_general)
        gen_outer.setContentsMargins(8, 8, 8, 8)
        gen_outer.setSpacing(8)

        # Scroll
        gen_scroll = QScrollArea(self.tab_general)
        gen_scroll.setWidgetResizable(True)
        gen_outer.addWidget(gen_scroll)

        gen_container = QWidget()
        gen_scroll.setWidget(gen_container)
        gen = QVBoxLayout(gen_container)
        gen.setContentsMargins(2, 2, 2, 12)
        gen.setSpacing(10)

        # Estilos de "tarjeta"
        card_css = """
        QGroupBox {
            border: 1px solid #2a2a2a;
            border-radius: 8px;
            margin-top: 12px;
            padding-top: 10px;
            background: rgba(255,255,255,0.02);
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 8px;
            color: #cfe9ff;
            font-weight: 600;
        }
        """

        # RESUMEN
        box_resume = QGroupBox("Resumen")
        box_resume.setStyleSheet(card_css)
        resume_form = QFormLayout(box_resume)
        resume_form.setLabelAlignment(Qt.AlignRight)
        resume_form.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)

        self.lbl_profile = QLabel("—")
        self.lbl_state   = QLabel("—")
        self.lbl_counts  = QLabel("—")
        for w in (self.lbl_profile, self.lbl_state, self.lbl_counts):
            w.setStyleSheet("font-size: 14px; font-weight: 600;")
        resume_form.addRow(QLabel("<b>Perfil:</b>"),  self.lbl_profile)
        resume_form.addRow(QLabel("<b>Estado:</b>"),  self.lbl_state)
        resume_form.addRow(QLabel("<b>Criaturas | Red:</b>"), self.lbl_counts)
        gen.addWidget(box_resume)

        # Dos columnas con Actividad y Perfil actual
        grid = QGridLayout()
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)
        gen.addLayout(grid)

        # ACTIVIDAD
        box_activity = QGroupBox("Actividad actual")
        box_activity.setStyleSheet(card_css)
        act_form = QFormLayout(box_activity)
        act_form.setLabelAlignment(Qt.AlignRight)
        self.g_act_cavebot = QLabel("—")
        self.g_act_healing = QLabel("—")
        self.g_act_food    = QLabel("—")
        self.g_act_anti    = QLabel("—")
        self.g_act_crea    = QLabel("—")
        self.g_act_red     = QLabel("—")
        for lab in (self.g_act_cavebot, self.g_act_healing, self.g_act_food, self.g_act_anti, self.g_act_crea, self.g_act_red):
            lab.setTextInteractionFlags(Qt.TextSelectableByMouse)
            lab.setStyleSheet("font-size: 13px;")
        act_form.addRow("Cavebot:",  self.g_act_cavebot)
        act_form.addRow("Healing:",  self.g_act_healing)
        act_form.addRow("Food:",     self.g_act_food)
        act_form.addRow("Anti:",     self.g_act_anti)
        act_form.addRow("Criaturas:", self.g_act_crea)
        act_form.addRow("Red stripe:", self.g_act_red)
        grid.addWidget(box_activity, 0, 0)

        # PERFIL ACTUAL
        box_profile = QGroupBox("Perfil activo")
        box_profile.setStyleSheet(card_css)
        prof_form = QFormLayout(box_profile)
        prof_form.setLabelAlignment(Qt.AlignRight)

        self.g_prof_attack_route = QLabel("—")
        self.g_prof_loot_kill    = QLabel("—")
        self.g_prof_ignore_n     = QLabel("—")
        self.g_prof_exit         = QLabel("—")
        self.g_prof_exit_imgs    = QLabel("—")
        for lab in (self.g_prof_attack_route, self.g_prof_loot_kill, self.g_prof_ignore_n, self.g_prof_exit, self.g_prof_exit_imgs):
            lab.setTextInteractionFlags(Qt.TextSelectableByMouse)
            lab.setStyleSheet("font-size: 13px;")
        prof_form.addRow("Atacar en ruta:", self.g_prof_attack_route)
        prof_form.addRow("Loot tras kill:", self.g_prof_loot_kill)
        prof_form.addRow("Ignorar ≤ N:",    self.g_prof_ignore_n)
        prof_form.addRow("Exit on pot:",    self.g_prof_exit)
        prof_form.addRow("Imgs (M/H):",     self.g_prof_exit_imgs)
        grid.addWidget(box_profile, 0, 1)

        # ÚLTIMOS eventos
        box_events = QGroupBox("Últimos eventos")
        box_events.setStyleSheet(card_css)
        v_ev = QVBoxLayout(box_events)
        self.g_events = QTextEdit()
        self.g_events.setReadOnly(True)
        self.g_events.setMinimumHeight(140)
        self.g_events.setStyleSheet("font-family: Consolas, 'Fira Code', monospace; font-size: 12px;")
        v_ev.addWidget(self.g_events)
        gen.addWidget(box_events)

        # ------------------ LOGS (pestaña separada) ------------------
        logs_lay = QVBoxLayout(self.tab_logs)
        logs_lay.setContentsMargins(8, 8, 8, 8)
        self.console = LogConsole()
        logs_lay.addWidget(self.console)

        # Añadir tabs
        self.tabs.addTab(self.tab_general,   "General")
        self.tabs.addTab(self.route_panel,   "Ruta & Waypoints")
        self.tabs.addTab(self.hotkeys_panel, "Hotkeys")
        self.tabs.addTab(self.regions_panel, "Regiones")
        self.tabs.addTab(self.pixels_panel,  "Pixeles")
        self.tabs.addTab(self.settings_panel, "Settings")
        self.tabs.addTab(self.flags_panel,   "Flags")
        self.tabs.addTab(self.tab_logs,      "Logs")

        # Estilos
        try:
            self.tabs.tabBar().setStyleSheet("""
                QTabBar::tab { padding: 6px 10px; }
                QTabBar::tab:hover { background: rgba(160,200,255,0.15); }
                QTabBar::tab:selected { background: rgba(0,153,255,0.20); }
            """)
            self.menuBar().setStyleSheet("""
                QMenuBar {
                    background: rgba(30,30,30,0.6);
                    color: #e0f2ff;
                }
                QMenuBar::item {
                    padding: 6px 10px;
                    background: transparent;
                    border-radius: 4px;
                }
                QMenuBar::item:selected {
                    background: rgba(0,153,255,0.25);
                    color: #ffffff;
                }
                QMenu {
                    background: #1e1e1e;
                    color: #e6f1ff;
                    border: 1px solid #2a2a2a;
                }
                QMenu::item {
                    padding: 6px 24px;
                    background: transparent;
                }
                QMenu::item:selected {
                    background: rgba(0,153,255,0.25);
                    color: #ffffff;
                }
                QMenu::separator {
                    height: 1px;
                    background: #2a2a2a;
                    margin: 4px 8px;
                }
            """)
        except Exception:
            pass

        # --------- Menú "File" + atajos ----------
        self._build_menu_bar()

        # Contenedor central
        central = QWidget(self)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(top)
        root.addWidget(self.tabs)
        self.setCentralWidget(central)

        # Señales (botones)
        self.btn_start.clicked.connect(self._on_start)
        self.btn_pause.clicked.connect(self._on_pause)
        self.btn_stop.clicked.connect(self._on_stop)

        # Atajos locales (cuando la ventana tiene foco)
        self.sc_home = QShortcut(QKeySequence(Qt.Key_Home), self)
        self.sc_home.activated.connect(lambda: self._trigger_pause_from("shortcut"))

        self.sc_end = QShortcut(QKeySequence(Qt.Key_End), self)
        self.sc_end.activated.connect(lambda: self._trigger_stop_from("shortcut"))

        # Hotkeys globales (keyboard) + WinAPI
        self._kb_hotkeys = []
        self._kb_ok = False
        self._install_global_hotkeys_keyboard()

        self._win_hotkeys_ids_home = set()  # IDs WinAPI para HOME
        self._win_hotkeys_ids_end  = set()  # IDs WinAPI para END
        self._native_filter = None
        self._install_global_hotkeys_winapi()

        # Timer de refresco
        self.timer = QTimer(self)
        self.timer.setInterval(250)
        self.timer.timeout.connect(self._refresh_state)
        self.timer.start()

        self._loaded_profile_path: Path | None = None

        # === Contexto de ruta para highlight (tab/idx vistos por logs) ===
        self._route_ctx = {"tab": None, "idx": None}

        self._route_last_shown = None  # (tab, idx, name) para no spamear la status bar

        # Cola corta de eventos recientes (para "Últimos eventos")
        self._recent_events = deque(maxlen=50)

        # Autocarga del último perfil
        self._autoload_last_profile()

    # ---------- Menú ----------
    def _build_menu_bar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")

        self.act_open = QAction("Cargar perfil…", self)
        self.act_open.setShortcut(QKeySequence("Ctrl+O"))
        self.act_open.setStatusTip("Abrir un archivo de perfil (.json)")
        self.act_open.hovered.connect(lambda: self._status("Cargar perfil… (Ctrl+O)"))
        self.act_open.triggered.connect(self._on_load_profile)

        self.act_save = QAction("Guardar", self)
        self.act_save.setShortcut(QKeySequence("Ctrl+S"))
        self.act_save.setStatusTip("Guardar el perfil actual")
        self.act_save.hovered.connect(lambda: self._status("Guardar (Ctrl+S)"))
        self.act_save.triggered.connect(self._on_save_shortcut)

        self.act_save_as = QAction("Guardar como…", self)
        self.act_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.act_save_as.setStatusTip("Guardar el perfil con otro nombre")
        self.act_save_as.hovered.connect(lambda: self._status("Guardar como… (Ctrl+Shift+S)"))
        self.act_save_as.triggered.connect(self._on_save_profile_as)

        self.act_exit = QAction("Salir", self)
        self.act_exit.setShortcut(QKeySequence("Ctrl+Q"))
        self.act_exit.setStatusTip("Cerrar la aplicación")
        self.act_exit.hovered.connect(lambda: self._status("Salir (Ctrl+Q)"))
        self.act_exit.triggered.connect(self.close)

        file_menu.hovered.connect(lambda act: self._status(act.text() if act else ""))

        file_menu.addAction(self.act_open)
        file_menu.addSeparator()
        file_menu.addAction(self.act_save)
        file_menu.addAction(self.act_save_as)
        file_menu.addSeparator()
        file_menu.addAction(self.act_exit)

    # ---------- Hotkeys globales (keyboard) ----------
    def _install_global_hotkeys_keyboard(self):
        """Intenta instalar HOME/END globales con 'keyboard' (necesita mismos privilegios que el juego)."""
        try:
            import keyboard  # pip install keyboard

            self._kb_hotkeys.append(
                keyboard.add_hotkey('home', lambda: QTimer.singleShot(0, lambda: self._trigger_pause_from("keyboard")))
            )
            self._kb_hotkeys.append(
                keyboard.add_hotkey('end',  lambda: QTimer.singleShot(0, lambda: self._trigger_stop_from("keyboard")))
            )
            self._kb_ok = True
            self._console_add("[Hotkeys] keyboard: HOME/END instalados.")
        except Exception as e:
            self._kb_ok = False
            self._console_add(f"[Hotkeys] keyboard no disponible: {e}")

    # ---------- Fallback nativo Windows: RegisterHotKey ----------
    def _install_global_hotkeys_winapi(self):
        """Registra HOME/END globales via API nativa. Intenta sin modificadores y también Ctrl+Alt."""
        if not sys.platform.startswith("win"):
            return
        try:
            user32 = ctypes.windll.user32
            MOD_ALT = 0x0001
            MOD_CONTROL = 0x0002
            VK_HOME = 0x24
            VK_END  = 0x23

            # IDs (pueden ser cualesquiera, pero únicos en el proceso)
            HK_HOME_PLAIN = 0xA011
            HK_END_PLAIN  = 0xA012
            HK_HOME_MOD   = 0xA001
            HK_END_MOD    = 0xA002

            # 1) Intentar HOME/END "pelados" (sin modificadores)
            ok_home_plain = user32.RegisterHotKey(None, HK_HOME_PLAIN, 0, VK_HOME)
            ok_end_plain  = user32.RegisterHotKey(None, HK_END_PLAIN,  0, VK_END)

            if ok_home_plain: self._win_hotkeys_ids_home.add(HK_HOME_PLAIN)
            if ok_end_plain:  self._win_hotkeys_ids_end.add(HK_END_PLAIN)

            if ok_home_plain or ok_end_plain:
                self._console_add("[Hotkeys] WinAPI: HOME/END sin modificadores registrados.")
            else:
                self._console_add("[Hotkeys] WinAPI: HOME/END sin modificadores NO disponibles (probablemente en uso).")

            # 2) Siempre registrar también Ctrl+Alt+Home / Ctrl+Alt+End como respaldo
            ok_home_mod = user32.RegisterHotKey(None, HK_HOME_MOD, MOD_CONTROL | MOD_ALT, VK_HOME)
            ok_end_mod  = user32.RegisterHotKey(None, HK_END_MOD,  MOD_CONTROL | MOD_ALT, VK_END)

            if ok_home_mod: self._win_hotkeys_ids_home.add(HK_HOME_MOD)
            if ok_end_mod:  self._win_hotkeys_ids_end.add(HK_END_MOD)

            if ok_home_mod or ok_end_mod:
                self._console_add("[Hotkeys] WinAPI: Ctrl+Alt+Home / Ctrl+Alt+End registrados (respaldo).")
            else:
                self._console_add("[Hotkeys] WinAPI: no pude registrar Ctrl+Alt+Home/End.")

            # Instalar filtro si se registró al menos uno
            if self._win_hotkeys_ids_home or self._win_hotkeys_ids_end:
                self._native_filter = _WinHotkeyFilter(
                    on_home=lambda: self._from_winapi_home(),
                    on_end=lambda: self._from_winapi_end(),
                    ids_home=tuple(self._win_hotkeys_ids_home),
                    ids_end=tuple(self._win_hotkeys_ids_end),
                )
                QCoreApplication.instance().installNativeEventFilter(self._native_filter)
                self._console_add("[Hotkeys] WinAPI activo.")
            else:
                self._console_add("[Hotkeys] WinAPI no disponible (ningún hotkey registrado).")

        except Exception as e:
            self._console_add(f"[Hotkeys] Error registrando WinAPI: {e}")

    # ---------- util de consola ----------
    def _console_add(self, text: str):
        fn = getattr(self.console, "add_line", None) or getattr(self.console, "append_line", None)
        if callable(fn):
            fn(text)

    # ---------- feedback / status ----------
    def _status(self, text: str, timeout_ms: int = 0):
        try:
            self.statusBar().showMessage(text, timeout_ms)
        except Exception:
            pass

    def _canon_tab(self, name: str) -> str:
        """
        Devuelve el nombre de tab con la capitalización EXACTA que existe en RoutePanel,
        haciendo comparación case-insensitive. Si no lo encuentra, retorna el original.
        """
        try:
            if not name:
                return name
            for i in range(self.route_panel.tabw.count()):
                t = self.route_panel.tabw.tabText(i)
                if t.lower() == str(name).lower():
                    return t
        except Exception:
            pass
        return name

    def _parse_route_log(self, line: str):
        """
        Extrae (tab, idx, name) de líneas [ROUTE] en formato JSON o texto.
        Acepta:
        - [ROUTE] {"route":{"tab":"hunt","idx":3}, "name":"wp4", ...}
        - [ROUTE] tab=hunt idx=3 name=wp4 ...
        - [ROUTE] tab=hunt i=3 ...
        Mantiene contexto para completar faltantes.
        Devuelve (tab:str, idx:int, name:str|None) o None.
        """
        import json, re

        s = (line or "").strip()
        if not s or "[ROUTE]" not in s:
            return None

        rest = s.split("[ROUTE]", 1)[1].strip()

        # 1) Intento JSON puro
        if rest.startswith("{"):
            try:
                obj = json.loads(rest)
                r = obj.get("route") or {}
                tab = str(r.get("tab") or "").strip()
                idx = r.get("idx")
                if isinstance(idx, str) and idx.isdigit():
                    idx = int(idx)
                if isinstance(idx, (int, float)):
                    idx = int(idx)
                name = obj.get("name")
                if tab and isinstance(idx, int):
                    # actualiza contexto y retorna
                    self._route_ctx["tab"] = tab
                    self._route_ctx["idx"] = idx
                    return tab, idx, (str(name) if name else None)
            except Exception:
                pass  # cae a regex textual

        # 2) Fallback: formato textual (tab=..., idx/i/index/row=..., name=..., wp=...)
        slow = rest.lower()

        tab = None
        m_tab = re.search(r'\btab\s*[:=]\s*"?([a-z0-9_\-]+)"?', slow)
        if m_tab:
            tab = m_tab.group(1).strip()

        idx = None
        m_idx = re.search(r'\b(?:idx|i|index|row)\s*[:=]\s*(\d+)', slow)
        if m_idx:
            try:
                idx = int(m_idx.group(1))
            except Exception:
                idx = None

        name = None
        m_name = re.search(r'\bname\s*[:=]\s*([^\s]+)', rest, flags=re.IGNORECASE)
        if m_name:
            name = m_name.group(1).strip().strip("'\"")
        else:
            m_wp = re.search(r'\bwp\s*[:=]\s*([^\s]+)', rest, flags=re.IGNORECASE)
            if m_wp:
                name = m_wp.group(1).strip().strip("'\"")

        # 3) Completar con contexto si falta algo
        if tab is None:
            tab = self._route_ctx.get("tab")
        if idx is None:
            idx = self._route_ctx.get("idx")

        if isinstance(tab, str) and tab and isinstance(idx, int):
            self._route_ctx["tab"] = tab
            self._route_ctx["idx"] = idx
            return tab, idx, name

        return None

    def _set_feedback(self, text: str, _color_hex: str = "#08c"):
        self._status(text, 4000)
        self._console_add(f"[GUI] {text}")

    # --- Botones globales ---
    def _on_start(self):
        """
        IMPORTANTE: fusionamos SIEMPRE los paneles (incluye ROUTE_ATTACH)
        antes de arrancar el cavebot para que respete el WP/tab elegido.
        Además, escribimos runtime_cfg.py aquí y le indicamos al Controller
        que no lo reescriba en start() (evita 'reset' de opciones).
        """
        # 1) Fusionar paneles -> perfil en memoria
        data = self._merge_panels_into_active_profile()
        self.controller.active_profile = data
        try:
            # Mantén coherencia en Controller/runtime antes de start
            self.controller.update_config(data)
        except Exception:
            pass

        # 1.5) Escribir runtime_cfg.py desde GUI con los valores actuales
        #      (incluye el parche de numéricos). Esto asegura que los
        #      cambios de opciones de Ruta se respeten.
        try:
            self._write_runtime_cfg_from_profile(data)
        except Exception:
            pass

        # Señal al Controller para que NO reescriba el runtime_cfg en start()
        try:
            setattr(self.controller, "_skip_runtime_write", True)
        except Exception:
            pass

        # 2) Arrancar con el perfil ya fusionado (y runtime_cfg ya escrito)
        ok, err = self.controller.start(data)
        if not ok:
            QMessageBox.warning(self, "No se pudo iniciar", err)
            return

        # 3) Resaltar y sembrar contexto con el ATTACH de arranque
        try:
            att = (self.controller.active_profile or {}).get("ROUTE_ATTACH", {}) or {}
            tab = att.get("tab") or self.route_panel.tabw.tabText(0)
            idx = int(att.get("index", 0))
            # Sembrar contexto para que el siguiente log parcial (solo idx o solo wp) funcione
            self._route_ctx = {"tab": tab, "idx": idx}
            self.route_panel.highlight_position(tab, idx)
            self._console_add(f"[ROUTE] start-at tab={tab} idx={idx}")
        except Exception:
            pass

    def _on_pause(self):
        st = self.controller.get_state()
        if not st["running"]:
            return
        if st["paused"]:
            self.controller.resume()
            self._status("RUN (Cavebot).")
        else:
            self.controller.pause()
            self._status("PAUSE (Cavebot).")

    def _on_stop(self):
        self.controller.stop()
        # Reset explícito del ATTACH (tab 0, fila 0) en la UI + config
        try:
            self.route_panel.reset_attach_to_default()
        except Exception:
            pass
        self._status("STOP.")

        # --- Resiembra el contexto de ruta con el ATTACH actual (después del reset) ---
        def _canon_tab_local(name: str) -> str:
            try:
                if not name:
                    return name
                for i in range(self.route_panel.tabw.count()):
                    t = self.route_panel.tabw.tabText(i)
                    if t.lower() == str(name).lower():
                        return t
            except Exception:
                pass
            return name

        try:
            att = (self.controller.active_profile or {}).get("ROUTE_ATTACH", {}) or {}
            tab = att.get("tab") or (self.route_panel.tabw.tabText(0) if self.route_panel.tabw.count() else "")
            idx = int(att.get("index", 0))
            tab = _canon_tab_local(tab)
            # Actualiza el contexto interno para que el siguiente log parcial funcione
            self._route_ctx = {"tab": tab, "idx": idx}
            # Opcional: refleja visualmente el attach actual al detener
            if tab:
                self.route_panel.highlight_position(tab, idx)
        except Exception:
            self._route_ctx = {"tab": None, "idx": None}

    # ---------- Wrappers de hotkeys (con logs) ----------
    def _trigger_pause_from(self, source: str):
        self._console_add(f"[Hotkeys] HOME via {source}")
        self._on_pause()

    def _trigger_stop_from(self, source: str):
        self._console_add(f"[Hotkeys] END via {source}")
        self._on_stop()

    def _from_winapi_home(self):
        self._trigger_pause_from("winapi")

    def _from_winapi_end(self):
        self._trigger_stop_from("winapi")

    # ---------- Perfil actual ----------
    def _current_profile_data(self) -> dict:
        data = getattr(self.controller, "active_profile", None)
        return data if isinstance(data, dict) else {}

    # ---------- Fusionar paneles -> perfil ----------
    def _merge_panels_into_active_profile(self) -> Dict[str, Any]:
        data = dict(self.controller.active_profile or {})
        data.update(self.regions_panel.to_profile_patch())
        data.update(self.pixels_panel.to_profile_patch())
        data.update(self.hotkeys_panel.to_profile_patch())
        data.update(self.route_panel.to_profile_patch())
        data.update(self.flags_panel.to_profile_patch())
        data.update(self.settings_panel.to_profile_patch())
        if hasattr(self, "ed_profile_name"):
            data["profile_name"] = self.ed_profile_name.text().strip() or data.get("profile_name", "")
        return data

    # --- Perfiles ---
    def _on_load_profile(self):
        cfg = getattr(self.controller, "config_manager", None)
        start_dir = str(cfg.profiles_dir if cfg else (Path.cwd() / "profiles"))

        path, _ = QFileDialog.getOpenFileName(self, "Cargar perfil", start_dir, "JSON (*.json)")
        if not path:
            return
        p = Path(path)

        try:
            if cfg:
                ok, data, err = cfg.load_profile(p)
                if not ok:
                    raise RuntimeError(err or "No se pudo cargar el perfil")
            else:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)

            self._set_feedback(f"Archivo «{p.name}» cargado.")
            self._loaded_profile_path = p

            self.controller.active_profile = data
            self.controller.active_profile_name = data.get("profile_name", p.stem)
            try:
                self.controller._remember_last_profile(self.controller.active_profile_name or p.stem)
            except Exception:
                pass

            self.regions_panel.load_from_profile(data)
            self.pixels_panel.load_from_profile(data)
            self.hotkeys_panel.load_from_profile(data)
            self.route_panel.load_from_profile(data)
            self.flags_panel.load_from_profile(data)
            self.settings_panel.load_from_profile(data)

            if cfg:
                warnings = cfg.validate_profile_images(data)
                for w in warnings:
                    self._console_add(w)

            self.controller.update_config(data)

        except Exception as e:
            QMessageBox.warning(self, "Error al cargar", str(e))

    def _on_save_profile(self):
        cfg = getattr(self.controller, "config_manager", None)
        if cfg is None:
            QMessageBox.warning(self, "Error al guardar", "ConfigManager no está disponible.")
            # Aun así, generamos runtime_cfg.py con lo que haya en GUI
            data = self._merge_panels_into_active_profile()
            self.controller.active_profile = data
            self._write_runtime_cfg_from_profile(data)
            return

        data = self._merge_panels_into_active_profile()
        self.controller.active_profile = data

        target_path = getattr(cfg, "active_profile_path", None)
        if not target_path:
            # redirige a Guardar Como…
            self._on_save_profile_as()
            # Guardar como se encarga de escribir runtime_cfg.py
            return

        ok, err = cfg.save_current(data)
        if not ok:
            QMessageBox.warning(self, "Error al guardar", err or "Error desconocido")
            # Igual generamos runtime_cfg.py para reflejar cambios
            self._write_runtime_cfg_from_profile(data)
            return

        try:
            name = Path(target_path).name
            stem = Path(target_path).stem
        except Exception:
            name = str(target_path)
            stem = name
        self._set_feedback(f"Archivo «{name}» guardado.")

        try:
            self.controller._remember_last_profile(self.controller.active_profile.get("profile_name", stem) or stem)
        except Exception:
            pass

        # Regenerar runtime_cfg.py con el perfil recién guardado
        self._write_runtime_cfg_from_profile(data)

    def _on_save_profile_as(self):
        cfg = getattr(self.controller, "config_manager", None)
        if cfg is None:
            QMessageBox.warning(self, "Error al guardar como…", "ConfigManager no está disponible.")
            # Aun si no hay ConfigManager, escribe runtime_cfg con lo que hay
            data = self._merge_panels_into_active_profile()
            self.controller.active_profile = data
            self._write_runtime_cfg_from_profile(data)
            return

        fname, _ = QFileDialog.getSaveFileName(
            self, "Guardar perfil como…",
            str(cfg.profiles_dir), "Perfiles JSON (*.json)"
        )
        if not fname:
            return
        path = Path(fname)
        if path.suffix.lower() != ".json":
            path = path.with_suffix(".json")

        data = self._merge_panels_into_active_profile()

        ok, err = cfg.save_profile(path, data)
        if not ok:
            QMessageBox.warning(self, "Error al guardar", err or "Error desconocido")
            # Aun si falla, actualiza runtime_cfg con los valores actuales
            self._write_runtime_cfg_from_profile(data)
            return

        prof_name = path.stem
        self.controller.active_profile = data
        self.controller.active_profile_name = prof_name
        self.lbl_profile.setText(f"{prof_name}")

        self._set_feedback(f"Archivo «{path.name}» guardado.")
        try:
            self.controller._remember_last_profile(prof_name)
        except Exception:
            pass

        # Regenerar runtime_cfg.py con el perfil recién guardado
        self._write_runtime_cfg_from_profile(data)

    # --- Refresco UI ---
    def _refresh_state(self):
        st = self.controller.get_state()

        # Labels resumen
        prof = st.get("profile_name") or "(sin cargar)"
        self.lbl_profile.setText(prof)

        running = bool(st.get("running"))
        paused  = bool(st.get("paused"))
        threads = st.get("threads", {})

        state_txt = "RUN" if running and not paused else ("PAUSE" if paused else "STOP")
        self.lbl_state.setText(state_txt)

        creatures = st.get("creatures", 0)
        red_val   = st.get("red", 0)
        self.lbl_counts.setText(f"{creatures} | {red_val}")

        # LEDs — Global
        self.led_global.set_state("on" if running else "off")

        cave_alive = bool(threads.get("cavebot"))
        if not running:
            self.led_cavebot.set_state("off")
        elif paused and cave_alive:
            self.led_cavebot.set_state("paused")
        else:
            self.led_cavebot.set_state("on" if cave_alive else "off")

        data = self._current_profile_data()
        def _is_set(key: str) -> bool:
            val = data.get(key, "")
            return bool(str(val).strip())

        # LEDs independientes de paused
        heal_enabled = _is_set("HK_HIGH_HEALING") or _is_set("HK_LOW_HEALING") or _is_set("HK_MANA_POTION")
        self.led_healing.set_state("on" if (running and heal_enabled) else "off")
        food_enabled = _is_set("HK_FOOD")
        self.led_food.set_state("on" if (running and food_enabled) else "off")
        anti_enabled = _is_set("HK_REMOVE_PARALYZE")
        self.led_anti.set_state("on" if (running and anti_enabled) else "off")

        # ---- Bloques del General ----
        self.g_act_cavebot.setText("ON" if (running and cave_alive and not paused) else ("PAUSE" if paused and cave_alive else "OFF"))
        self.g_act_healing.setText("ON" if (running and heal_enabled) else "OFF")
        self.g_act_food.setText("ON" if (running and food_enabled) else "OFF")
        self.g_act_anti.setText("ON" if (running and anti_enabled) else "OFF")
        self.g_act_crea.setText(str(creatures))
        self.g_act_red.setText("Sí" if bool(red_val) else "No")

        attack_until_arrived_off_x = str(data.get("ATTACK_UNTIL_ARRIVED_MODE", "")).lower() == "x"
        loot_after_kill_off_x      = str(data.get("LOOT_AFTER_KILL_MODE", "")).lower() == "x"
        self.g_prof_attack_route.setText("Sí" if not attack_until_arrived_off_x else "No")
        self.g_prof_loot_kill.setText("Sí" if not loot_after_kill_off_x else "No")

        ign = str(data.get("IGNORE_CREATURES_AT_MOST", "")).strip()
        self.g_prof_ignore_n.setText(ign if ign else "—")

        exit_on = str(data.get("exit_when_no_pots", "")).lower() == "x"
        self.g_prof_exit.setText("ON" if exit_on else "OFF")
        mana_img = data.get("POTION_CHECK_MANA_IMG", "")
        health_img = data.get("POTION_CHECK_HEALTH_IMG", "")
        self.g_prof_exit_imgs.setText(f"{mana_img or '—'} / {health_img or '—'}")

        # ====== LOGS → consola + últimos eventos + HIGHLIGHT/STATUS ======
        new_lines = self.controller.pop_logs()
        for ln in new_lines:
            self.console.append_line(ln)

            # Últimos eventos
            s = (ln or "").strip()
            if s:
                self._recent_events.append(s)

            # Intentar highlight/estatus desde logs (JSON-first)
            try:
                parsed = self._parse_route_log(ln)
                if parsed:
                    tab, idx, name = parsed
                    # 1) Intentar highlight en el panel de ruta (si está disponible)
                    try:
                        self.route_panel.highlight_position(tab, int(idx))
                    except Exception:
                        pass
                    # 2) Estatus visible (sin spamear)
                    wp_txt = (name or f"wp{int(idx)+1}")
                    key = (tab, int(idx), wp_txt)
                    if key != getattr(self, "_route_last_shown", None):
                        self._status(f"Ruta: {tab} → {wp_txt} (idx {idx})")
                        self._route_last_shown = key
            except Exception:
                pass

        # Panel "Últimos eventos"
        if self._recent_events:
            tail = list(self._recent_events)[-20:]
            self.g_events.setPlainText("\n".join(tail))
            self.g_events.verticalScrollBar().setValue(self.g_events.verticalScrollBar().maximum())
        else:
            self.g_events.setPlainText("")

    # --- Autocargar último perfil ---
    def _autoload_last_profile(self):
        try:
            last = ""
            if hasattr(self.controller, "get_last_profile_name"):
                last = self.controller.get_last_profile_name() or ""
            if not last:
                return
            data = self.controller.load_profile_from_disk(last)
            self.controller.active_profile = data
            self.controller.active_profile_name = data.get("profile_name", last)

            self.regions_panel.load_from_profile(data)
            self.pixels_panel.load_from_profile(data)
            self.hotkeys_panel.load_from_profile(data)
            self.route_panel.load_from_profile(data)
            self.flags_panel.load_from_profile(data)
            self.settings_panel.load_from_profile(data)

            self._set_feedback(f"Auto-cargado perfil «{self.controller.active_profile_name}».")
            self.controller.update_config(data)
        except Exception as e:
            self._console_add(f"[GUI] No se pudo auto-cargar último perfil: {e}")

    # --- Escribir runtime_cfg.py a partir del perfil actual ---
    def _write_runtime_cfg_from_profile(self, profile: dict) -> None:
        try:
            # Mantener coherencia en memoria
            if hasattr(self.controller, "update_config"):
                self.controller.update_config(profile)

            # Writer “oficial” si existe
            if hasattr(self.controller, "_write_runtime_cfg"):
                self.controller._write_runtime_cfg(profile)

            # Fuerza de forma robusta los numéricos de ruta
            self._patch_runtime_cfg_numbers(profile)

            self._console_add("[GUI] runtime_cfg.py actualizado.")
        except Exception as e:
            self._console_add(f"[GUI] Error al escribir runtime_cfg.py: {e}")

    def _find_runtime_cfg_path(self):
        """
        Intenta detectar la ruta de runtime_cfg.py:
        1) base_dir del ConfigManager si existe
        2) cwd (directorio actual)
        3) dos niveles arriba del archivo actual (raíz del proyecto)
        Devuelve la primera que exista o la mejor candidata para crear.
        """
        from pathlib import Path
        candidates = []

        base = getattr(getattr(self.controller, "config_manager", None), "base_dir", None)
        if base:
            candidates.append(Path(base) / "runtime_cfg.py")

        candidates.append(Path.cwd() / "runtime_cfg.py")

        try:
            here = Path(__file__).resolve()
            candidates.append(here.parents[2] / "runtime_cfg.py")
        except Exception:
            pass

        for c in candidates:
            if c.exists():
                return c
        return candidates[0] if candidates else Path("runtime_cfg.py")


    def _patch_runtime_cfg_numbers(self, profile: dict) -> None:
        """
        Reescribe (o añade) las 7 llaves numéricas en runtime_cfg.py
        a partir de los valores presentes en 'profile'.
        """
        from pathlib import Path
        import re

        keys = [
            ("WAIT_AFTER_ARRIVAL_S", float),
            ("WAIT_BEFORE_NEXT_WP_S", float),
            ("MAX_TRIES_PER_WP", int),
            ("SLEEP_AFTER_CLICK", float),
            ("LURE_MAX_TRIES", int),
            ("LURE_PAUSE_SEC", float),
            ("LURE_RESUME_SEC", float),
        ]

        # Tomar del perfil los valores vigentes
        vals = {}
        for k, cast in keys:
            if k in profile:
                try:
                    vals[k] = cast(profile[k])
                except Exception:
                    pass

        if not vals:
            return  # nada que forzar

        path = self._find_runtime_cfg_path()
        try:
            txt = Path(path).read_text(encoding="utf-8")
        except FileNotFoundError:
            header = "# === Archivo auto-generado por la GUI ===\nfrom __future__ import annotations\n\n"
            txt = header

        changed = False
        for k, v in vals.items():
            v_str = repr(float(v)) if isinstance(v, float) else str(int(v))
            pat = re.compile(rf'(?m)^{re.escape(k)}\s*=\s*.*$')
            line = f"{k} = {v_str}"
            if pat.search(txt):
                new_txt = pat.sub(line, txt)
            else:
                sep = "\n" if not txt.endswith("\n") else ""
                new_txt = txt + f"{sep}{line}\n"
            if new_txt != txt:
                txt = new_txt
                changed = True

        if changed:
            Path(path).write_text(txt, encoding="utf-8")
            # ---> Logea la ruta tocada para verificar rápidamente:
            self._console_add(f"[GUI] runtime_cfg.py actualizado en: {path}")
    

    # --- Ctrl+S: Guardar + runtime_cfg ---
    def _on_save_shortcut(self):
        """
        Guardar el perfil actual y reescribir runtime_cfg.py con la config fusionada
        de TODOS los paneles (incluido route_panel).
        """
        cfg = getattr(self.controller, "config_manager", None)

        # 1) Fusionar paneles -> active_profile
        data = self._merge_panels_into_active_profile()
        self.controller.active_profile = data

        # 2) Guardar si hay ConfigManager; si no, igual seguimos
        if cfg is not None:
            target_path = getattr(cfg, "active_profile_path", None)
            if not target_path:
                # Si no hay archivo activo, redirige a "Guardar como…" (esa ruta también escribe runtime_cfg.py)
                return self._on_save_profile_as()

            ok, err = cfg.save_current(data)
            if not ok:
                QMessageBox.warning(self, "Error al guardar", err or "Error desconocido")
                # Aunque falle el guardado, forzamos runtime_cfg.py con lo que hay en GUI
                self._write_runtime_cfg_from_profile(data)
                return
            try:
                name = Path(target_path).name
            except Exception:
                name = str(target_path)
            self._set_feedback(f"Archivo «{name}» guardado.")
        else:
            # No hay ConfigManager: avisa pero seguimos
            QMessageBox.warning(self, "Guardado local", "ConfigManager no está disponible; se actualizará solo runtime_cfg.py con la configuración actual.")

        # 3) Reescribir runtime_cfg.py usando el wrapper que hace el parche de llaves
        self._write_runtime_cfg_from_profile(data)

    # --- Limpiar hotkeys globales al cerrar ---
    def closeEvent(self, event):
        # keyboard
        try:
            import keyboard
            for hid in getattr(self, "_kb_hotkeys", []):
                try:
                    keyboard.remove_hotkey(hid)
                except Exception:
                    pass
        except Exception:
            pass

        # WinAPI
        if sys.platform.startswith("win"):
            try:
                user32 = ctypes.windll.user32
                # Desregistrar todos los IDs que hayamos usado
                for wid in list(getattr(self, "_win_hotkeys_ids_home", set())):
                    try: user32.UnregisterHotKey(None, int(wid))
                    except Exception: pass
                for wid in list(getattr(self, "_win_hotkeys_ids_end", set())):
                    try: user32.UnregisterHotKey(None, int(wid))
                    except Exception: pass

                if getattr(self, "_native_filter", None):
                    QCoreApplication.instance().removeNativeEventFilter(self._native_filter)
            except Exception:
                pass

        super().closeEvent(event)
