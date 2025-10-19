# gui/widgets/settings_panel.py
from __future__ import annotations
from typing import Dict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QGroupBox, QLabel, QLineEdit,
    QSpinBox, QDoubleSpinBox, QSizePolicy, QScrollArea, QAbstractSpinBox
)

# ---------- helpers visual ----------
def _expand(w):
    w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    return w

def _dbl_box(minv: float, maxv: float, step: float, val: float) -> QDoubleSpinBox:
    sb = QDoubleSpinBox()
    sb.setRange(minv, maxv)
    sb.setSingleStep(step)
    sb.setDecimals(2)
    sb.setValue(val)
    sb.setButtonSymbols(QAbstractSpinBox.NoButtons)
    return _expand(sb)

class _NPlusSpin(QSpinBox):
    """
    Spin que permite 'vacío' (= 0) para representar 'nulo'.
    - rango 0..8, con specialValueText("") para que 0 se vea vacío
    - value_or_none() -> None si está vacío, int si 1..8
    """
    def __init__(self, parent=None, maximum: int = 8):
        super().__init__(parent)
        self.setRange(0, maximum)
        self.setSingleStep(1)
        self.setSpecialValueText("")       # 0 se muestra como vacío
        self.setButtonSymbols(QAbstractSpinBox.NoButtons)
        _expand(self)

    def value_or_none(self):
        v = int(super().value())
        return None if v == 0 else v

    def set_from_optional(self, n: int | None):
        super().setValue(0 if (n is None) else int(max(1, n)))


def _int_to_nplus_or_empty(n_opt: int | None) -> str:
    return "" if n_opt is None else f"{max(1, int(n_opt))}+"

def _parse_nplus_optional(s) -> int | None:
    s = (s or "").strip()
    if not s:
        return None
    if s.endswith("+"):
        s = s[:-1]
    try:
        n = int(s)
        return max(1, n)
    except Exception:
        return None


class SettingsPanel(QWidget):
    """
    - Umbrales de ataque (N+) + Spell rotation (dos columnas)
    - Support (rotation, cooldown, start delay)
    """
    def __init__(self, controller=None, parent=None):
        super().__init__(parent)
        self.controller = controller

        self.setStyleSheet("""
            QAbstractSpinBox::up-button, QAbstractSpinBox::down-button { width:0; height:0; border:none; }
            QGroupBox { margin-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
        """)

        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0)
        scroll = QScrollArea(self); scroll.setWidgetResizable(True); outer.addWidget(scroll)
        container = QWidget(); scroll.setWidget(container)
        root = QVBoxLayout(container); root.setContentsMargins(8,8,8,8); root.setSpacing(10)

        # ====== Ataque (dos columnas) ======
        grp_attack = QGroupBox("Ataque", container)
        grid_attack = QGridLayout(grp_attack); grid_attack.setContentsMargins(8,8,8,8); grid_attack.setHorizontalSpacing(18)

        # Izquierda: N+
        grp_thr = QGroupBox("Umbrales de ataque (N+)", grp_attack)
        form_thr = QGridLayout(grp_thr); form_thr.setColumnStretch(1, 1)

        self.sb_exori      = _NPlusSpin()
        self.sb_exori_gran = _NPlusSpin()
        self.sb_exori_mas  = _NPlusSpin()
        self.sb_exori_hur  = _NPlusSpin()
        self.sb_exori_ico  = _NPlusSpin()

        r = 0
        form_thr.addWidget(QLabel("exori (N+):"),      r,0); form_thr.addWidget(self.sb_exori,      r,1); r+=1
        form_thr.addWidget(QLabel("exori gran (N+):"), r,0); form_thr.addWidget(self.sb_exori_gran, r,1); r+=1
        form_thr.addWidget(QLabel("exori mas (N+):"),  r,0); form_thr.addWidget(self.sb_exori_mas,  r,1); r+=1
        form_thr.addWidget(QLabel("exori hur (N+):"),  r,0); form_thr.addWidget(self.sb_exori_hur,  r,1); r+=1
        form_thr.addWidget(QLabel("exori ico (N+):"),  r,0); form_thr.addWidget(self.sb_exori_ico,  r,1); r+=1

        # Derecha: Spell rotation
        grp_spell = QGroupBox("Spell rotation", grp_attack)
        form_spell = QGridLayout(grp_spell); form_spell.setColumnStretch(1, 1)
        self.sb_spell_start = _dbl_box(0.00, 10.00, 0.05, 1.50)
        self.sb_spell_cd    = _dbl_box(0.00, 10.00, 0.05, 2.00)
        form_spell.addWidget(QLabel("Start delay (s):"), 0,0); form_spell.addWidget(self.sb_spell_start, 0,1)
        form_spell.addWidget(QLabel("Cooldown (s):"),    1,0); form_spell.addWidget(self.sb_spell_cd,   1,1)

        grid_attack.addWidget(grp_thr,   0,0)
        grid_attack.addWidget(grp_spell, 0,1)
        grid_attack.setColumnStretch(0,1); grid_attack.setColumnStretch(1,1)
        root.addWidget(grp_attack)

        # ====== Support ======
        grp_support = QGroupBox("Support", container)
        form_sup = QGridLayout(grp_support); form_sup.setColumnStretch(1, 1)
        self.le_support_rotation = _expand(QLineEdit()); self.le_support_rotation.setPlaceholderText("p.ej. boost,res,ampres")
        self.sb_support_cd   = _dbl_box(0.00, 10.00, 0.05, 2.00)
        self.sb_support_wait = _dbl_box(0.00, 10.00, 0.05, 1.00)
        r = 0
        form_sup.addWidget(QLabel("support rotation:"),        r,0); form_sup.addWidget(self.le_support_rotation, r,1); r+=1
        form_sup.addWidget(QLabel("support cooldown (s):"),    r,0); form_sup.addWidget(self.sb_support_cd,       r,1); r+=1
        form_sup.addWidget(QLabel("support start delay (s):"), r,0); form_sup.addWidget(self.sb_support_wait,     r,1); r+=1
        root.addWidget(grp_support)

        root.addStretch(1)

    # -------- Perfil -> UI --------
    def load_from_profile(self, profile: Dict):
        # N+ (permiten vacío)
        self.sb_exori.set_from_optional(_parse_nplus_optional(profile.get("USE_EXORI_MIN_PLUS")))
        self.sb_exori_gran.set_from_optional(_parse_nplus_optional(profile.get("USE_EXORIGRAN_MIN_PLUS")))
        self.sb_exori_mas.set_from_optional(_parse_nplus_optional(profile.get("USE_EXORIMAS_MIN_PLUS")))
        self.sb_exori_hur.set_from_optional(_parse_nplus_optional(profile.get("USE_EXORIHUR_MIN_PLUS")))
        self.sb_exori_ico.set_from_optional(_parse_nplus_optional(profile.get("USE_EXORICO_MIN_PLUS")))

        # Spell rotation
        try: self.sb_spell_start.setValue(float(profile.get("SPELL_ROTATION_START_DELAY", 1.50)))
        except Exception: pass
        try: self.sb_spell_cd.setValue(float(profile.get("SPELL_ROTATION_COOLDOWN", 2.00)))
        except Exception: pass

        # Support
        rot = profile.get("SUPPORT_ROTATION")
        self.le_support_rotation.setText(",".join(rot) if isinstance(rot, list) else str(rot or "boost,res,ampres"))
        try: self.sb_support_cd.setValue(float(profile.get("SUPPORT_COOLDOWN", 2.00)))
        except Exception: pass
        try: self.sb_support_wait.setValue(float(profile.get("SUPPORT_START_DELAY", 1.00)))
        except Exception: pass

    # -------- UI -> Perfil (patch) --------
    def to_profile_patch(self) -> Dict:
        rot_txt = self.le_support_rotation.text().strip()
        rot_list = [s.strip() for s in rot_txt.split(",") if s.strip()]
        return {
            # N+ (vacío -> "")
            "USE_EXORI_MIN_PLUS":     _int_to_nplus_or_empty(self.sb_exori.value_or_none()),
            "USE_EXORIGRAN_MIN_PLUS": _int_to_nplus_or_empty(self.sb_exori_gran.value_or_none()),
            "USE_EXORIMAS_MIN_PLUS":  _int_to_nplus_or_empty(self.sb_exori_mas.value_or_none()),
            "USE_EXORIHUR_MIN_PLUS":  _int_to_nplus_or_empty(self.sb_exori_hur.value_or_none()),
            "USE_EXORICO_MIN_PLUS":   _int_to_nplus_or_empty(self.sb_exori_ico.value_or_none()),

            "SPELL_ROTATION_START_DELAY": float(self.sb_spell_start.value()),
            "SPELL_ROTATION_COOLDOWN":    float(self.sb_spell_cd.value()),

            "SUPPORT_ROTATION": rot_list,
            "SUPPORT_COOLDOWN": float(self.sb_support_cd.value()),
            "SUPPORT_START_DELAY": float(self.sb_support_wait.value()),
        }
