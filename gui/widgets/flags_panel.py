# gui/widgets/flags_panel.py
from __future__ import annotations
from typing import Dict, List, Tuple, Set
import os, re

from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QPixmap, QMouseEvent
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QCheckBox, QLabel,
    QScrollArea, QHBoxLayout, QComboBox, QLineEdit, QPushButton,
    QSpinBox, QAbstractSpinBox, QGridLayout, QSizePolicy
)

# Overlays propios
from gui.widgets.pixel_picker import PixelPickerOverlay
from gui.widgets.region_picker import RegionPickerOverlay

HINT_STYLE = """
QGroupBox {
    border: 1px solid #2e2e2e;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 10px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: #cfd8dc;
}
QCheckBox { spacing: 8px; }
QCheckBox:hover { color: #e0f7fa; }
QCheckBox::indicator {
    width: 18px; height: 18px;
    border: 1px solid #555; border-radius: 3px; background: #222;
}
QCheckBox::indicator:hover { border: 1px solid #00c853; }
QCheckBox::indicator:checked {
    image: none;
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #00e676, stop:1 #00c853);
    border: 1px solid #00c853;
}
QComboBox { padding: 2px 8px; }
"""

THUMB_SIZE = 32      # 32x32 "SQM"
GRID_COLS  = 6       # columnas de la galería


def _inline_hint(text: str) -> QLabel:
    lab = QLabel(text)
    lab.setStyleSheet("color:#90a4ae; font-size:11px; margin-left:8px;")
    lab.setToolTip("Cómo se representa este flag dentro de main.py")
    return lab


class _Thumb(QWidget):
    """
    Miniatura clicable con estado ON/OFF.
    Evitamos parent-hacks: emitimos una señal directa al panel.
    """
    toggled = Signal(str, bool)  # (filename, selected)

    def __init__(self, img_path: str, display_name: str, selected: bool = False, parent=None):
        super().__init__(parent)
        self.img_path = img_path
        self.display_name = display_name
        self.filename = os.path.basename(img_path)
        self.selected = selected

        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(4)

        self.pic = QLabel(self)
        self.pic.setAlignment(Qt.AlignCenter)
        self.pic.setFixedSize(THUMB_SIZE, THUMB_SIZE)
        self.pic.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        pm = QPixmap(self.img_path)
        if not pm.isNull():
            self.pic.setPixmap(pm.scaled(THUMB_SIZE, THUMB_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.pic.setText("—")

        self.lbl = QLabel(self.display_name, self)
        self.lbl.setAlignment(Qt.AlignCenter)
        self.lbl.setStyleSheet("color:#cfd8dc; font-size:10px;")
        self.lbl.setWordWrap(True)

        lay.addWidget(self.pic, alignment=Qt.AlignCenter)
        lay.addWidget(self.lbl)

        self.setToolTip(self.filename)
        self._apply_selected_style()

    def sizeHint(self):
        # Altura total = 32 (img) + ~20 (texto) + márgenes
        return QSize(90, THUMB_SIZE + 26)

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.LeftButton:
            self.selected = not self.selected
            self._apply_selected_style()
            self.toggled.emit(self.filename, self.selected)
            # No llamamos a super() para evitar propagación innecesaria
            return
        super().mousePressEvent(e)

    def _apply_selected_style(self):
        if self.selected:
            self.setStyleSheet("""
                QWidget {
                    border: 2px solid #00e676;
                    border-radius: 8px;
                    background: rgba(0,255,136,0.08);
                }
            """)
        else:
            self.setStyleSheet("""
                QWidget {
                    border: 1px solid #3a3a3a;
                    border-radius: 8px;
                    background: #222;
                }
            """)


class FlagsPanel(QWidget):
    """
    Panel 'Flags' (con scroll) para opciones ON/OFF.

    + Targeting extra (cuando 'Pelear en ruta' = ON):
      ATTACK_SPECIFIC_CREATURE_ENABLED  → "x"/""
      SPECIFIC_CREATURE_REGION_X1Y1X2Y2 → (x1,y1,x2,y2)
      ATTACK_SPECIFIC_CREATURES         → [filenames ./creatures]
    """

    def __init__(self, controller=None, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setStyleSheet(HINT_STYLE)

        # Overlays
        self._pixel_overlay: PixelPickerOverlay | None = None
        self._region_overlay: RegionPickerOverlay | None = None

        # Estado local
        self._creature_dir = "creatures"
        self._thumbs: List[_Thumb] = []
        self._selected_creatures: Set[str] = set()
        self._specific_region: Tuple[int, int, int, int] | None = None

        outer = QVBoxLayout(self)

        # ---- Scroll container ----
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll)

        cont = QWidget()
        scroll.setWidget(cont)
        lay = QVBoxLayout(cont)
        lay.setAlignment(Qt.AlignTop)

        # ===== Combate / Loot =====
        gb_combat = QGroupBox("Combate / Loot", cont)
        v1 = QVBoxLayout(gb_combat)

        # Pelear en ruta
        self.cb_fight_during_route = QCheckBox("Pelear en ruta (atacar mientras vas al WP)", gb_combat)
        self.cb_fight_during_route.setToolTip(
            "ON: se detiene a combatir si aparecen enemigos durante el desplazamiento.\n"
            "OFF: ignora enemigos en ruta y solo combate al llegar al waypoint.\n\n"
            'main.py → ON: ""   |   OFF: "x"'
        )
        row1 = QHBoxLayout()
        row1.addWidget(self.cb_fight_during_route)
        row1.addWidget(_inline_hint('main: ""=ON, "x"=OFF'))
        row1.addStretch(1)
        v1.addLayout(row1)

        # (NUEVO) Attack specific creature — visible si "Pelear en ruta" = ON
        self.row_attack_specific = QWidget(gb_combat)
        row1b = QHBoxLayout(self.row_attack_specific)
        row1b.setContentsMargins(24, 0, 0, 0)
        self.cb_attack_specific = QCheckBox("Attack specific creature", self.row_attack_specific)
        self.cb_attack_specific.setToolTip(
            "ON: cuando atacas en ruta, limita el targeting a criaturas elegidas dentro de una región.\n"
            'main.py → ATTACK_SPECIFIC_CREATURE_ENABLED: "x"=ON, ""=OFF'
        )
        row1b.addWidget(self.cb_attack_specific)
        row1b.addWidget(_inline_hint('main: "x"=ON'))
        row1b.addStretch(1)
        v1.addWidget(self.row_attack_specific)

        # (NUEVO) Controles de región + galería
        self.row_specific_region = QWidget(gb_combat)
        v_region = QVBoxLayout(self.row_specific_region)
        v_region.setContentsMargins(48, 4, 0, 8)

        region_row = QHBoxLayout()
        self.lbl_specific_region = QLabel("specificcreatureregion_x1y1x2y2: (sin definir)", self.row_specific_region)
        self.lbl_specific_region.setStyleSheet("color:#cfd8dc;")
        self.btn_pick_specific = QPushButton("Pick Region (Overlay)", self.row_specific_region)
        self.btn_pick_specific.setToolTip("Selecciona una región en pantalla para buscar criaturas específicas.")
        region_row.addWidget(self.lbl_specific_region)
        region_row.addStretch(1)
        region_row.addWidget(self.btn_pick_specific)
        v_region.addLayout(region_row)

        # Galería scrollable y compacta
        gallery_box = QGroupBox("Elegir criaturas (carpeta ./creatures)", self.row_specific_region)
        vgal = QVBoxLayout(gallery_box)

        self.gallery_scroll = QScrollArea(gallery_box)
        self.gallery_scroll.setWidgetResizable(True)
        self.gallery_scroll.setMinimumHeight(THUMB_SIZE + 125)

        self.gallery_wrap = QWidget()
        self.grid_creatures = QGridLayout(self.gallery_wrap)
        self.grid_creatures.setContentsMargins(8, 8, 8, 8)
        self.grid_creatures.setHorizontalSpacing(8)
        self.grid_creatures.setVerticalSpacing(8)

        self.gallery_scroll.setWidget(self.gallery_wrap)
        vgal.addWidget(self.gallery_scroll)

        v_region.addWidget(gallery_box)
        v1.addWidget(self.row_specific_region)

        # ---- Loot tras cada kill ----
        self.cb_loot_after_kill = QCheckBox("Loot tras cada kill", gb_combat)
        row2 = QHBoxLayout()
        row2.addWidget(self.cb_loot_after_kill)
        row2.addWidget(_inline_hint('main: ""=ON, "x"=OFF'))
        row2.addStretch(1)
        v1.addLayout(row2)

        # ---- Ignorar si ≤ N criaturas ----
        self.cb_ignore_at_most = QCheckBox("Ignorar si ≤ N criaturas", gb_combat)
        self.cmb_ignore_n = QComboBox(gb_combat)
        for n in range(1, 9): self.cmb_ignore_n.addItem(str(n))
        row_ignore = QHBoxLayout()
        row_ignore.addWidget(self.cb_ignore_at_most)
        row_ignore.addWidget(self.cmb_ignore_n)
        row_ignore.addWidget(_inline_hint('main: "N"=ON, ""=OFF'))
        row_ignore.addStretch(1)
        v1.addLayout(row_ignore)

        lay.addWidget(gb_combat)

        # ===== Exit on pot =====
        gb_exit = QGroupBox("Exit on pot", cont)
        v2 = QVBoxLayout(gb_exit)

        self.cb_exit_master = QCheckBox("Salir cuando faltan potions", gb_exit)
        row3 = QHBoxLayout()
        row3.addWidget(self.cb_exit_master)
        row3.addWidget(_inline_hint('main: "x"=ON'))
        row3.addStretch(1)
        v2.addLayout(row3)

        subrow = QHBoxLayout(); subrow.setContentsMargins(24, 0, 0, 0)
        subcol = QVBoxLayout()

        self.cb_exit_check_mana = QCheckBox("Checar mana pot", gb_exit)
        self.cmb_mana_img = QComboBox(gb_exit)
        self.cmb_mana_img.addItems(["mp.png", "smp.png"])
        row_m = QHBoxLayout()
        row_m.addWidget(self.cb_exit_check_mana)
        row_m.addWidget(_inline_hint('main: "x"=ON'))
        row_m.addWidget(self.cmb_mana_img)
        row_m.addStretch(1)
        subcol.addLayout(row_m)

        self.cb_exit_check_health = QCheckBox("Checar health pot", gb_exit)
        self.cmb_health_img = QComboBox(gb_exit)
        self.cmb_health_img.addItems(["hp.png", "shp.png", "uhp.png", "supremepotion.png"])
        row_h = QHBoxLayout()
        row_h.addWidget(self.cb_exit_check_health)
        row_h.addWidget(_inline_hint('main: "x"=ON'))
        row_h.addWidget(self.cmb_health_img)
        row_h.addStretch(1)
        subcol.addLayout(row_h)

        subrow.addLayout(subcol)
        v2.addLayout(subrow)

        lay.addWidget(gb_exit)

        # ===== Training ML =====
        gb_train = QGroupBox("Training ML", cont)
        vt = QVBoxLayout(gb_train)

        self.cb_training_ml = QCheckBox("Activar Training ML (mana full → lanzar hotkey)", gb_train)
        row_t0 = QHBoxLayout()
        row_t0.addWidget(self.cb_training_ml)
        row_t0.addWidget(_inline_hint('main: TRAINING_ML_ENABLED'))
        row_t0.addStretch(1)
        vt.addLayout(row_t0)

        self.row_t1_container = QWidget(gb_train)
        row_t1 = QHBoxLayout(self.row_t1_container)
        row_t1.setContentsMargins(0, 0, 0, 0)
        self.lbl_training_hotkey = QLabel("Hotkey:", self.row_t1_container)
        self.le_training_hotkey = QLineEdit(self.row_t1_container)
        self.le_training_hotkey.setPlaceholderText("Hotkey (p. ej. 6, f7, ctrl+1)")
        self.le_training_hotkey.setMaxLength(16)
        self.le_training_hotkey.setFixedWidth(160)
        row_t1.addWidget(self.lbl_training_hotkey)
        row_t1.addWidget(self.le_training_hotkey)
        row_t1.addWidget(_inline_hint('main: TRAINING_ML_HOTKEY'))
        row_t1.addStretch(1)
        vt.addWidget(self.row_t1_container)

        self.row_t2_container = QWidget(gb_train)
        row_t2 = QHBoxLayout(self.row_t2_container)
        row_t2.setContentsMargins(0, 0, 0, 0)
        self.lbl_tml_x = QLabel("X:", self.row_t2_container)
        self.spn_tml_x = QSpinBox(self.row_t2_container)
        self.spn_tml_x.setRange(0, 9999); self.spn_tml_x.setFixedWidth(100)
        self.spn_tml_x.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.lbl_tml_y = QLabel("Y:", self.row_t2_container)
        self.spn_tml_y = QSpinBox(self.row_t2_container)
        self.spn_tml_y.setRange(0, 9999); self.spn_tml_y.setFixedWidth(100)
        self.spn_tml_y.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.btn_pick_tml = QPushButton("Pick Pixel (XY+RGB)", self.row_t2_container)
        row_t2.addWidget(self.lbl_tml_x); row_t2.addWidget(self.spn_tml_x)
        row_t2.addWidget(self.lbl_tml_y); row_t2.addWidget(self.spn_tml_y)
        row_t2.addWidget(self.btn_pick_tml)
        row_t2.addWidget(_inline_hint('main: TRAINING_ML_POS=(x,y)'))
        row_t2.addStretch(1)
        vt.addWidget(self.row_t2_container)

        self.row_t3_container = QWidget(gb_train)
        row_t3 = QHBoxLayout(self.row_t3_container)
        row_t3.setContentsMargins(0, 0, 0, 0)
        self.lbl_tml_r = QLabel("R:", self.row_t3_container)
        self.spn_tml_r = QSpinBox(self.row_t3_container)
        self.spn_tml_r.setRange(0, 255); self.spn_tml_r.setFixedWidth(80)
        self.spn_tml_r.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.lbl_tml_g = QLabel("G:", self.row_t3_container)
        self.spn_tml_g = QSpinBox(self.row_t3_container)
        self.spn_tml_g.setRange(0, 255); self.spn_tml_g.setFixedWidth(80)
        self.spn_tml_g.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.lbl_tml_b = QLabel("B:", self.row_t3_container)
        self.spn_tml_b = QSpinBox(self.row_t3_container)
        self.spn_tml_b.setRange(0, 255); self.spn_tml_b.setFixedWidth(80)
        self.spn_tml_b.setButtonSymbols(QAbstractSpinBox.NoButtons)
        row_t3.addWidget(self.lbl_tml_r); row_t3.addWidget(self.spn_tml_r)
        row_t3.addWidget(self.lbl_tml_g); row_t3.addWidget(self.spn_tml_g)
        row_t3.addWidget(self.lbl_tml_b); row_t3.addWidget(self.spn_tml_b)
        row_t3.addWidget(_inline_hint('main: TRAINING_ML_RGB=(r,g,b)'))
        row_t3.addStretch(1)
        vt.addWidget(self.row_t3_container)

        lay.addWidget(gb_train)

        # ===== Pelar =====
        self.gb_pelar = QGroupBox("Pelar", cont)
        vp = QVBoxLayout(self.gb_pelar)

        self.cb_pelar = QCheckBox("Activar Pelar", self.gb_pelar)
        row_p0 = QHBoxLayout()
        row_p0.addWidget(self.cb_pelar)
        row_p0.addWidget(_inline_hint('main: PELAR_ENABLED'))
        row_p0.addStretch(1)
        vp.addLayout(row_p0)

        self.row_p_mode_container = QWidget(self.gb_pelar)
        row_p_mode = QHBoxLayout(self.row_p_mode_container)
        row_p_mode.setContentsMargins(0, 0, 0, 0)
        self.lbl_pelar_mode = QLabel("Skinning mode:", self.row_p_mode_container)
        self.cmb_pelar_mode = QComboBox(self.row_p_mode_container)
        self.cmb_pelar_mode.addItem("Skin After Each Kill", userData="after_kill")
        self.cmb_pelar_mode.addItem("Skin After Clear",     userData="post_clear")
        row_p_mode.addWidget(self.lbl_pelar_mode)
        row_p_mode.addWidget(self.cmb_pelar_mode)
        row_p_mode.addWidget(_inline_hint('main: PELAR_MODE = \"after_kill\" | \"post_clear\"'))
        row_p_mode.addStretch(1)
        vp.addWidget(self.row_p_mode_container)

        self.row_p1_container = QWidget(self.gb_pelar)
        row_p1 = QHBoxLayout(self.row_p1_container)
        self.lbl_pelar_hotkey = QLabel("Hotkey:", self.row_p1_container)
        self.le_pelar_hotkey = QLineEdit(self.row_p1_container)
        self.le_pelar_hotkey.setPlaceholderText("Hotkey (p. ej. 7, f8, ctrl+2)")
        self.le_pelar_hotkey.setMaxLength(16)
        self.le_pelar_hotkey.setFixedWidth(160)
        row_p1.addWidget(self.lbl_pelar_hotkey)
        row_p1.addWidget(self.le_pelar_hotkey)
        row_p1.addWidget(_inline_hint('main: HK_PELAR'))
        row_p1.addStretch(1)
        vp.addWidget(self.row_p1_container)
        lay.addWidget(self.gb_pelar)

        # ===== Misceláneo =====
        gb_misc = QGroupBox("Misceláneo", cont)
        v3 = QVBoxLayout(gb_misc)
        self.cb_dropvials = QCheckBox("Tirar viales al finalizar (dropvials)", gb_misc)
        row4 = QHBoxLayout()
        row4.addWidget(self.cb_dropvials)
        row4.addWidget(_inline_hint('main: "x"=ON'))
        row4.addStretch(1)
        v3.addLayout(row4)
        lay.addWidget(gb_misc)
        lay.addStretch(1)

        # Señales → actualizar config al vuelo
        for cb, key in (
            (self.cb_fight_during_route, "ATTACK_UNTIL_ARRIVED_MODE"),
            (self.cb_loot_after_kill,    "LOOT_AFTER_KILL_MODE"),
            (self.cb_exit_master,        "exit_when_no_pots"),
            (self.cb_exit_check_mana,    "CHECK_MANA_ON"),
            (self.cb_exit_check_health,  "CHECK_HEALTH_ON"),
            (self.cb_dropvials,          "dropvials"),
            (self.cb_ignore_at_most,     "IGNORE_CREATURES_AT_MOST"),
            (self.cb_attack_specific,    "ATTACK_SPECIFIC_CREATURE_ENABLED"),
        ):
            cb.stateChanged.connect(lambda _=None, c=cb, k=key: self._on_flag_changed(c, k))

        # Eventos
        self.cmb_ignore_n.currentIndexChanged.connect(self._on_ignore_n_changed)
        self.cmb_mana_img.currentIndexChanged.connect(self._on_mana_img_changed)
        self.cmb_health_img.currentIndexChanged.connect(self._on_health_img_changed)

        self.cb_training_ml.stateChanged.connect(self._on_training_flag_changed)
        self.le_training_hotkey.textChanged.connect(self._on_training_hotkey_changed)
        self.spn_tml_x.valueChanged.connect(self._on_training_xy_changed)
        self.spn_tml_y.valueChanged.connect(self._on_training_xy_changed)
        self.spn_tml_r.valueChanged.connect(self._on_training_rgb_changed)
        self.spn_tml_g.valueChanged.connect(self._on_training_rgb_changed)
        self.spn_tml_b.valueChanged.connect(self._on_training_rgb_changed)
        self.btn_pick_tml.clicked.connect(self._on_training_pick_clicked)

        self.btn_pick_specific.clicked.connect(self._on_pick_specific_region_clicked)

        self.cb_pelar.stateChanged.connect(self._on_pelar_flag_changed)
        self.le_pelar_hotkey.textChanged.connect(self._on_pelar_hotkey_changed)
        self.cmb_pelar_mode.currentIndexChanged.connect(self._on_pelar_mode_changed)

        # Visibilidad inicial y galería
        self._sync_dependent_controls_visibility()
        self._reload_creature_gallery()

    # ---------- Perfil -> UI ----------
    def load_from_profile(self, profile: Dict):
        self.cb_fight_during_route.setChecked(str(profile.get("ATTACK_UNTIL_ARRIVED_MODE", "")).lower() != "x")
        self.cb_loot_after_kill.setChecked(   str(profile.get("LOOT_AFTER_KILL_MODE", "")).lower()      != "x")

        self.cb_attack_specific.setChecked(str(profile.get("ATTACK_SPECIFIC_CREATURE_ENABLED", "")).lower() == "x")
        reg = profile.get("SPECIFIC_CREATURE_REGION_X1Y1X2Y2", "")
        self._specific_region = self._parse_xyxy(reg)
        self._refresh_specific_region_label()

        selected = profile.get("ATTACK_SPECIFIC_CREATURES", [])
        self._selected_creatures = set(str(s) for s in selected) if isinstance(selected, (list, tuple)) else set()
        self._sync_thumbs_selection()

        val_ign = str(profile.get("IGNORE_CREATURES_AT_MOST", "")).strip()
        on_ignore, sel_n = False, 1
        if val_ign.isdigit():
            n = int(val_ign)
            if 1 <= n <= 8: on_ignore, sel_n = True, n
        self.cb_ignore_at_most.setChecked(on_ignore)
        self.cmb_ignore_n.setCurrentIndex(max(0, min(7, sel_n - 1)))

        self.cb_exit_master.setChecked(      str(profile.get("exit_when_no_pots", "")).lower() == "x")
        self.cb_exit_check_mana.setChecked(  str(profile.get("CHECK_MANA_ON", "")).lower()     == "x")
        self.cb_exit_check_health.setChecked(str(profile.get("CHECK_HEALTH_ON", "")).lower()   == "x")

        mana_img = str(profile.get("POTION_CHECK_MANA_IMG", "smp.png")).strip().lower()
        if mana_img not in ("mp.png", "smp.png"): mana_img = "mp.png"
        self.cmb_mana_img.setCurrentText(mana_img)

        health_img = str(profile.get("POTION_CHECK_HEALTH_IMG", "hp.png")).strip().lower()
        if health_img not in ("hp.png", "shp.png", "uhp.png", "supremepotion.png"): health_img = "hp.png"
        self.cmb_health_img.setCurrentText(health_img)

        self.cb_dropvials.setChecked(str(profile.get("dropvials", "")).lower() == "x")

        t_enabled = profile.get("TRAINING_ML_ENABLED", False)
        t_on = (str(t_enabled).lower() == "x") or (t_enabled is True) or (str(t_enabled) == "1")
        self.cb_training_ml.setChecked(t_on)
        self.le_training_hotkey.setText(str(profile.get("TRAINING_ML_HOTKEY", "")).strip())

        x, y = self._parse_xy(profile.get("TRAINING_ML_POS", (1001, 500)))
        self.spn_tml_x.setValue(x); self.spn_tml_y.setValue(y)

        r, g, b = self._parse_rgb(profile.get("TRAINING_ML_RGB", (195, 150, 125)))
        self.spn_tml_r.setValue(r); self.spn_tml_g.setValue(g); self.spn_tml_b.setValue(b)

        p_enabled = profile.get("PELAR_ENABLED", "")
        p_on = (str(p_enabled).lower() == "x") or (p_enabled is True) or (str(p_enabled) == "1")
        self.cb_pelar.setChecked(p_on)
        self.le_pelar_hotkey.setText(str(profile.get("HK_PELAR", "")).strip())

        mode = str(profile.get("PELAR_MODE", "after_kill")).strip().lower()
        if mode not in ("after_kill", "post_clear"): mode = "after_kill"
        for i in range(self.cmb_pelar_mode.count()):
            if self.cmb_pelar_mode.itemData(i) == mode:
                self.cmb_pelar_mode.setCurrentIndex(i); break

        self._sync_dependent_controls_visibility()

    # ---------- UI -> Perfil ----------
    def to_profile_patch(self) -> Dict:
        out: Dict[str, object] = {}
        out["ATTACK_UNTIL_ARRIVED_MODE"] = "" if self.cb_fight_during_route.isChecked() else "x"
        out["LOOT_AFTER_KILL_MODE"]      = "" if self.cb_loot_after_kill.isChecked()    else "x"

        out["ATTACK_SPECIFIC_CREATURE_ENABLED"] = "x" if self.cb_attack_specific.isChecked() else ""
        out["SPECIFIC_CREATURE_REGION_X1Y1X2Y2"] = (tuple(int(v) for v in self._specific_region)
                                                    if self._specific_region else "")
        out["ATTACK_SPECIFIC_CREATURES"] = list(sorted(self._selected_creatures))

        out["IGNORE_CREATURES_AT_MOST"] = self.cmb_ignore_n.currentText() if self.cb_ignore_at_most.isChecked() else ""
        out["exit_when_no_pots"] = "x" if self.cb_exit_master.isChecked()       else ""
        out["CHECK_MANA_ON"]     = "x" if self.cb_exit_check_mana.isChecked()    else ""
        out["CHECK_HEALTH_ON"]   = "x" if self.cb_exit_check_health.isChecked()  else ""
        out["dropvials"]         = "x" if self.cb_dropvials.isChecked()          else ""

        out["POTION_CHECK_MANA_IMG"]   = self.cmb_mana_img.currentText()
        out["POTION_CHECK_HEALTH_IMG"] = self.cmb_health_img.currentText()

        out["TRAINING_ML_ENABLED"] = "x" if self.cb_training_ml.isChecked() else ""
        out["TRAINING_ML_HOTKEY"]  = self.le_training_hotkey.text().strip()
        x = int(self.spn_tml_x.value()); y = int(self.spn_tml_y.value())
        r = int(self.spn_tml_r.value()); g = int(self.spn_tml_g.value()); b = int(self.spn_tml_b.value())
        out["TRAINING_ML_POS"] = (x, y)
        out["TRAINING_ML_RGB"] = (r, g, b)

        out["PELAR_ENABLED"] = "x" if self.cb_pelar.isChecked() else ""
        out["HK_PELAR"]      = self.le_pelar_hotkey.text().strip()
        out["PELAR_MODE"]    = self.cmb_pelar_mode.currentData() or "after_kill"
        return out

    # ---------- Cambio inmediato ----------
    def _on_flag_changed(self, checkbox: QCheckBox, key: str):
        if not self.controller or not hasattr(self.controller, "update_config"):
            self._sync_dependent_controls_visibility()
            return

        if key in ("ATTACK_UNTIL_ARRIVED_MODE", "LOOT_AFTER_KILL_MODE"):
            val = "" if checkbox.isChecked() else "x"
        elif key == "IGNORE_CREATURES_AT_MOST":
            val = self.cmb_ignore_n.currentText() if checkbox.isChecked() else ""
        elif key in ("exit_when_no_pots", "CHECK_MANA_ON", "CHECK_HEALTH_ON",
                     "dropvials", "ATTACK_SPECIFIC_CREATURE_ENABLED"):
            val = "x" if checkbox.isChecked() else ""
        else:
            self._sync_dependent_controls_visibility(); return

        try: self.controller.update_config({key: val})
        except Exception: pass

        self._sync_dependent_controls_visibility()

        if key == "CHECK_MANA_ON" and checkbox.isChecked():
            try: self.controller.update_config({"POTION_CHECK_MANA_IMG": self.cmb_mana_img.currentText()})
            except Exception: pass
        if key == "CHECK_HEALTH_ON" and checkbox.isChecked():
            try: self.controller.update_config({"POTION_CHECK_HEALTH_IMG": self.cmb_health_img.currentText()})
            except Exception: pass

        if key == "ATTACK_SPECIFIC_CREATURE_ENABLED" and checkbox.isChecked():
            try:
                if self._specific_region:
                    self.controller.update_config({"SPECIFIC_CREATURE_REGION_X1Y1X2Y2": tuple(self._specific_region)})
                if self._selected_creatures:
                    self.controller.update_config({"ATTACK_SPECIFIC_CREATURES": list(sorted(self._selected_creatures))})
            except Exception:
                pass

    # ---------- Handlers combos ----------
    def _on_ignore_n_changed(self, _idx: int):
        if not (self.controller and hasattr(self.controller, "update_config")): return
        if self.cb_ignore_at_most.isChecked():
            try: self.controller.update_config({"IGNORE_CREATURES_AT_MOST": self.cmb_ignore_n.currentText()})
            except Exception: pass

    def _on_mana_img_changed(self, _idx: int):
        if not (self.controller and hasattr(self.controller, "update_config")): return
        if self.cb_exit_check_mana.isChecked():
            try: self.controller.update_config({"POTION_CHECK_MANA_IMG": self.cmb_mana_img.currentText()})
            except Exception: pass

    def _on_health_img_changed(self, _idx: int):
        if not (self.controller and hasattr(self.controller, "update_config")): return
        if self.cb_exit_check_health.isChecked():
            try: self.controller.update_config({"POTION_CHECK_HEALTH_IMG": self.cmb_health_img.currentText()})
            except Exception: pass

    # ---------- Training ML ----------
    def _on_training_flag_changed(self, _state: int):
        if not (self.controller and hasattr(self.controller, "update_config")):
            self._sync_dependent_controls_visibility(); return
        val = "x" if self.cb_training_ml.isChecked() else ""
        try: self.controller.update_config({"TRAINING_ML_ENABLED": val})
        except Exception: pass
        self._sync_dependent_controls_visibility()

    def _on_training_hotkey_changed(self, _txt: str):
        if not (self.controller and hasattr(self.controller, "update_config")): return
        try: self.controller.update_config({"TRAINING_ML_HOTKEY": self.le_training_hotkey.text().strip()})
        except Exception: pass

    def _on_training_xy_changed(self, _=None):
        if not (self.controller and hasattr(self.controller, "update_config")): return
        x = int(self.spn_tml_x.value()); y = int(self.spn_tml_y.value())
        try: self.controller.update_config({"TRAINING_ML_POS": (x, y)})
        except Exception: pass

    def _on_training_rgb_changed(self, _=None):
        if not (self.controller and hasattr(self.controller, "update_config")): return
        r = int(self.spn_tml_r.value()); g = int(self.spn_tml_g.value()); b = int(self.spn_tml_b.value())
        try: self.controller.update_config({"TRAINING_ML_RGB": (r, g, b)})
        except Exception: pass

    def _on_training_pick_clicked(self):
        self._pixel_overlay = PixelPickerOverlay(self)
        self._pixel_overlay.pixelSelected.connect(self._on_overlay_pixel)
        self._pixel_overlay.show()

    def _on_overlay_pixel(self, x: int, y: int, r: int, g: int, b: int):
        self.spn_tml_x.setValue(int(x)); self.spn_tml_y.setValue(int(y))
        self.spn_tml_r.setValue(int(r)); self.spn_tml_g.setValue(int(g)); self.spn_tml_b.setValue(int(b))
        self._on_training_xy_changed(); self._on_training_rgb_changed()
        try:
            if self._pixel_overlay: self._pixel_overlay.close()
        finally:
            self._pixel_overlay = None

    # ---------- Pelar ----------
    def _on_pelar_flag_changed(self, _state: int):
        if not (self.controller and hasattr(self.controller, "update_config")):
            self._sync_dependent_controls_visibility(); return
        val = "x" if self.cb_pelar.isChecked() else ""
        try: self.controller.update_config({"PELAR_ENABLED": val})
        except Exception: pass
        self._sync_dependent_controls_visibility()

    def _on_pelar_hotkey_changed(self, _txt: str):
        if not (self.controller and hasattr(self.controller, "update_config")): return
        try: self.controller.update_config({"HK_PELAR": self.le_pelar_hotkey.text().strip()})
        except Exception: pass

    def _on_pelar_mode_changed(self, _idx: int):
        if not (self.controller and hasattr(self.controller, "update_config")):
            self._sync_dependent_controls_visibility(); return
        mode = self.cmb_pelar_mode.currentData() or "after_kill"
        try: self.controller.update_config({"PELAR_MODE": mode})
        except Exception: pass
        self._sync_dependent_controls_visibility()

    # ---------- Attack specific ----------
    def _on_pick_specific_region_clicked(self):
        if self._region_overlay:
            try: self._region_overlay.close()
            except Exception: pass
        self._region_overlay = RegionPickerOverlay(self)
        self._region_overlay.regionSelected.connect(self._on_specific_region_picked)

    def _on_specific_region_picked(self, x1: int, y1: int, x2: int, y2: int):
        self._specific_region = (int(x1), int(y1), int(x2), int(y2))
        self._refresh_specific_region_label()
        if self.controller and hasattr(self.controller, "update_config"):
            try: self.controller.update_config({"SPECIFIC_CREATURE_REGION_X1Y1X2Y2": self._specific_region})
            except Exception: pass

    def _on_creature_thumb_toggled(self, fname: str, is_selected: bool):
        if is_selected: self._selected_creatures.add(fname)
        else:           self._selected_creatures.discard(fname)
        if self.controller and hasattr(self.controller, "update_config"):
            try: self.controller.update_config({"ATTACK_SPECIFIC_CREATURES": list(sorted(self._selected_creatures))})
            except Exception: pass

    # ---------- Utils internos ----------
    def _sync_dependent_controls_visibility(self):
        self.cmb_ignore_n.setEnabled(self.cb_ignore_at_most.isChecked())

        on_route = self.cb_fight_during_route.isChecked()
        self.row_attack_specific.setVisible(on_route)
        self.cb_attack_specific.setEnabled(on_route)

        on_specific = on_route and self.cb_attack_specific.isChecked()
        self.row_specific_region.setVisible(on_specific)

        on_mana = self.cb_exit_check_mana.isChecked()
        self.cmb_mana_img.setVisible(on_mana); self.cmb_mana_img.setEnabled(on_mana)

        on_health = self.cb_exit_check_health.isChecked()
        self.cmb_health_img.setVisible(on_health); self.cmb_health_img.setEnabled(on_health)

        on_tml = self.cb_training_ml.isChecked()
        self.row_t1_container.setVisible(on_tml)
        self.row_t2_container.setVisible(on_tml)
        self.row_t3_container.setVisible(on_tml)

        self.gb_pelar.setVisible(True)
        on_p = self.cb_pelar.isChecked()
        self.row_p1_container.setVisible(on_p)
        self.row_p_mode_container.setVisible(on_p)

    def _reload_creature_gallery(self):
        # Limpieza
        while self.grid_creatures.count():
            item = self.grid_creatures.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None); w.deleteLater()
        self._thumbs.clear()

        if not os.path.isdir(self._creature_dir):
            return

        files = [f for f in os.listdir(self._creature_dir)
                 if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif"))]
        files.sort(key=str.lower)

        r, c = 0, 0
        for fname in files:
            path = os.path.join(self._creature_dir, fname)
            th = _Thumb(path, os.path.splitext(fname)[0], selected=(fname in self._selected_creatures))
            th.toggled.connect(self._on_creature_thumb_toggled)   # ← señal, no parent hacks
            self._thumbs.append(th)
            self.grid_creatures.addWidget(th, r, c)
            c += 1
            if c >= GRID_COLS:
                c = 0; r += 1

    def _sync_thumbs_selection(self):
        for th in self._thumbs:
            th.selected = (os.path.basename(th.img_path) in self._selected_creatures)
            th._apply_selected_style()

    def _refresh_specific_region_label(self):
        if self._specific_region:
            x1, y1, x2, y2 = self._specific_region
            self.lbl_specific_region.setText(f"specificcreatureregion_x1y1x2y2: ({x1}, {y1}) → ({x2}, {y2})")
        else:
            self.lbl_specific_region.setText("specificcreatureregion_x1y1x2y2: (sin definir)")

    # ---- Parsers helpers ----
    @staticmethod
    def _parse_xy(v) -> Tuple[int, int]:
        if isinstance(v, (list, tuple)) and len(v) == 2:
            return int(v[0]), int(v[1])
        s = str(v); m = re.findall(r"-?\d+", s)
        if len(m) >= 2: return int(m[0]), int(m[1])
        return 1001, 500

    @staticmethod
    def _parse_rgb(v) -> Tuple[int, int, int]:
        if isinstance(v, (list, tuple)) and len(v) == 3:
            return int(v[0]), int(v[1]), int(v[2])
        s = str(v); m = re.findall(r"-?\d+", s)
        if len(m) >= 3: return int(m[0]), int(m[1]), int(m[2])
        return 195, 150, 125

    @staticmethod
    def _parse_xyxy(v) -> Tuple[int, int, int, int] | None:
        if isinstance(v, (list, tuple)) and len(v) == 4:
            x1, y1, x2, y2 = map(int, v); return (x1, y1, x2, y2)
        s = str(v); nums = re.findall(r"-?\d+", s)
        if len(nums) >= 4:
            x1, y1, x2, y2 = map(int, nums[:4]); return (x1, y1, x2, y2)
        return None
