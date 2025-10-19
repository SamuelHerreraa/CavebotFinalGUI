# gui/widgets/pixels_panel.py
from __future__ import annotations
from typing import Dict, Tuple, List

from ctypes import windll
from PySide6.QtCore import Qt, QTimer, QRect, Signal
from PySide6.QtGui import QCursor, QGuiApplication, QPainter, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QMessageBox,
    QFrame, QLabel
)

# ======== Util Windows: leer color de un pixel con GetPixel ========
_user32 = windll.user32
_gdi32  = windll.gdi32

def get_pixel_rgb_win32(x: int, y: int) -> Tuple[int, int, int]:
    hdc = _user32.GetDC(0)
    colorref = _gdi32.GetPixel(hdc, x, y)
    _user32.ReleaseDC(0, hdc)
    if colorref == -1:
        return (0, 0, 0)
    r =  colorref        & 0x0000FF
    g = (colorref >> 8)  & 0x0000FF
    b = (colorref >> 16) & 0x0000FF
    return (int(r), int(g), int(b))


# ======== Overlay de selección de PÍXEL (X,Y + RGB en vivo) ========
class PixelPickerOverlay(QWidget):
    picked = Signal(int, int, int, int, tuple)   # x, y, r, g, b

    def __init__(self, parent=None, hud_offset_y: int = 100):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self._screens: List[QWidget] = []
        for scr in QGuiApplication.screens():
            ov = _PerScreenPixelOverlay(scr, self, hud_offset_y)
            ov.show()
            self._screens.append(ov)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    def closeEvent(self, _):
        for w in self._screens:
            try:
                w.hide()
                w.deleteLater()
            except Exception:
                pass
        self._screens.clear()

    def _emit_and_close(self, x: int, y: int, rgb: Tuple[int,int,int]):
        r, g, b = rgb
        try:
            self.picked.emit(x, y, r, g, b)
        finally:
            self.close()


class _PerScreenPixelOverlay(QWidget):
    def __init__(self, screen, manager: PixelPickerOverlay, hud_offset_y: int):
        super().__init__(None)
        self._manager = manager
        self._hud_offset_y = hud_offset_y

        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        geo = screen.geometry()
        self.setGeometry(geo)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)
        self.setMouseTracking(True)
        self.setCursor(Qt.CrossCursor)

        self._bg = screen.grabWindow(0)
        self._hud_text = "x=0, y=0  |  RGB=(0,0,0)  |  Izq: elegir  |  Der/Esc: cancelar"

        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def _tick(self):
        pos = QCursor.pos()
        r, g, b = get_pixel_rgb_win32(pos.x(), pos.y())
        self._hud_text = f"x={pos.x()}, y={pos.y()}  |  RGB=({r},{g},{b})  |  Izq: elegir  |  Der/Esc: cancelar"
        hud_rect = QRect(self.geometry().width()//2 - 300, 10 + self._hud_offset_y, 600, 34)
        self.update(hud_rect)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            pos = QCursor.pos()
            rgb = get_pixel_rgb_win32(pos.x(), pos.y())
            self._manager._emit_and_close(pos.x(), pos.y(), rgb)
        elif e.button() == Qt.RightButton:
            self._manager.close()

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Escape, Qt.Key_Q):
            self._manager.close()
        else:
            super().keyPressEvent(e)

    def paintEvent(self, _):
        p = QPainter(self)
        if not self._bg.isNull():
            p.drawPixmap(0, 0, self._bg)
        hud_w, hud_h = 600, 34
        x = (self.width() - hud_w) // 2
        y = 10 + self._hud_offset_y
        p.fillRect(QRect(x, y, hud_w, hud_h), QColor(0, 0, 0, 180))
        p.setPen(QColor(255, 255, 255))
        p.drawText(QRect(x+10, y, hud_w-20, hud_h), Qt.AlignVCenter | Qt.AlignLeft, self._hud_text)


# ======== Panel de Píxeles ========
PIXEL_ROWS = [
    # --- Coordenadas clave del juego ---
    ("PLAYER_CENTER_MINIMAP", (1807, 82),  (0, 0, 0)),   # solo X,Y
    ("PLAYER_CENTER_SCREEN",  (862,  453), (0, 0, 0)),   # solo X,Y

    # --- Barras y colores de vida/mana/boost ---
    ("HIGH_HEAL_POS / HIGH_HEAL_RGB", (1845, 308), (218, 79, 79)),
    ("LOW_HEAL_POS / LOW_HEAL_RGB",   (1811, 307), (191, 64, 64)),
    ("MANA_POS / MANA_RGB",           (1840, 322), (101, 98, 239)),
    ("BOOST_COLOR_POS / BOOST_COLOR_RGB", (1831, 322), (101, 98, 239)),

    # --- Sistema de criaturas ---
    ("CREATURE_XY_START", (1594, 103), (0, 0, 0)),  # solo X,Y
    # ⬇️ AHORA 'both': X,Y + RGB
    ("CREATURE_DEAD_CHECK_POS / CREATURE_DEAD_CHECK_RGB", (1626, 103), (60, 60, 60)),
    ("CREATURE_ROW_DY", (23, 0), (0, 0, 0)),        # solo X
]

class ColorSwatch(QFrame):
    def __init__(self, rgb=(0,0,0), parent=None):
        super().__init__(parent)
        self.setFixedSize(44, 20)
        self.setFrameShape(QFrame.StyledPanel)
        self.set_rgb(rgb)

    def set_rgb(self, rgb):
        r,g,b = rgb
        self.setStyleSheet(f"background-color: rgb({r},{g},{b}); border: 1px solid #444; border-radius: 3px;")


class PixelsPanel(QWidget):
    """
    Tabla de posiciones/colores. Tipos por fila:
      - "both": X,Y y R,G,B (pos + rgb)
      - "pos":  solo X,Y (RGB colapsado)
      - "dy":   solo X (Y y RGB colapsados)
    """
    ROW_MAP = {
        # --- Coordenadas clave del juego ---
        "PLAYER_CENTER_MINIMAP": ("PLAYER_CENTER_MINIMAP", None, "pos"),
        "PLAYER_CENTER_SCREEN":  ("PLAYER_CENTER_SCREEN",  None, "pos"),

        # --- Barras y colores de vida/mana/boost ---
        "HIGH_HEAL_POS / HIGH_HEAL_RGB": ("HIGH_HEAL_POS", "HIGH_HEAL_RGB", "both"),
        "LOW_HEAL_POS / LOW_HEAL_RGB":   ("LOW_HEAL_POS",  "LOW_HEAL_RGB",  "both"),
        "MANA_POS / MANA_RGB":           ("MANA_POS",      "MANA_RGB",      "both"),
        "BOOST_COLOR_POS / BOOST_COLOR_RGB": ("BOOST_COLOR_POS", "BOOST_COLOR_RGB", "both"),

        # --- Sistema de criaturas ---
        "CREATURE_XY_START": ("CREATURE_XY_START", None, "pos"),
        # ⬇️ CAMBIO: ahora 'both'
        "CREATURE_DEAD_CHECK_POS / CREATURE_DEAD_CHECK_RGB": ("CREATURE_DEAD_CHECK_POS", "CREATURE_DEAD_CHECK_RGB", "both"),
        "CREATURE_ROW_DY": ("CREATURE_ROW_DY", None, "dy"),
    }

    def __init__(self, controller=None, parent=None):
        super().__init__(parent)
        self.controller = controller

        lay = QVBoxLayout(self)
        self.table = QTableWidget(0, 7, self)
        self.table.setHorizontalHeaderLabels(["Nombre", "X", "Y", "R", "G", "B", "Color"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True)
        self.table.setStyleSheet("QTableWidget::item:selected { background: #00c853; color: #000; }")

        self._populate_defaults()
        self._tune_columns()
        lay.addWidget(self.table)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        self.btn_pick = QPushButton("Pick Pixel (X,Y + RGB)")
        btn_row.addWidget(self.btn_pick)
        lay.addLayout(btn_row)
        self.btn_pick.clicked.connect(self._on_pick_pixel)

    # ----- columnas/filas -----
    def _tune_columns(self):
        hdr = self.table.horizontalHeader()
        hdr.setStretchLastSection(False)
        self.table.setColumnWidth(0, 360)
        for col in (1, 2, 3, 4, 5):
            self.table.setColumnWidth(col, 70)
        self.table.setColumnWidth(6, 56)
        self.table.setWordWrap(False)

    def _append_row(self, name: str, pos_xy: Tuple[int,int], rgb: Tuple[int,int,int]):
        r = self.table.rowCount()
        self.table.insertRow(r)

        it_name = QTableWidgetItem(name)
        it_name.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

        it_x = QTableWidgetItem(str(int(pos_xy[0])))
        it_y = QTableWidgetItem(str(int(pos_xy[1])))
        it_r = QTableWidgetItem(str(int(rgb[0])))
        it_g = QTableWidgetItem(str(int(rgb[1])))
        it_b = QTableWidgetItem(str(int(rgb[2])))
        for it in (it_x, it_y, it_r, it_g, it_b):
            it.setTextAlignment(Qt.AlignCenter)

        self.table.setItem(r, 0, it_name)
        self.table.setItem(r, 1, it_x)
        self.table.setItem(r, 2, it_y)
        self.table.setItem(r, 3, it_r)
        self.table.setItem(r, 4, it_g)
        self.table.setItem(r, 5, it_b)

        # Por defecto un swatch (si luego es pos/dy se reemplaza por “—”)
        sw = ColorSwatch(rgb, self.table)
        self.table.setCellWidget(r, 6, sw)

        # Aplicar bloqueo y “ocultamiento” por tipo
        pos_key, rgb_key, kind = self.ROW_MAP.get(name, (None, None, "both"))
        self._apply_kind_flags(r, kind)
        self._apply_kind_spans_and_swatch(r, kind)

    def _apply_kind_flags(self, row: int, kind: str):
        def _lock(col: int, lock: bool):
            it = self.table.item(row, col)
            if not it:
                return
            if lock:
                it.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            else:
                it.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)

        if kind == "both":
            for c in (1,2,3,4,5): _lock(c, False)
        elif kind == "pos":
            _lock(1, False); _lock(2, False)        # X,Y editables
            for c in (3,4,5): _lock(c, True)        # RGB bloqueados
        elif kind == "dy":
            _lock(1, False)                         # X editable
            _lock(2, True)                          # Y bloqueado
            for c in (3,4,5): _lock(c, True)        # RGB bloqueados

    def _apply_kind_spans_and_swatch(self, row: int, kind: str):
        # Limpiar span previo SOLO si realmente hay un span (>1x1)
        def _clear_rgb_span_if_needed():
            try:
                rs = self.table.rowSpan(row, 3)
                cs = self.table.columnSpan(row, 3)
            except Exception:
                rs = cs = 1
            if rs != 1 or cs != 1:
                self.table.setSpan(row, 3, 1, 1)

        if kind == "both":
            _clear_rgb_span_if_needed()
            # asegurar celdas R,G,B
            for c in (3, 4, 5):
                it = self.table.item(row, c)
                if it is None:
                    it = QTableWidgetItem("0")
                    it.setTextAlignment(Qt.AlignCenter)
                    it.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                    self.table.setItem(row, c, it)
            # swatch
            sw = self.table.cellWidget(row, 6)
            if not isinstance(sw, ColorSwatch):
                try:
                    r = int(self.table.item(row, 3).text() or 0)
                    g = int(self.table.item(row, 4).text() or 0)
                    b = int(self.table.item(row, 5).text() or 0)
                except Exception:
                    r = g = b = 0
                self.table.setCellWidget(row, 6, ColorSwatch((r, g, b), self.table))

        else:
            _clear_rgb_span_if_needed()
            self.table.setSpan(row, 3, 1, 3)

            na = QTableWidgetItem("—")
            na.setTextAlignment(Qt.AlignCenter)
            na.setFlags(Qt.ItemIsEnabled)
            na.setForeground(QColor("#888"))
            self.table.setItem(row, 3, na)

            lbl = QLabel("—", self.table)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color:#888;")
            self.table.setCellWidget(row, 6, lbl)

            if kind == "dy":
                it_y = QTableWidgetItem("—")
                it_y.setTextAlignment(Qt.AlignCenter)
                it_y.setFlags(Qt.ItemIsEnabled)
                it_y.setForeground(QColor("#888"))
                self.table.setItem(row, 2, it_y)

    def _populate_defaults(self):
        self.table.setRowCount(0)
        for name, pos, rgb in PIXEL_ROWS:
            self._append_row(name, pos, rgb)

    # ----- Perfil -> Tabla -----
    def load_from_profile(self, profile: Dict):
        for row in range(self.table.rowCount()):
            name = self.table.item(row, 0).text()
            pos_key, rgb_key, kind = self.ROW_MAP.get(name, (None, None, None))

            # POS
            if kind in ("both", "pos"):
                pos = profile.get(pos_key)
                if isinstance(pos, (list, tuple)) and len(pos) >= 2:
                    self.table.item(row, 1).setText(str(int(pos[0])))
                    self.table.item(row, 2).setText(str(int(pos[1])))

            # RGB (solo para 'both')
            if kind == "both":
                rgb = profile.get(rgb_key)
                if isinstance(rgb, (list, tuple)) and len(rgb) >= 3:
                    r, g, b = int(rgb[0]), int(rgb[1]), int(rgb[2])
                    self.table.item(row, 3).setText(str(r))
                    self.table.item(row, 4).setText(str(g))
                    self.table.item(row, 5).setText(str(b))
                    sw = self.table.cellWidget(row, 6)
                    if isinstance(sw, ColorSwatch):
                        sw.set_rgb((r, g, b))

            # DY
            if kind == "dy":
                dy = profile.get(pos_key)
                if isinstance(dy, int):
                    self.table.item(row, 1).setText(str(dy))

            # Reaplicar locks y spans
            self._apply_kind_flags(row, kind or "both")
            self._apply_kind_spans_and_swatch(row, kind or "both")

    # ----- Tabla -> Perfil (patch) -----
    def to_profile_patch(self) -> Dict:
        out = {}
        for row in range(self.table.rowCount()):
            name = self.table.item(row, 0).text()
            pos_key, rgb_key, kind = self.ROW_MAP.get(name, (None, None, None))
            if not pos_key:
                continue

            def _int_at(r, c):
                try:
                    return int(self.table.item(r, c).text())
                except Exception:
                    return 0

            x = _int_at(row, 1)
            y = _int_at(row, 2)
            r = _int_at(row, 3)
            g = _int_at(row, 4)
            b = _int_at(row, 5)

            if kind == "both":
                out[pos_key] = (x, y)
                out[rgb_key] = (r, g, b)
            elif kind == "pos":
                out[pos_key] = (x, y)
            elif kind == "dy":
                out[pos_key] = x  # solo X
        return out

    # ----- Overlay picker -----
    def _on_pick_pixel(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Selecciona una fila", "Primero selecciona una entrada en la tabla.")
            return
        overlay = PixelPickerOverlay(self, hud_offset_y=100)
        overlay.picked.connect(lambda x,y,r,g,b: self._apply_pick(row, x,y,r,g,b))

    def _apply_pick(self, row: int, x: int, y: int, r: int, g: int, b: int):
        name = self.table.item(row, 0).text()
        pos_key, rgb_key, kind = self.ROW_MAP.get(name, (None, None, None))

        # reflejar en tabla
        if kind in ("both", "pos"):
            self.table.item(row, 1).setText(str(x))
            self.table.item(row, 2).setText(str(y))
        if kind == "both":
            self.table.item(row, 3).setText(str(r))
            self.table.item(row, 4).setText(str(g))
            self.table.item(row, 5).setText(str(b))
            sw = self.table.cellWidget(row, 6)
            if isinstance(sw, ColorSwatch):
                sw.set_rgb((r, g, b))
        if kind == "dy":
            self.table.item(row, 1).setText(str(x))

        # enviar patch al controller
        try:
            patch = {}
            if kind == "both":
                patch[pos_key] = (x, y)
                patch[rgb_key] = (r, g, b)
            elif kind == "pos":
                patch[pos_key] = (x, y)
            elif kind == "dy":
                patch[pos_key] = int(self.table.item(row, 1).text() or 0)
            if patch and self.controller and hasattr(self.controller, "update_config"):
                self.controller.update_config(patch)
        except Exception:
            pass
