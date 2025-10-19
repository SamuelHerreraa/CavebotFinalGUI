# gui/widgets/region_picker.py
from __future__ import annotations
from typing import List
from PySide6.QtCore import Qt, QRect, QPoint, Signal
from PySide6.QtGui import QGuiApplication, QPainter
from PySide6.QtWidgets import QWidget, QRubberBand

class _PerScreenOverlay(QWidget):
    """
    Overlay por pantalla. Sin velo oscuro para evitar destellos.
    Pinta la screenshot nativa del monitor y el QRubberBand para selección.
    """
    def __init__(self, screen, manager_parent):
        super().__init__(None)
        self.screen = screen
        self.manager_parent = manager_parent

        # Ventana: arriba, sin bordes, tipo tool (no roba foco)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)

        # Cubrir SOLO este monitor (sin fullscreen virtual)
        g = self.screen.geometry()
        self.setGeometry(g)

        # Evitar fondo del sistema y repintados innecesarios
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)

        # Captura de este monitor ANTES de mostrar (evita flash)
        self._bg = self.screen.grabWindow(0)

        # Selección
        self._dragging = False
        self._origin_global = QPoint()
        self._rubber = QRubberBand(QRubberBand.Rectangle, self)
        self._rubber.setStyleSheet("""
            QRubberBand {
                border: 2px solid #00ff88;
                background: rgba(0, 255, 136, 60);
            }
        """)
        self.setCursor(Qt.CrossCursor)

        # Mostrar ya con todo listo
        self.show()

    # ---------------- Eventos de ratón ----------------
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._dragging = True
            self._origin_global = e.globalPosition().toPoint()
            local = self.mapFromGlobal(self._origin_global)
            self._rubber.setGeometry(QRect(local, local))
            self._rubber.show()
        elif e.button() == Qt.RightButton:
            self.manager_parent._cancel_all()

    def mouseMoveEvent(self, e):
        if not self._dragging:
            return
        cur_global = e.globalPosition().toPoint()
        r_local = QRect(self.mapFromGlobal(self._origin_global),
                        self.mapFromGlobal(cur_global)).normalized()
        self._rubber.setGeometry(r_local)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton and self._dragging:
            self._dragging = False
            rect_local = self._rubber.geometry().normalized()
            self._rubber.hide()

            # Convertir a coordenadas globales
            tl_g = self.mapToGlobal(rect_local.topLeft())
            br_g = self.mapToGlobal(rect_local.bottomRight())
            x1, y1 = tl_g.x(), tl_g.y()
            x2, y2 = br_g.x(), br_g.y()

            if (x2 - x1) > 2 and (y2 - y1) > 2:
                self.manager_parent._emit_and_close(x1, y1, x2, y2)
            else:
                self.manager_parent._cancel_all()

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Escape, Qt.Key_Q):
            self.manager_parent._cancel_all()
        else:
            super().keyPressEvent(e)

    # ---------------- Pintado ----------------
    def paintEvent(self, _):
        # Pintamos solo la screenshot del monitor, SIN velo oscuro (para evitar destellos).
        p = QPainter(self)
        if not self._bg.isNull():
            p.drawPixmap(0, 0, self._bg)


class RegionPickerOverlay(QWidget):
    """
    Manager multi-monitor. Crea un overlay por QScreen y emite regionSelected(x1,y1,x2,y2)
    con coords globales cuando cualquiera termina la selección.
    """
    regionSelected = Signal(int, int, int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        # Manager no visible; solo orquesta
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self._overlays: List[_PerScreenOverlay] = []

        # Crear OVERLAYS ya listos (cada uno captura y luego se muestra)
        for scr in QGuiApplication.screens():
            ov = _PerScreenOverlay(scr, self)
            self._overlays.append(ov)

    # --- API interna usada por hijos ---
    def _emit_and_close(self, x1, y1, x2, y2):
        try:
            self.regionSelected.emit(x1, y1, x2, y2)
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
