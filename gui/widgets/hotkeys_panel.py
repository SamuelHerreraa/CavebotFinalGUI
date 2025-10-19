# gui/widgets/hotkeys_panel.py
from __future__ import annotations
from typing import Dict, List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QLabel
)

"""
HOTKEYS en GUI (EXCLUYENDO las fijas por defecto):
- Fijas (no aparecen en el tab):
  * HK_TOGGLE_PAUSE = "home"
  * HK_QUIT         = "-"
  * LURE_PAUSE_KEY  = "esc"
"""

HOTKEY_KEYS: List[str] = [
    "HK_FOOD",

    "HK_HIGH_HEALING",
    "HK_LOW_HEALING",
    "HK_MANA_POTION",

    "HK_EXORI_GRAN",
    "HK_EXORI",
    "HK_EXORI_MAS",
    "HK_EXORI_HUR",
    "HK_EXORI_ICO",

    "HK_EXETARES",
    "HK_BOOST",
    "HK_EXETAAMPRES",

    "HK_ROPE",
    "HK_SHOVEL",

    "HK_AMULET",
    "HK_RING",

    "HK_LOOT",
    "HK_TARGET",

    "HK_REMOVE_PARALYZE",
]

# Hints opcionales (se muestran como tooltip)
PLACEHOLDERS: Dict[str, str] = {
    "HK_FOOD": "p.ej. 5",
    "HK_HIGH_HEALING": "p.ej. f3",
    "HK_LOW_HEALING": "p.ej. f5",
    "HK_MANA_POTION": "p.ej. f6",
    "HK_EXORI_GRAN": "p.ej. 1",
    "HK_EXORI": "p.ej. 2",
    "HK_EXORI_MAS": "p.ej. 3",
    "HK_EXORI_HUR": "",
    "HK_EXORI_ICO": "",
    "HK_EXETARES": "p.ej. f1",
    "HK_BOOST": "",
    "HK_EXETAAMPRES": "",
    "HK_ROPE": "p.ej. f10",
    "HK_SHOVEL": "p.ej. f11",
    "HK_AMULET": "",
    "HK_RING": "",
    "HK_LOOT": "p.ej. add",
    "HK_TARGET": "p.ej. 9",
    "HK_REMOVE_PARALYZE": "p.ej. f2",
}

class HotkeysPanel(QWidget):
    """
    Tabla simple: (Nombre de clave) | (Hotkey)
    - Editable en la segunda columna
    - load_from_profile(): refleja lo que venga del JSON
    - to_profile_patch(): devuelve {CLAVE: "valor"} para fusionar al perfil
    """
    def __init__(self, controller=None, parent=None):
        super().__init__(parent)
        self.controller = controller

        lay = QVBoxLayout(self)

        # Nota informativa
        help_lbl = QLabel(
            "Valores típicos: 'f1', 'f2', '1', '2', 'add', etc."
        )
        lay.addWidget(help_lbl)

        self.table = QTableWidget(0, 2, self)
        self.table.setHorizontalHeaderLabels(["Nombre", "Hotkey"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True)
        self.table.setStyleSheet("QTableWidget::item:selected { background:#00c853; color:#000; }")

        lay.addWidget(self.table)

        self._populate_rows()
        self._tune_columns()

    # ---------- UI helpers ----------
    def _populate_rows(self):
        self.table.setRowCount(0)
        for key in HOTKEY_KEYS:
            r = self.table.rowCount()
            self.table.insertRow(r)

            it_name = QTableWidgetItem(key)
            it_name.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

            it_val = QTableWidgetItem("")  # vacío por defecto
            it_val.setTextAlignment(Qt.AlignCenter)

            # Usamos tooltip como “placeholder”/ayuda
            ph = PLACEHOLDERS.get(key, "")
            if ph:
                it_val.setToolTip(ph)

            self.table.setItem(r, 0, it_name)
            self.table.setItem(r, 1, it_val)

    def _tune_columns(self):
        self.table.setColumnWidth(0, 260)  # nombre
        self.table.setColumnWidth(1, 220)  # valor
        self.table.horizontalHeader().setStretchLastSection(True)

    # ---------- Perfil -> Tabla ----------
    def load_from_profile(self, profile: Dict):
        for row in range(self.table.rowCount()):
            key = self.table.item(row, 0).text()
            val = profile.get(key, "")
            self.table.item(row, 1).setText("" if val is None else str(val))

    # ---------- Tabla -> Perfil ----------
    def to_profile_patch(self) -> Dict[str, str]:
        out: Dict[str, str] = {}
        for row in range(self.table.rowCount()):
            key = self.table.item(row, 0).text()
            val = self.table.item(row, 1).text().strip()
            out[key] = val  # puede ser "" (nulo)
        return out
