# gui/login_dialog.py
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QCheckBox, QPushButton, QWidget
)
from PySide6.QtCore import Qt

class LoginDialog(QDialog):
    def __init__(self, saved_email: str = "", saved_remember: bool = False, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Licencia requerida")
        self.setModal(True)
        self.setMinimumWidth(420)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(10)

        title = QLabel("<b>Inicia sesión para validar tu licencia</b>")
        root.addWidget(title)

        # --- Email ---
        row_email = QWidget(self)
        lay_e = QHBoxLayout(row_email); lay_e.setContentsMargins(0,0,0,0); lay_e.setSpacing(8)
        lay_e.addWidget(QLabel("Email:"))
        self.ed_email = QLineEdit()
        self.ed_email.setPlaceholderText("email@example.com")
        lay_e.addWidget(self.ed_email, 1)
        root.addWidget(row_email)

        # --- Password ---
        row_pass = QWidget(self)
        lay_p = QHBoxLayout(row_pass); lay_p.setContentsMargins(0,0,0,0); lay_p.setSpacing(8)
        lay_p.addWidget(QLabel("Password:"))
        self.ed_password = QLineEdit()
        self.ed_password.setEchoMode(QLineEdit.Password)
        lay_p.addWidget(self.ed_password, 1)
        root.addWidget(row_pass)

        # --- Remember ---
        self.chk_remember = QCheckBox("Recordar email")
        # Estilo: verde cuando está checked, borde oscuro cuando no
        self.chk_remember.setStyleSheet("""
            QCheckBox::indicator {
                width: 18px; height: 18px;
                border: 1px solid #333; border-radius: 4px;
                background: transparent;
            }
            QCheckBox::indicator:checked {
                background: #1db954;            /* verde */
                border: 1px solid #0f7a33;
            }
            QCheckBox { padding-left: 4px; }
        """)
        root.addWidget(self.chk_remember)

        # --- Error label ---
        self.lbl_error = QLabel("")
        self.lbl_error.setStyleSheet("color:#ff6b6b;")
        self.lbl_error.setWordWrap(True)
        root.addWidget(self.lbl_error)

        # --- Buttons ---
        row_btns = QWidget(self)
        lay_b = QHBoxLayout(row_btns); lay_b.setContentsMargins(0,0,0,0)
        lay_b.addStretch(1)
        self.btn_ok = QPushButton("Entrar")
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        lay_b.addWidget(self.btn_ok)
        lay_b.addWidget(self.btn_cancel)
        root.addWidget(row_btns)

        # Prefills
        self.ed_email.setText(saved_email or "")
        # Si había preferencia o email guardado → marcado (verde)
        self.chk_remember.setChecked(bool(saved_remember or saved_email))

        # UX: Enter para aceptar
        self.ed_email.returnPressed.connect(self.accept)
        self.ed_password.returnPressed.connect(self.accept)

    # ------------- API pública -------------
    def get_credentials(self):
        """
        Devuelve (email, password, remember: bool)
        """
        return (
            self.ed_email.text().strip(),
            self.ed_password.text(),
            bool(self.chk_remember.isChecked())
        )

    def set_error(self, msg: str):
        self.lbl_error.setText(msg or "")

    def show_license_info(self, days_remaining: int, plan: str = ""):
        """
        Si quisieras mostrar info en el propio diálogo (además del QMessageBox externo),
        podrías reutilizar esta función — actualmente no se usa por fuera.
        """
        if days_remaining is None:
            days_remaining = 0
        plan = plan or "-"
        self.set_error(f"Plan: {plan} — Días restantes: {int(days_remaining)}")
