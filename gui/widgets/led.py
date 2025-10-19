# gui/widgets/led.py
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout
from PySide6.QtCore import Qt

class Led(QWidget):
    """
    LED con 3 estados:
      - "on"     -> verde
      - "paused" -> ámbar
      - "off"    -> rojo (o gris oscuro)
    """
    def __init__(self, label: str = ""):
        super().__init__()
        self._state = "off"

        self.dot = QLabel(" ")
        self.dot.setFixedSize(14, 14)
        self.dot.setStyleSheet(self._style_for("off"))

        self.text = QLabel(label)
        self.text.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(4, 0, 4, 0)
        lay.setSpacing(6)
        lay.addWidget(self.dot)
        lay.addWidget(self.text)

    def _style_for(self, state: str) -> str:
        if state == "on":
            color = "#3DDC84"   # verde
        elif state == "paused":
            color = "#FFB020"   # ámbar
        else:
            color = "#D14D4D"   # rojo
        return (
            f"border-radius:7px; background:{color};"
            "border:1px solid rgba(0,0,0,0.2);"
        )

    def set_state(self, state: str):
        if state not in ("on", "paused", "off"):
            state = "off"
        if state != self._state:
            self._state = state
            self.dot.setStyleSheet(self._style_for(state))

    # Atajos de compatibilidad
    def set_on(self, on: bool):
        self.set_state("on" if on else "off")

    def set_paused(self):
        self.set_state("paused")
