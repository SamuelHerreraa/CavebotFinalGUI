# gui/widgets/regions_panel.py
from __future__ import annotations
from typing import Dict, Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QMessageBox,
    QHeaderView, QSizePolicy
)

from gui.widgets.region_picker import RegionPickerOverlay

FIXED_REGIONS = [
    "PARALYZEBAR_RECT_X1Y1X2Y2",
    "AMULET_REGION_X1Y1X2Y2",
    "RING_REGION_X1Y1X2Y2",
    "BATTLELIST_RECT_X1Y1X2Y2",
    "EXIT_REGION_HEALTH_X1Y1X2Y2",
    "EXIT_REGION_MANA_X1Y1X2Y2",
    "EXIT_REGION_EXIT_X1Y1X2Y2",
    "ZOOM_RECT_X1Y1X2Y2",
]

class RegionsPanel(QWidget):
    """
    Tabla fija de 8 regiones. Solo 'Pick Region (Overlay)' para actualizar (x1,y1,x2,y2)
    de la fila seleccionada. La columna 'Nombre' es larga y flexible; x1,y1,x2,y2
    tienen ancho fijo para 5 dígitos y están centradas.
    """
    def __init__(self, controller=None, parent=None):
        super().__init__(parent)
        self.controller = controller

        lay = QVBoxLayout(self)

        # --- Tabla ---
        self.table = QTableWidget(0, 5, self)
        self.table.setHorizontalHeaderLabels(["Nombre", "x1", "y1", "x2", "y2"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(False)
        self.table.setShowGrid(True)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Alto de fila cómodo
        self.table.verticalHeader().setDefaultSectionSize(28)

        # --- Tamaños de columnas ---
        # Nombre: quepa "EXIT_REGION_HEALTH_X1Y1X2Y2111" y que ESTIRE.
        fm = self.table.fontMetrics()
        sample_text = "EXIT_REGION_HEALTH_X1Y1X2Y2111"
        name_min = fm.horizontalAdvance(sample_text) + 32  # margen
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Stretch)     # columna 0 (Nombre) estira
        self.table.setColumnWidth(0, name_min)              # ancho mínimo inicial

        # Numéricas: ancho fijo para 5 dígitos (ej. 99999)
        five_digits = fm.horizontalAdvance("99999") + 24    # padding
        for col in (1, 2, 3, 4):
            hh.setSectionResizeMode(col, QHeaderView.Fixed)
            self.table.setColumnWidth(col, max(70, five_digits))

        # Estilos: selección visible + padding
        self.table.setStyleSheet("""
            QTableWidget::item { padding: 6px 10px; }
            QTableWidget::item:selected { background: #00c853; color: #000; }
        """)

        lay.addWidget(self.table)

        # --- Botón: solo Pick ---
        btn_row = QHBoxLayout()
        self.btn_pick = QPushButton("Pick Region (Overlay)")
        btn_row.addStretch(1)
        btn_row.addWidget(self.btn_pick)
        lay.addLayout(btn_row)

        self._populate_defaults()

        # Señales
        self.btn_pick.clicked.connect(self._on_pick_region)

    # --------- Datos ----------
    def _populate_defaults(self):
        self.table.setRowCount(0)
        for name in FIXED_REGIONS:
            self._append_row(name, 0, 0, 0, 0)

    def _append_row(self, name: str, x1: int, y1: int, x2: int, y2: int):
        r = self.table.rowCount()
        self.table.insertRow(r)

        it_name = QTableWidgetItem(name)
        it_name.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

        it_x1 = QTableWidgetItem(str(x1))
        it_y1 = QTableWidgetItem(str(y1))
        it_x2 = QTableWidgetItem(str(x2))
        it_y2 = QTableWidgetItem(str(y2))

        for it in (it_x1, it_y1, it_x2, it_y2):
            it.setTextAlignment(Qt.AlignCenter)

        self.table.setItem(r, 0, it_name)
        self.table.setItem(r, 1, it_x1)
        self.table.setItem(r, 2, it_y1)
        self.table.setItem(r, 3, it_x2)
        self.table.setItem(r, 4, it_y2)

    def load_from_profile(self, profile: Dict):
        existing = {name: profile.get(name) for name in FIXED_REGIONS}
        self._populate_defaults()
        for row in range(self.table.rowCount()):
            name = self.table.item(row, 0).text()
            vals = existing.get(name)
            if isinstance(vals, (list, tuple)) and len(vals) == 4:
                self.table.item(row, 1).setText(str(int(vals[0])))
                self.table.item(row, 2).setText(str(int(vals[1])))
                self.table.item(row, 3).setText(str(int(vals[2])))
                self.table.item(row, 4).setText(str(int(vals[3])))

    def to_profile_patch(self) -> Dict[str, Tuple[int, int, int, int]]:
        out = {}
        for row in range(self.table.rowCount()):
            name = self.table.item(row, 0).text()
            try:
                x1 = int(self.table.item(row, 1).text())
                y1 = int(self.table.item(row, 2).text())
                x2 = int(self.table.item(row, 3).text())
                y2 = int(self.table.item(row, 4).text())
            except Exception:
                x1 = y1 = x2 = y2 = 0
            out[name] = (x1, y1, x2, y2)
        return out

    # --------- Overlay ----------
    def _on_pick_region(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Selecciona una fila", "Primero selecciona una región en la tabla.")
            return

        overlay = RegionPickerOverlay()
        overlay.regionSelected.connect(lambda x1,y1,x2,y2: self._apply_pick(row, x1,y1,x2,y2))
        overlay.show()

    def _apply_pick(self, row: int, x1: int, y1: int, x2: int, y2: int):
        self.table.item(row, 1).setText(str(x1))
        self.table.item(row, 2).setText(str(y1))
        self.table.item(row, 3).setText(str(x2))
        self.table.item(row, 4).setText(str(y2))

        try:
            name = self.table.item(row, 0).text()
            patch = {name: (x1, y1, x2, y2)}
            if self.controller and hasattr(self.controller, "update_config"):
                self.controller.update_config(patch)
        except Exception:
            pass
