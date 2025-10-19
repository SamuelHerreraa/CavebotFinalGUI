# gui/widgets/pixel_picker.py
from __future__ import annotations
from typing import List, Tuple
from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtGui import QGuiApplication, QPainter, QColor
from PySide6.QtWidgets import QWidget, QRubberBand


class _PerScreenPixelOverlay(QWidget):
    """
    Overlay por pantalla (sin flashes). Pinta la screenshot del monitor
    y permite elegir UN punto. Al hacer click izquierdo: emite x,y y el RGB
    tomado de la captura. Click derecho/Esc cancela.
    """
    def __init__(self, screen, manager_parent):
        super().__init__(None)
        self.screen = screen
        self.manager_parent = manager_parent

        # Ventana arriba y sin bordes
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)

        # Cubrir SOLO este monitor
        g = self.screen.geometry()
        self.setGeometry(g)

        # Sin fondo del sistema (evita destellos)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)

        # Captura previa del monitor
        self._bg = self.screen.grabWindow(0)

        # Indicador de punto (usa QRubberBand muy pequeño)
        self._rubber = QRubberBand(QRubberBand.Rectangle, self)
        self._rubber.setStyleSheet("""
            QRubberBand {
                border: 2px solid #00ff88;
                background: rgba(0, 255, 136, 60);
            }
        """)
        self.setCursor(Qt.CrossCursor)

        self.show()

    def _sample_rgb_global(self, gx: int, gy: int) -> Tuple[int, int, int]:
        """
        Toma color desde la captura de ESTE monitor.
        gx,gy están en coords globales; mapeamos a coords locales del monitor.
        """
        local = self.mapFromGlobal(QPoint(gx, gy))
        x, y = local.x(), local.y()
        if 0 <= x < self._bg.width() and 0 <= y < self._bg.height():
            qcol = QColor(self._bg.toImage().pixel(x, y))
            return qcol.red(), qcol.green(), qcol.blue()
        return (0, 0, 0)

    # ---------------- Eventos ----------------
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            gp = e.globalPosition().toPoint()
            # marca visual 3x3
            local = self.mapFromGlobal(gp)
            self._rubber.setGeometry(local.x() - 2, local.y() - 2, 5, 5)
            self._rubber.show()
        elif e.button() == Qt.RightButton:
            self.manager_parent._cancel_all()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            gp = e.globalPosition().toPoint()
            r, g, b = self._sample_rgb_global(gp.x(), gp.y())
            self.manager_parent._emit_and_close(gp.x(), gp.y(), r, g, b)

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Escape, Qt.Key_Q):
            self.manager_parent._cancel_all()
        else:
            super().keyPressEvent(e)

    # ---------------- Pintado ----------------
    def paintEvent(self, _):
        p = QPainter(self)
        if not self._bg.isNull():
            p.drawPixmap(0, 0, self._bg)


class PixelPickerOverlay(QWidget):
    """
    Manager multi-monitor. Crea un overlay por QScreen y emite pixelSelected(x,y,r,g,b)
    cuando cualquiera termina la selección.
    """
    pixelSelected = Signal(int, int, int, int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self._overlays: List[_PerScreenPixelOverlay] = []

        for scr in QGuiApplication.screens():
            ov = _PerScreenPixelOverlay(scr, self)
            self._overlays.append(ov)

    # --- API interna ---
    def _emit_and_close(self, x, y, r, g, b):
        try:
            self.pixelSelected.emit(x, y, r, g, b)
        finally:
            self._close_all()

    def _cancel_all(self):
        self._close_all()

    def _close_all(self):
        for ov in self._overlays:
            try:
                ov.hide()
                ov.deleteLater()
            except Exception:
                pass
        self._overlays.clear()
        self.close()
