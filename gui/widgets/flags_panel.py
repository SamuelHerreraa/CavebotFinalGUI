# gui/widgets/flags_panel.py
from __future__ import annotations
from typing import Dict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QCheckBox, QLabel,
    QScrollArea, QHBoxLayout, QComboBox
)

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
QCheckBox {
    spacing: 8px;
}
QCheckBox:hover {
    color: #e0f7fa;
}
QCheckBox::indicator {
    width: 18px; height: 18px;
    border: 1px solid #555; border-radius: 3px; background: #222;
}
QCheckBox::indicator:hover {
    border: 1px solid #00c853;
}
QCheckBox::indicator:checked {
    image: none;
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                                stop:0 #00e676, stop:1 #00c853);
    border: 1px solid #00c853;
}
QComboBox { padding: 2px 8px; }
"""

def _inline_hint(text: str) -> QLabel:
    lab = QLabel(text)
    lab.setStyleSheet("color:#90a4ae; font-size:11px; margin-left:8px;")
    lab.setToolTip("Cómo se representa este flag dentro de main.py")
    return lab

class FlagsPanel(QWidget):
    """
    Panel 'Flags' (con scroll) para opciones ON/OFF.

    Mapeo (compatible con main.py):
    - ATTACK_UNTIL_ARRIVED_MODE  → UI ON: ""   | UI OFF: "x"
    - LOOT_AFTER_KILL_MODE       → UI ON: ""   | UI OFF: "x"
    - IGNORE_CREATURES_AT_MOST   → UI ON: "N"(1..8) | UI OFF: ""
    - exit_when_no_pots          → UI ON: "x"  | UI OFF: ""
    - CHECK_MANA_ON              → UI ON: "x"  | UI OFF: ""
    - CHECK_HEALTH_ON            → UI ON: "x"  | UI OFF: ""
    - POTION_CHECK_MANA_IMG      → "mp.png" | "smp.png" (visible si CHECK_MANA_ON=ON)
    - POTION_CHECK_HEALTH_IMG    → "hp.png" | "shp.png" | "uhp.png" | "supremepotion.png" (visible si CHECK_HEALTH_ON=ON)
    - dropvials                  → UI ON: "x"  | UI OFF: ""
    """

    def __init__(self, controller=None, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setStyleSheet(HINT_STYLE)

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

        # Loot tras kill
        self.cb_loot_after_kill = QCheckBox("Loot tras cada kill", gb_combat)
        self.cb_loot_after_kill.setToolTip(
            "ON: lootea inmediatamente después de matar.\n"
            "OFF: no lootea entre kills; solo donde corresponda.\n\n"
            'main.py → ON: ""   |   OFF: "x"'
        )
        row2 = QHBoxLayout()
        row2.addWidget(self.cb_loot_after_kill)
        row2.addWidget(_inline_hint('main: ""=ON, "x"=OFF'))
        row2.addStretch(1)
        v1.addLayout(row2)

        # Ignorar si ≤ N criaturas (1..8)
        self.cb_ignore_at_most = QCheckBox("Ignorar si ≤ N criaturas", gb_combat)
        self.cb_ignore_at_most.setToolTip(
            "ON: sale del combate si el conteo de criaturas es ≤ N (excepto una casi muerta).\n"
            "OFF: no aplica este umbral."
        )
        self.cmb_ignore_n = QComboBox(gb_combat)
        for n in range(1, 9):
            self.cmb_ignore_n.addItem(str(n))
        self.cmb_ignore_n.setToolTip("Umbral N (1..8). Se aplica cuando el toggle está ON.")
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

        # Master
        self.cb_exit_master = QCheckBox("Salir cuando faltan potions", gb_exit)
        self.cb_exit_master.setToolTip(
            "ON: activa la secuencia de salida segura cuando falten potions (mana/health) según lo seleccionado.\n"
            'main.py → ON: "x"  |  OFF: ""'
        )
        row3 = QHBoxLayout()
        row3.addWidget(self.cb_exit_master)
        row3.addWidget(_inline_hint('main: "x"=ON'))
        row3.addStretch(1)
        v2.addLayout(row3)

        # Subopciones (indent)
        subrow = QHBoxLayout()
        subrow.setContentsMargins(24, 0, 0, 0)
        subcol = QVBoxLayout()

        # Checar mana pot + imagen
        self.cb_exit_check_mana = QCheckBox("Checar mana pot", gb_exit)
        self.cb_exit_check_mana.setToolTip('ON: revisa ícono de mana pot en la región configurada.  (main: "x"=ON)')
        self.cmb_mana_img = QComboBox(gb_exit)
        self.cmb_mana_img.addItems(["mp.png", "smp.png"])
        self.cmb_mana_img.setToolTip('Imagen a buscar cuando "Checar mana pot" está ON.')
        row_m = QHBoxLayout()
        row_m.addWidget(self.cb_exit_check_mana)
        row_m.addWidget(_inline_hint('main: "x"=ON'))
        row_m.addWidget(self.cmb_mana_img)
        row_m.addStretch(1)
        subcol.addLayout(row_m)

        # Checar health pot + imagen
        self.cb_exit_check_health = QCheckBox("Checar health pot", gb_exit)
        self.cb_exit_check_health.setToolTip('ON: revisa ícono de health pot en la región configurada.  (main: "x"=ON)')
        self.cmb_health_img = QComboBox(gb_exit)
        self.cmb_health_img.addItems(["hp.png", "shp.png", "uhp.png", "supremepotion.png"])
        self.cmb_health_img.setToolTip('Imagen a buscar cuando "Checar health pot" está ON.')
        row_h = QHBoxLayout()
        row_h.addWidget(self.cb_exit_check_health)
        row_h.addWidget(_inline_hint('main: "x"=ON'))
        row_h.addWidget(self.cmb_health_img)
        row_h.addStretch(1)
        subcol.addLayout(row_h)

        subrow.addLayout(subcol)
        v2.addLayout(subrow)

        lay.addWidget(gb_exit)

        # ===== Misceláneo =====
        gb_misc = QGroupBox("Misceláneo", cont)
        v3 = QVBoxLayout(gb_misc)

        self.cb_dropvials = QCheckBox("Tirar viales al finalizar (dropvials)", gb_misc)
        self.cb_dropvials.setToolTip('ON: al terminar una secuencia se tiran los viales acumulados.  (main: "x"=ON)')
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
        ):
            cb.stateChanged.connect(lambda _=None, c=cb, k=key: self._on_flag_changed(c, k))

        # Eventos de combos
        self.cmb_ignore_n.currentIndexChanged.connect(self._on_ignore_n_changed)
        self.cmb_mana_img.currentIndexChanged.connect(self._on_mana_img_changed)
        self.cmb_health_img.currentIndexChanged.connect(self._on_health_img_changed)

        # Visibilidad inicial de combos dependientes
        self._sync_dependent_controls_visibility()

    # ---------- Perfil -> UI ----------
    def load_from_profile(self, profile: Dict):
        # Combate / Loot (invertidos respecto a 'x')
        self.cb_fight_during_route.setChecked(str(profile.get("ATTACK_UNTIL_ARRIVED_MODE", "")).lower() != "x")
        self.cb_loot_after_kill.setChecked(   str(profile.get("LOOT_AFTER_KILL_MODE", "")).lower()      != "x")

        # Ignore ≤ N
        val_ign = str(profile.get("IGNORE_CREATURES_AT_MOST", "")).strip()
        on_ignore, sel_n = False, 1
        if val_ign.isdigit():
            n = int(val_ign)
            if 1 <= n <= 8:
                on_ignore, sel_n = True, n
        self.cb_ignore_at_most.setChecked(on_ignore)
        try:
            self.cmb_ignore_n.setCurrentIndex(max(0, min(7, sel_n - 1)))
        except Exception:
            self.cmb_ignore_n.setCurrentIndex(0)

        # Exit on pot (x = ON)
        self.cb_exit_master.setChecked(      str(profile.get("exit_when_no_pots", "")).lower() == "x")
        self.cb_exit_check_mana.setChecked(  str(profile.get("CHECK_MANA_ON", "")).lower()     == "x")
        self.cb_exit_check_health.setChecked(str(profile.get("CHECK_HEALTH_ON", "")).lower()   == "x")

        # Mana image
        mana_img = str(profile.get("POTION_CHECK_MANA_IMG", "smp.png")).strip().lower()
        if mana_img not in ("mp.png", "smp.png"):
            mana_img = "mp.png"
        self.cmb_mana_img.setCurrentText(mana_img)

        # Health image
        health_img = str(profile.get("POTION_CHECK_HEALTH_IMG", "hp.png")).strip().lower()
        if health_img not in ("hp.png", "shp.png", "uhp.png", "supremepotion.png"):
            health_img = "hp.png"
        self.cmb_health_img.setCurrentText(health_img)

        # Misceláneo (x = ON)
        self.cb_dropvials.setChecked(str(profile.get("dropvials", "")).lower() == "x")

        self._sync_dependent_controls_visibility()

    # ---------- UI -> Perfil (patch) ----------
    def to_profile_patch(self) -> Dict:
        out: Dict[str, str] = {}

        # Combate / Loot invertidos (UI ON -> "")
        out["ATTACK_UNTIL_ARRIVED_MODE"] = "" if self.cb_fight_during_route.isChecked() else "x"
        out["LOOT_AFTER_KILL_MODE"]      = "" if self.cb_loot_after_kill.isChecked()    else "x"

        # Ignore ≤ N
        out["IGNORE_CREATURES_AT_MOST"] = self.cmb_ignore_n.currentText() if self.cb_ignore_at_most.isChecked() else ""

        # Exit on pot & misc (x = ON)
        out["exit_when_no_pots"] = "x" if self.cb_exit_master.isChecked()       else ""
        out["CHECK_MANA_ON"]     = "x" if self.cb_exit_check_mana.isChecked()    else ""
        out["CHECK_HEALTH_ON"]   = "x" if self.cb_exit_check_health.isChecked()  else ""
        out["dropvials"]         = "x" if self.cb_dropvials.isChecked()          else ""

        # Persistir selección de imágenes
        out["POTION_CHECK_MANA_IMG"]   = self.cmb_mana_img.currentText()
        out["POTION_CHECK_HEALTH_IMG"] = self.cmb_health_img.currentText()

        return out

    # ---------- Cambio inmediato ----------
    def _on_flag_changed(self, checkbox: QCheckBox, key: str):
        if not self.controller or not hasattr(self.controller, "update_config"):
            self._sync_dependent_controls_visibility()
            return

        if key == "ATTACK_UNTIL_ARRIVED_MODE":
            val = "" if checkbox.isChecked() else "x"
        elif key == "LOOT_AFTER_KILL_MODE":
            val = "" if checkbox.isChecked() else "x"
        elif key == "IGNORE_CREATURES_AT_MOST":
            val = self.cmb_ignore_n.currentText() if checkbox.isChecked() else ""
        elif key in ("exit_when_no_pots", "CHECK_MANA_ON", "CHECK_HEALTH_ON", "dropvials"):
            val = "x" if checkbox.isChecked() else ""
        else:
            self._sync_dependent_controls_visibility()
            return

        try:
            self.controller.update_config({key: val})
        except Exception:
            pass

        self._sync_dependent_controls_visibility()

        # Si se activó mana/health-check, empujar también la imagen actual
        if key == "CHECK_MANA_ON" and checkbox.isChecked():
            try:
                self.controller.update_config({"POTION_CHECK_MANA_IMG": self.cmb_mana_img.currentText()})
            except Exception:
                pass
        if key == "CHECK_HEALTH_ON" and checkbox.isChecked():
            try:
                self.controller.update_config({"POTION_CHECK_HEALTH_IMG": self.cmb_health_img.currentText()})
            except Exception:
                pass

    def _on_ignore_n_changed(self, _idx: int):
        if not (self.controller and hasattr(self.controller, "update_config")):
            return
        if self.cb_ignore_at_most.isChecked():
            try:
                self.controller.update_config({"IGNORE_CREATURES_AT_MOST": self.cmb_ignore_n.currentText()})
            except Exception:
                pass

    def _on_mana_img_changed(self, _idx: int):
        if not (self.controller and hasattr(self.controller, "update_config")):
            return
        if self.cb_exit_check_mana.isChecked():
            try:
                self.controller.update_config({"POTION_CHECK_MANA_IMG": self.cmb_mana_img.currentText()})
            except Exception:
                pass

    def _on_health_img_changed(self, _idx: int):
        if not (self.controller and hasattr(self.controller, "update_config")):
            return
        if self.cb_exit_check_health.isChecked():
            try:
                self.controller.update_config({"POTION_CHECK_HEALTH_IMG": self.cmb_health_img.currentText()})
            except Exception:
                pass

    def _sync_dependent_controls_visibility(self):
        # Ignorar ≤ N: habilitar combo solo si el toggle está ON
        self.cmb_ignore_n.setEnabled(self.cb_ignore_at_most.isChecked())

        # Mana image combo: visible y habilitado si mana-check está ON
        on_mana = self.cb_exit_check_mana.isChecked()
        self.cmb_mana_img.setVisible(on_mana)
        self.cmb_mana_img.setEnabled(on_mana)

        # Health image combo: visible y habilitado si health-check está ON
        on_health = self.cb_exit_check_health.isChecked()
        self.cmb_health_img.setVisible(on_health)
        self.cmb_health_img.setEnabled(on_health)
