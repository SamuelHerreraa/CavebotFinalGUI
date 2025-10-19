# gui/widgets/route_panel.py
from __future__ import annotations
from typing import List, Dict, Any, Tuple
from pathlib import Path

from PySide6.QtCore import Qt, QEvent, QPoint, QSize, Signal
from PySide6.QtGui import QAction, QPixmap, QPainter, QColor, QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QComboBox, QMessageBox, QMenu, QScrollArea, QLabel,
    QGridLayout, QFrame, QSizePolicy, QTabWidget, QInputDialog, QToolButton,
    QGroupBox, QFormLayout, QSpinBox, QDoubleSpinBox, QAbstractSpinBox
)

# ------------ Constantes / ajustes ------------
ACTIONS = ["none", "lure", "zoom", "rope", "shovel", "stairs", "ignore", "goto"]
GALLERY_WPS = [f"wp{i}" for i in range(1, 21)] + ["zoomin", "zoomout"]

THUMB_SIZE      = QSize(28, 28)
GALLERY_COLS    = 6
GALLERY_SPACE   = 1
GALLERY_MARG    = (1, 1, 1, 1)
TABLE_ICON_SIZE = QSize(18, 18)  # icono en columna WP

ROLE_GOTO = Qt.UserRole + 10    # {"tab": str, "label": str}


# ---------- Mini widget clicable para la galería ----------
class _GalleryItem(QFrame):
    clicked = Signal(str)

    def __init__(self, name: str, img_path: Path | None,
                 thumb_size: QSize = THUMB_SIZE, parent=None):
        super().__init__(parent)
        self._name = name
        self.setObjectName("GalleryItem")
        self.setCursor(Qt.PointingHandCursor)

        self.setFixedWidth(thumb_size.width() + 26)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(6)

        self._thumb = QLabel(self)
        self._thumb.setFixedSize(thumb_size)
        self._thumb.setAlignment(Qt.AlignCenter)
        pm = self._make_thumb(img_path, thumb_size)
        self._thumb.setPixmap(pm)
        lay.addWidget(self._thumb, alignment=Qt.AlignCenter)

        self._lbl = QLabel(name, self)
        self._lbl.setAlignment(Qt.AlignCenter)
        self._lbl.setStyleSheet("color:#ccc; font-size:11px;")
        lay.addWidget(self._lbl, alignment=Qt.AlignCenter)

        self.setStyleSheet("""
            QFrame#GalleryItem {
                border: 1px solid #333; border-radius: 8px; background: rgba(255,255,255,0.03);
            }
            QFrame#GalleryItem:hover {
                border-color: #09f; background: rgba(0,153,255,0.08);
            }
        """)

    def _make_thumb(self, img_path: Path | None, size: QSize) -> QPixmap:
        w, h = size.width(), size.height()
        canvas = QPixmap(w, h)
        canvas.fill(QColor(24, 24, 24))

        p = QPainter(canvas)
        p.fillRect(0, 0, w, h, QColor(20, 20, 20))

        if img_path and img_path.exists():
            src = QPixmap(str(img_path))
            if not src.isNull():
                scaled = src.scaled(w - 8, h - 8, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                x = (w - scaled.width()) // 2
                y = (h - scaled.height()) // 2
                p.drawPixmap(x, y, scaled)
        else:
            p.setPen(QColor(160, 160, 160))
            p.drawText(0, 0, w, h, Qt.AlignCenter, "no img")
        p.end()
        return canvas

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit(self._name)
        super().mouseReleaseEvent(e)


class RoutePanel(QWidget):
    """
    Panel 'Ruta & Waypoints' con sub-tabs internos.
    Sin simulador: la UI solo resalta según:
      - Doble click en WP (columna 1) para fijar ATTACH (punto de inicio).
      - Logs reales del cavebot (MainWindow._refresh_state → highlight_position()).
      - Feedback “Inicio: …” mostrando desde dónde arrancará si presionas Start.
    """

    def __init__(self, controller=None, parent=None):
        super().__init__(parent)
        self.controller = controller

        # Rutas base para imágenes ./marcas
        self.base_dir: Path = getattr(getattr(controller, "config_manager", None), "base_dir", None) \
                              or getattr(controller, "base_dir", None) \
                              or Path.cwd()
        self.marcas_dir: Path = Path(self.base_dir) / "marcas"

        # Estructuras internas
        self._tab_tables: list[QTableWidget] = []

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        # -------- Columna izquierda: Tabs + Tabla + Botones --------
        left = QVBoxLayout()
        left.setContentsMargins(6, 6, 6, 6)
        left.setSpacing(8)

        # Tabs
        self.tabw = QTabWidget(self)
        self.tabw.setMovable(True)
        self.tabw.setTabsClosable(False)

        # Botón "+" minimalista con hover
        self.btn_add_tab = QToolButton(self)
        self.btn_add_tab.setText("+")
        self.btn_add_tab.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.btn_add_tab.setAutoRaise(True)
        self.btn_add_tab.setCursor(Qt.PointingHandCursor)
        self.btn_add_tab.setToolTip("Agregar tab de ruta")
        self.btn_add_tab.setStyleSheet("""
        QToolButton {
            padding: 4px 10px;
            font-weight: 700;
            border: 1px solid #2a2a2a;
            border-radius: 6px;
        }
        QToolButton:hover {
            background: rgba(0,153,255,0.15);
            border-color: #09f;
        }
        """)
        self.btn_add_tab.clicked.connect(self._prompt_add_tab)
        self.tabw.setCornerWidget(self.btn_add_tab, Qt.TopRightCorner)

        # Menú contextual en la barra de tabs (eliminar/renombrar)
        self.tabw.tabBar().setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabw.tabBar().customContextMenuRequested.connect(self._on_tabbar_context_menu)

        left.addWidget(self.tabw)

        # Crea tabs iniciales + demo
        self._add_tab("hunt", seed=True)
        self._add_tab("refill", seed=False)
        self._add_tab("123", seed=False)
        self._setup_demo_initial_state()

        # Puntero a la tabla actual (del tab activo)
        self.table: QTableWidget = self._tab_tables[self.tabw.currentIndex()]
        self.tabw.currentChanged.connect(self._on_tab_changed)

        # ---- Botonera inferior (sin Simular)
        btns = QHBoxLayout()
        self.btn_del   = QPushButton("Eliminar")
        self.btn_up    = QPushButton("Subir ▲")
        self.btn_down  = QPushButton("Bajar ▼")
        self.btn_clear = QPushButton("Limpiar")
        btns.addWidget(self.btn_del)
        btns.addWidget(self.btn_up)
        btns.addWidget(self.btn_down)
        btns.addStretch(1)
        btns.addWidget(self.btn_clear)
        left.addLayout(btns)

        # ---- Feedback de inicio
        self.lbl_next_start = QLabel("Inicio: —")
        self.lbl_next_start.setStyleSheet("color:#9cc9ff; font-size:12px; padding-left:2px;")
        left.addWidget(self.lbl_next_start)

        self.btn_del.clicked.connect(self._on_del)
        self.btn_clear.clicked.connect(self._on_clear)
        self.btn_up.clicked.connect(lambda: self._move_selected(-1))
        self.btn_down.clicked.connect(lambda: self._move_selected(+1))

        # -------- Columna derecha: Galería + Opciones --------
        right = QVBoxLayout()
        right.setContentsMargins(6, 10, 6, 6)
        right.setSpacing(8)

        title = QLabel("Icons")
        title.setStyleSheet("color:#8ac6ff; font-weight:bold;")
        right.addWidget(title)

        # Scroll: galería + opciones
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        container = QWidget()
        vbox_right = QVBoxLayout(container)
        l, t, r, b = GALLERY_MARG
        vbox_right.setContentsMargins(l, t, r, b)
        vbox_right.setSpacing(8)

        # --- (1) Galería de iconos ---
        gallery_widget = QWidget(container)
        grid = QGridLayout(gallery_widget)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(GALLERY_SPACE)

        for i, name in enumerate(GALLERY_WPS):
            img_path = (self.marcas_dir / f"{name}.png")
            item = _GalleryItem(name, img_path, THUMB_SIZE, parent=gallery_widget)
            item.clicked.connect(self._on_gallery_click)
            row, col = divmod(i, GALLERY_COLS)
            grid.addWidget(item, row, col)

        vbox_right.addWidget(gallery_widget)

        # --- (2) Opciones de Ruta ---
        opts_group = QGroupBox("Opciones de Ruta")
        form = QFormLayout(opts_group)
        form.setLabelAlignment(Qt.AlignLeft)

        def _compact(sb: QAbstractSpinBox, w=92, h=24):
            sb.setButtonSymbols(QAbstractSpinBox.NoButtons)
            sb.setFixedHeight(h)
            sb.setMaximumWidth(w)
            try:
                sb.setAlignment(Qt.AlignRight)
            except Exception:
                pass
            sb.setStyleSheet("QAbstractSpinBox{padding-right:4px;}")

        self.sp_wait_after = QDoubleSpinBox(opts_group)
        self.sp_wait_after.setDecimals(2)
        self.sp_wait_after.setSingleStep(0.05)
        self.sp_wait_after.setRange(0.0, 30.0)
        self.sp_wait_after.setValue(0.0)
        _compact(self.sp_wait_after)

        self.sp_wait_before = QDoubleSpinBox(opts_group)
        self.sp_wait_before.setDecimals(2)
        self.sp_wait_before.setSingleStep(0.05)
        self.sp_wait_before.setRange(0.0, 30.0)
        self.sp_wait_before.setValue(0.0)
        _compact(self.sp_wait_before)

        self.sp_lure_max = QSpinBox(opts_group)
        self.sp_lure_max.setRange(1, 999)
        self.sp_lure_max.setValue(10)
        _compact(self.sp_lure_max)

        self.sp_lure_pause = QDoubleSpinBox(opts_group)
        self.sp_lure_pause.setDecimals(2)
        shead = 0.1
        self.sp_lure_pause.setSingleStep(shead)
        self.sp_lure_pause.setRange(0.0, 30.0)
        self.sp_lure_pause.setValue(1.5)
        _compact(self.sp_lure_pause)

        self.sp_lure_resume = QDoubleSpinBox(opts_group)
        self.sp_lure_resume.setDecimals(2)
        self.sp_lure_resume.setSingleStep(0.1)
        self.sp_lure_resume.setRange(0.0, 30.0)
        self.sp_lure_resume.setValue(1.5)
        _compact(self.sp_lure_resume)

        self.sp_max_tries_wp = QSpinBox(opts_group)
        self.sp_max_tries_wp.setRange(1, 999)
        self.sp_max_tries_wp.setValue(30)
        _compact(self.sp_max_tries_wp)

        self.sp_sleep_after_click = QDoubleSpinBox(opts_group)
        self.sp_sleep_after_click.setDecimals(3)
        self.sp_sleep_after_click.setSingleStep(0.01)
        self.sp_sleep_after_click.setRange(0.0, 5.0)
        self.sp_sleep_after_click.setValue(0.05)
        _compact(self.sp_sleep_after_click)

        form.addRow("MAX_TRIES_PER_WP", self.sp_max_tries_wp)
        form.addRow("SLEEP_AFTER_CLICK", self.sp_sleep_after_click)
        form.addRow("WAIT_AFTER_ARRIVAL_S", self.sp_wait_after)
        form.addRow("WAIT_BEFORE_NEXT_WP_S", self.sp_wait_before)
        form.addRow("LURE_MAX_TRIES", self.sp_lure_max)
        form.addRow("LURE_PAUSE_SEC", self.sp_lure_pause)
        form.addRow("LURE_RESUME_SEC", self.sp_lure_resume)

        vbox_right.addWidget(opts_group)

        scroll.setWidget(container)
        right.addWidget(scroll)

        # ---- Mantener ancho mínimo del panel derecho
        item_w = THUMB_SIZE.width() + 26
        cols_w = (item_w * GALLERY_COLS) + GALLERY_SPACE * (GALLERY_COLS - 1)
        margins_w = l + r
        sidebar_w = cols_w + margins_w + 6

        right_wrap = QWidget()
        right_wrap.setLayout(right)
        right_wrap.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        right_wrap.setMinimumWidth(sidebar_w)

        left_wrap = QWidget()
        left_wrap.setLayout(left)

        root.addWidget(left_wrap, 1)
        root.addWidget(right_wrap, 0)

        # ---- Estado inicial de "Inicio: ..."
        self._reset_default_attach()  # por defecto primer tab/fila

    # ------------ Tab management ------------
    def _make_table(self) -> QTableWidget:
        tbl = QTableWidget(0, 3, self)
        tbl.setHorizontalHeaderLabels(["Etiqueta", "WP", "Acción"])
        tbl.verticalHeader().setVisible(False)
        tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        tbl.setSelectionMode(QAbstractItemView.ExtendedSelection)
        tbl.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked)
        tbl.setAlternatingRowColors(True)
        tbl.setShowGrid(True)
        tbl.setWordWrap(False)
        tbl.setColumnWidth(0, 220)   # etiqueta
        tbl.setColumnWidth(1, 46)    # icono WP
        tbl.setColumnWidth(2, 120)   # acción
        tbl.setIconSize(TABLE_ICON_SIZE)
        tbl.setContextMenuPolicy(Qt.CustomContextMenu)
        tbl.customContextMenuRequested.connect(lambda pos, t=tbl: self._on_context_menu_tab(t, pos))
        tbl.installEventFilter(self)  # para Delete/Backspace
        # Doble click: GOTO (en etiqueta) o ATTACH (solo en WP)
        tbl.itemDoubleClicked.connect(lambda it, t=tbl: self._on_item_double_clicked(t, it))
        # Selección → solo preview (no cambia attach)
        tbl.itemSelectionChanged.connect(lambda t=tbl: self._on_selection_preview(t))
        return tbl

    def _add_tab(self, name: str, seed: bool = False):
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(0, 0, 0, 0)
        table = self._make_table()
        v.addWidget(table)

        self._tab_tables.append(table)
        self.tabw.addTab(page, name)

        if seed:
            for wp in ("wp1", "wp2", "wp3", "wp4"):
                self._append_row(wp, "none", label="", table=table)

    def _on_tab_changed(self, idx: int):
        if 0 <= idx < len(self._tab_tables):
            self.table = self._tab_tables[idx]
        self._update_next_start_label()

    def _prompt_add_tab(self):
        base, ok = QInputDialog.getText(self, "Nuevo tab", "Nombre del tab:")
        if not ok:
            return
        name = (base or "").strip()
        if not name:
            return
        existing = {self.tabw.tabText(i).lower() for i in range(self.tabw.count())}
        orig = name
        n = 2
        while name.lower() in existing:
            name = f"{orig} {n}"
            n += 1
        self._add_tab(name, seed=False)
        self.tabw.setCurrentIndex(self.tabw.count() - 1)
        self._update_next_start_label()

    # --- Menú contextual barra de tabs ---
    def _on_tabbar_context_menu(self, pos: QPoint):
        bar = self.tabw.tabBar()
        idx = bar.tabAt(pos)
        if idx < 0:
            return

        menu = QMenu(self)

        act_rename = QAction(f"Renombrar tab '{self.tabw.tabText(idx)}'…", menu)
        act_rename.setData(idx)
        act_rename.triggered.connect(self._on_rename_tab_action)
        menu.addAction(act_rename)

        menu.addSeparator()

        act_del = QAction(f"Eliminar tab '{self.tabw.tabText(idx)}'…", menu)
        act_del.setEnabled(self.tabw.count() > 1)
        act_del.setData(idx)
        act_del.triggered.connect(self._on_delete_tab_action)
        menu.addAction(act_del)

        menu.exec(bar.mapToGlobal(pos))
    
    def _on_rename_tab_action(self):
        act = self.sender()
        if not isinstance(act, QAction):
            return
        idx = int(act.data())
        self._prompt_rename_tab(idx)

    def _on_delete_tab_action(self):
        act = self.sender()
        if not isinstance(act, QAction):
            return
        idx = int(act.data())
        self._delete_tab(idx)

    def _delete_tab(self, idx: int):
        if self.tabw.count() <= 1:
            QMessageBox.information(self, "No permitido", "Debe existir al menos un tab.")
            return
        tab_name = self.tabw.tabText(idx)
        table = self._tab_tables.pop(idx)
        page = self.tabw.widget(idx)
        self.tabw.removeTab(idx)
        table.deleteLater()
        page.deleteLater()
        # Si borré el tab donde estaba el attach → reset default
        att = self._get_attach()
        if att and att.get("tab") == tab_name:
            self._reset_default_attach()
        else:
            self._update_next_start_label()

    def _prompt_rename_tab(self, idx: int):
        old_name = self.tabw.tabText(idx)
        new_name, ok = QInputDialog.getText(self, "Renombrar tab", "Nuevo nombre:", text=old_name)
        if not ok:
            return

        new_name = (new_name or "").strip()
        if not new_name or new_name == old_name:
            return

        existing = {self.tabw.tabText(i).lower() for i in range(self.tabw.count()) if i != idx}
        if new_name.lower() in existing:
            QMessageBox.warning(self, "Nombre duplicado", f"Ya existe un tab llamado '{new_name}'.")
            return

        self._rename_tab(idx, old_name, new_name)

    def _rename_tab(self, idx: int, old_name: str, new_name: str):
        self.tabw.setTabText(idx, new_name)
        # Actualiza GOTO que apunten al tab renombrado
        for tbl in self._tab_tables:
            for r in range(tbl.rowCount()):
                it = tbl.item(r, 0)  # Etiqueta
                if not it:
                    continue
                gd = it.data(ROLE_GOTO)
                if isinstance(gd, dict) and gd.get("tab") == old_name:
                    new_gd = {"tab": new_name, "label": gd.get("label", "")}
                    it.setData(ROLE_GOTO, new_gd)
                    text = (it.text() or "")
                    if text.startswith("goto,"):
                        it.setText(f"goto,{new_name}:{new_gd['label']}")
                    it.setToolTip(f"GOTO → {new_name}:{new_gd['label']}")
        # Si el attach apuntaba al tab renombrado → actualizarlo
        att = self._get_attach()
        if att and att.get("tab") == old_name:
            self._set_attach(new_name, int(att.get("index", 0)))
        else:
            self._update_next_start_label()

    # ------------ Menú contextual (por tabla) ------------
    def _on_context_menu_tab(self, table: QTableWidget, pos: QPoint):
        self.table = table
        global_pos = table.viewport().mapToGlobal(pos)
        row_under = table.rowAt(pos.y())

        if row_under >= 0:
            if row_under not in [i.row() for i in table.selectedIndexes()]:
                table.selectRow(row_under)

        menu = QMenu(self)

        add_menu = QMenu("Añadir", menu)
        for i in range(1, 21):
            name = f"wp{i}"
            act = QAction(name, add_menu)
            act.triggered.connect(lambda _, n=name: self._context_add_named(n, row_under))
            add_menu.addAction(act)
        add_menu.addSeparator()
        for zname in ("zoomin", "zoomout"):
            act = QAction(zname, add_menu)
            act.triggered.connect(lambda _, n=zname: self._context_add_named(n, row_under, force_action="zoom"))
            add_menu.addAction(act)
        menu.addMenu(add_menu)

        # Configurar GOTO…
        goto_act = QAction("Configurar GOTO…", menu)
        goto_act.triggered.connect(lambda: self._ensure_goto_and_prompt(row_under))
        menu.addAction(goto_act)

        del_act = QAction("Eliminar fila(s)", menu)
        del_act.triggered.connect(lambda: self._on_del_table(table))
        del_act.setEnabled(self._has_any_selection_table(table))
        menu.addAction(del_act)

        menu.exec(global_pos)

    # ------------ GOTO & Attach ------------
    def _on_item_double_clicked(self, table: QTableWidget, item: QTableWidgetItem):
        """Doble click:
        - Columna 0 (Etiqueta): si acción es 'goto' → dialog GOTO.
        - Columna 1 (WP): fija ATTACH (único) a ese tab/fila.
        """
        if not item:
            return
        row = item.row()
        col = item.column()

        # Etiqueta → configurar GOTO si aplica
        if col == 0:
            cb = table.cellWidget(row, 2)
            if isinstance(cb, QComboBox) and cb.currentText().lower() == "goto":
                old = self.table
                self.table = table
                self._prompt_goto(row)
                self.table = old
            return

        # WP → fijar ATTACH global
        if col == 1:
            try:
                tab_index = self._tab_tables.index(table)
            except ValueError:
                return
            tab_name = self.tabw.tabText(tab_index)
            self._set_attach(tab_name, row)

    def _clear_all_selections(self, except_tab_index: int = -1):
        """Quita la selección de todas las tablas menos la indicada."""
        for i, tbl in enumerate(self._tab_tables):
            if i != except_tab_index:
                try:
                    tbl.clearSelection()
                except Exception:
                    pass

    def _wp_name_at(self, tab_name: str, row_index: int) -> str:
        idx = self._tab_index_by_name(tab_name)
        if idx == -1: 
            return ""
        tbl = self._tab_tables[idx]
        if 0 <= row_index < tbl.rowCount():
            it = tbl.item(row_index, 1)
            if it:
                name = it.data(Qt.UserRole)
                if not isinstance(name, str) or not name:
                    name = it.text() or ""
                return (name or "").strip()
        return ""

    def _get_attach(self) -> dict:
        prof = getattr(self.controller, "active_profile", None) or {}
        att = prof.get("ROUTE_ATTACH") or {}
        tab = (att.get("tab") or (self.tabw.tabText(0) if self.tabw.count() else "")).strip()
        try:
            idx = int(att.get("index", 0))
        except Exception:
            idx = 0
        return {"tab": tab, "index": max(0, idx)}

    def _set_attach(self, tab_name: str, row_index: int):
        """Fija el punto de arranque global (único) y limpia selecciones de otros tabs."""
        tab_index = self._tab_index_by_name(tab_name)
        if tab_index == -1:
            return
        row_index = max(0, int(row_index))

        # Selección visual SOLO en ese tab
        self.tabw.setCurrentIndex(tab_index)
        tbl = self._tab_tables[tab_index]
        self._clear_all_selections(except_tab_index=tab_index)
        if 0 <= row_index < tbl.rowCount():
            try:
                tbl.selectRow(row_index)
                item = tbl.item(row_index, 0)
                if item:
                    tbl.scrollToItem(item, QAbstractItemView.PositionAtCenter)
            except Exception:
                pass

        # Guardar a perfil activo + runtime_cfg
        if self.controller and hasattr(self.controller, "update_config"):
            self.controller.update_config({"ROUTE_ATTACH": {"tab": tab_name, "index": int(row_index)}})

        # Feedback “Inicio: …”
        self._update_next_start_label()

    def _update_next_start_label(self, selection_preview: QTableWidget | None = None):
        """Muestra 'Inicio: ...' con el attach actual; si hay selección, la muestra como tooltip."""
        att = self._get_attach()
        if att:
            tab = att.get("tab", "")
            idx = int(att.get("index", 0))
            wp = self._wp_name_at(tab, idx)
            self.lbl_next_start.setText(f"Inicio: {tab or '—'} · fila {idx+1 if tab else '—'} · {wp or '—'}")
            self.lbl_next_start.setToolTip("")
        else:
            self.lbl_next_start.setText("Inicio: —")
            self.lbl_next_start.setToolTip("")

        # Tooltip de selección (preview)
        if isinstance(selection_preview, QTableWidget):
            try:
                tab_index = self._tab_tables.index(selection_preview)
                tab_name = self.tabw.tabText(tab_index)
                row = selection_preview.currentRow()
                if row >= 0:
                    wp_name = self._wp_name_at(tab_name, row)
                    tip = f"Seleccionado: {tab_name} · fila {row+1} · {wp_name or '-'}"
                    self.lbl_next_start.setToolTip(tip)
            except Exception:
                pass

    def _reset_default_attach(self):
        """Primer tab + primera fila (si existen)."""
        if self.tabw.count() == 0:
            return
        # Buscar primer tab con filas, sino el 0
        chosen_tab = self.tabw.tabText(0)
        for i in range(self.tabw.count()):
            if self._tab_tables[i].rowCount() > 0:
                chosen_tab = self.tabw.tabText(i)
                break
        self._set_attach(chosen_tab, 0)

    # Pública para que MainWindow pueda llamarla al hacer STOP
    def reset_attach_to_default(self):
        self._reset_default_attach()

    def highlight_position(self, tab_name: str, row_idx: int):
        """
        Salta al tab y marca SOLO la fila indicada, limpiando selecciones previas
        en todos los tabs y centrando la vista en la fila.
        """
        idx = self._tab_index_by_name(tab_name)
        if idx == -1:
            return

        # Cambiar a ese tab y actualizar puntero a tabla actual
        if self.tabw.currentIndex() != idx:
            self.tabw.setCurrentIndex(idx)
        self.table = self._tab_tables[idx]

        # 1) Limpiar selección en TODOS los tabs
        for t in self._tab_tables:
            try:
                t.blockSignals(True)
                t.clearSelection()
            finally:
                t.blockSignals(False)

        # 2) Seleccionar la fila destino en el tab actual
        if 0 <= row_idx < self.table.rowCount():
            try:
                self.table.blockSignals(True)
                self.table.selectRow(row_idx)
                it = self.table.item(row_idx, 0)
                if it:
                    self.table.scrollToItem(it, QAbstractItemView.PositionAtCenter)
            finally:
                self.table.blockSignals(False)

    def _ensure_goto_and_prompt(self, row: int):
        if row is None or row < 0:
            return
        cb = self._combo_at(row)
        if not cb:
            return
        block = cb.blockSignals(True)
        if cb.findText("goto") < 0:
            cb.addItem("goto")
        cb.setCurrentText("goto")
        cb.blockSignals(block)
        self._prompt_goto(row)

    def _set_goto(self, row: int, tab: str, label: str):
        it = self.table.item(row, 0)  # Etiqueta
        if it:
            it.setData(ROLE_GOTO, {"tab": tab, "label": label})
            it.setText(f"goto,{tab}:{label}")
            it.setToolTip(f"GOTO → {tab}:{label}")

    def _get_goto(self, row: int) -> dict | None:
        it = self.table.item(row, 0)
        data = it.data(ROLE_GOTO) if it else None
        return data if isinstance(data, dict) else None

    def _clear_goto(self, row: int):
        it = self.table.item(row, 0)
        if it:
            it.setData(ROLE_GOTO, None)
            it.setToolTip("")

    def _prompt_goto(self, row: int):
        if row < 0:
            return
        text, ok = QInputDialog.getText(self, "Configurar GOTO", "Destino (tab:etiqueta):")
        if not ok:
            return
        text = (text or "").strip()
        if ":" not in text:
            QMessageBox.warning(self, "Formato inválido", "Usa: nombre_tab:etiqueta")
            return
        tab, label = [s.strip() for s in text.split(":", 1)]
        if not tab or not label:
            QMessageBox.warning(self, "Datos faltantes", "Completa tab y etiqueta.")
            return
        self._set_goto(row, tab, label)

    # ------------ Event filter (Delete/Backspace) ------------
    def eventFilter(self, obj, ev):
        if isinstance(obj, QTableWidget) and ev.type() == QEvent.KeyPress:
            if ev.key() in (Qt.Key_Delete, Qt.Key_Backspace):
                if obj.state() == QAbstractItemView.EditingState:
                    return False
                if self._has_any_selection_table(obj):
                    self._on_del_table(obj)
                    return True
        return super().eventFilter(obj, ev)

    # ------------ Helpers de tabla/filas ------------
    def _make_label_item(self, label: str) -> QTableWidgetItem:
        return QTableWidgetItem(label or "")

    def _get_label(self, row: int) -> str:
        it = self.table.item(row, 0)
        return (it.text() if it else "").strip()

    def _pix_for_name(self, name: str, table: QTableWidget | None = None) -> QPixmap:
        path = self.marcas_dir / f"{name}.png"
        if table is not None:
            w, h = table.iconSize().width(), table.iconSize().height()
        else:
            w, h = TABLE_ICON_SIZE.width(), TABLE_ICON_SIZE.height()
        if path.exists():
            src = QPixmap(str(path))
            if not src.isNull():
                return src.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        pm = QPixmap(w, h)
        pm.fill(QColor(24, 24, 24))
        p = QPainter(pm)
        p.fillRect(0, 0, w, h, QColor(20, 20, 20))
        p.setPen(QColor(160, 160, 160))
        p.drawText(0, 0, w, h, Qt.AlignCenter, "no img")
        p.end()
        return pm

    def _make_name_item(self, name: str, table: QTableWidget | None = None) -> QTableWidgetItem:
        item = QTableWidgetItem()
        item.setData(Qt.UserRole, name)
        item.setIcon(QIcon(self._pix_for_name(name, table)))
        item.setSizeHint(QSize(TABLE_ICON_SIZE.width() + 8, TABLE_ICON_SIZE.height() + 8))
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        return item

    def _get_name(self, row: int) -> str:
        it = self.table.item(row, 1)  # columna WP
        if not it:
            return ""
        name = it.data(Qt.UserRole)
        return name if isinstance(name, str) and name else (it.text() or "").strip()

    def _combo_at(self, row: int) -> QComboBox | None:
        w = self.table.cellWidget(row, 2)  # columna Acción
        return w if isinstance(w, QComboBox) else None

    # ------------ Inserción / borrado / movimiento ------------
    def _append_row(self, name: str, action: str = "none", label: str | None = None, table: QTableWidget | None = None):
        tbl = table or self.table
        self._insert_row_at(tbl.rowCount(), name, action, label, table=tbl)

    def _insert_row_at(self, row: int, name: str, action: str = "none", label: str | None = None, table: QTableWidget | None = None):
        tbl = table or self.table
        row = max(0, min(row, tbl.rowCount()))
        tbl.insertRow(row)

        it_label = self._make_label_item(label or "")
        tbl.setItem(row, 0, it_label)

        it_wp = self._make_name_item(name, table=tbl)
        tbl.setItem(row, 1, it_wp)
        tbl.setRowHeight(row, TABLE_ICON_SIZE.height() + 10)

        cb = QComboBox(tbl)
        cb.addItems(ACTIONS)
        if action and action not in ACTIONS:
            cb.addItem(action)
        cb.setCurrentText(action or "none")
        cb.currentTextChanged.connect(lambda text, r=row, t=tbl: self._on_action_changed(r, text, t))
        tbl.setCellWidget(row, 2, cb)

    def _on_action_changed(self, row: int, text: str, table: QTableWidget):
        if text.lower() == "goto":
            old = self.table
            self.table = table
            self._prompt_goto(row)
            self.table = old
        else:
            it = table.item(row, 0)
            if it:
                it.setData(ROLE_GOTO, None)
                it.setToolTip("")

    def _take_row(self, row: int):
        cb = self._combo_at(row)
        self.table.setCellWidget(row, 2, None)
        self.table.removeRow(row)
        return cb.currentText() if cb else "none"

    def _has_any_selection(self) -> bool:
        sel = self.table.selectionModel()
        return bool(sel and sel.hasSelection())

    def _has_any_selection_table(self, table: QTableWidget) -> bool:
        sel = table.selectionModel()
        return bool(sel and sel.hasSelection())

    def _on_del_table(self, table: QTableWidget):
        sel_model = table.selectionModel()
        if not sel_model or not sel_model.hasSelection():
            r = table.currentRow()
            if r < 0:
                QMessageBox.information(self, "Selecciona una fila", "Primero selecciona un waypoint.")
                return
            rows_to_delete = [r]
        else:
            rows_to_delete = sorted({idx.row() for idx in sel_model.selectedRows()}, reverse=True)

        after_focus_row = min(rows_to_delete[0], max(0, table.rowCount() - 1))
        for r in rows_to_delete:
            table.setCellWidget(r, 2, None)
            table.removeRow(r)

        if table.rowCount() > 0:
            table.selectRow(min(after_focus_row, table.rowCount() - 1))
        self._update_next_start_label()

    def _on_del(self):
        self._on_del_table(self.table)

    def _on_clear(self):
        while self.table.rowCount() > 0:
            self._take_row(0)
        self._update_next_start_label()

    def _move_selected(self, delta: int):
        if delta == 0 or self.table.rowCount() <= 1:
            return
        src = self.table.currentRow()
        if src < 0:
            return

        dst = src + delta
        if dst < 0 or dst >= self.table.rowCount():
            return

        label_src = self._get_label(src)
        label_dst = self._get_label(dst)
        name_src  = self._get_name(src)
        name_dst  = self._get_name(dst)

        cb_src = self._combo_at(src)
        cb_dst = self._combo_at(dst)
        action_src = cb_src.currentText() if cb_src else "none"
        action_dst = cb_dst.currentText() if cb_dst else "none"

        self.table.setItem(src, 0, self._make_label_item(label_dst))
        self.table.setItem(dst, 0, self._make_label_item(label_src))

        self.table.setItem(src, 1, self._make_name_item(name_dst, table=self.table))
        self.table.setItem(dst, 1, self._make_name_item(name_src, table=self.table))

        def _safe_set(cb: QComboBox | None, value: str):
            if not isinstance(cb, QComboBox):
                return
            if value and cb.findText(value) < 0:
                cb.addItem(value)
            cb.setCurrentText(value or "none")

        _safe_set(cb_src, action_dst)
        _safe_set(cb_dst, action_src)

        self.table.selectRow(dst)
        self.table.scrollToItem(self.table.item(dst, 0), QAbstractItemView.PositionAtCenter)
        self._update_next_start_label()

    # ------------------ Añadir desde galería / menú ------------------
    def _context_add_named(self, name: str, row_under: int, force_action: str | None = None):
        insert_at = self.table.rowCount()
        action = force_action if force_action else ("zoom" if name.startswith("zoom") else "none")
        self._insert_row_at(insert_at, name, action, label="")
        self.table.selectRow(insert_at)
        self.table.scrollToBottom()
        self._update_next_start_label()

    def _on_gallery_click(self, name: str):
        insert_at = self.table.rowCount()
        action = "zoom" if name.startswith("zoom") else "none"
        self._insert_row_at(insert_at, name, action, label="")
        self.table.selectRow(insert_at)
        self.table.scrollToBottom()
        self._update_next_start_label()

    # ------------------ PERFIL -> TABLA (multi-tab) ------------------
    def load_from_profile(self, profile: dict):
        route_tabs: Dict[str, Any] = profile.get("ROUTE_TABS") or {}

        if route_tabs:
            while self.tabw.count() > 0:
                self.tabw.removeTab(0)
            self._tab_tables.clear()

            for tab_name, data in route_tabs.items():
                self._add_tab(tab_name, seed=False)
                self.tabw.setCurrentIndex(self.tabw.count() - 1)
                self.table = self._tab_tables[-1]

                route   = data.get("ROUTE") or []
                actions = data.get("ROUTE_ACTIONS") or []
                labels  = data.get("ROUTE_LABELS") or []
                gotos   = data.get("ROUTE_GOTO") or []
                L = max(len(route), len(actions), len(labels), len(gotos))
                if len(route)   < L: route   = route   + [""] * (L - len(route))
                if len(actions) < L: actions = actions + ["none"] * (L - len(actions))
                if len(labels)  < L: labels  = labels  + [""] * (L - len(labels))
                if len(gotos)   < L: gotos   = gotos   + [""] * (L - len(gotos))

                for i in range(L):
                    name   = (str(route[i] or "").strip() or f"wp{i+1}")
                    action = str(actions[i] or "none").strip().lower()
                    label  = str(labels[i] or "").strip()
                    self._append_row(name, action, label=label)
                    g = str(gotos[i] or "").strip()
                    if g and ":" in g:
                        tab, lab = [s.strip() for s in g.split(":", 1)]
                        self._set_goto(self.table.rowCount() - 1, tab, lab)
                    elif label.lower().startswith("goto,") and ":" in label:
                        try:
                            _, rest = label.split(",", 1)
                            tab, lab = [s.strip() for s in rest.split(":", 1)]
                            self._set_goto(self.table.rowCount() - 1, tab, lab)
                        except Exception:
                            pass

            if self.tabw.count() > 0:
                self.tabw.setCurrentIndex(0)
                self.table = self._tab_tables[0]
        else:
            # Compat: claves planas -> tab actual
            route   = profile.get("ROUTE") or []
            actions = profile.get("ROUTE_ACTIONS") or []
            labels  = profile.get("ROUTE_LABELS") or []
            gotos   = profile.get("ROUTE_GOTO") or []
            L = max(len(route), len(actions), len(labels), len(gotos))
            if L != 0:
                if len(route)   < L: route   = route   + [""] * (L - len(route))
                if len(actions) < L: actions = actions + ["none"] * (L - len(actions))
                if len(labels)  < L: labels  = labels  + [""] * (L - len(labels))
                if len(gotos)   < L: gotos   = gotos   + [""] * (L - len(gotos))

                while self.table.rowCount() > 0:
                    self._take_row(0)

                for i in range(L):
                    name   = (str(route[i] or "").strip() or f"wp{i+1}")
                    action = str(actions[i] or "none").strip().lower()
                    label  = str(labels[i] or "").strip()
                    self._append_row(name, action, label=label)
                    g = str(gotos[i] or "").strip()
                    if g and ":" in g:
                        tab, lab = [s.strip() for s in g.split(":", 1)]
                        self._set_goto(self.table.rowCount() - 1, tab, lab)
                    elif label.lower().startswith("goto,") and ":" in label:
                        try:
                            _, rest = label.split(",", 1)
                            tab, lab = [s.strip() for s in rest.split(":", 1)]
                            self._set_goto(self.table.rowCount() - 1, tab, lab)
                        except Exception:
                            pass

        # Opciones de ruta
        try:
            if "WAIT_AFTER_ARRIVAL_S" in profile:
                self.sp_wait_after.setValue(float(profile.get("WAIT_AFTER_ARRIVAL_S", 0.0)))
            if "WAIT_BEFORE_NEXT_WP_S" in profile:
                self.sp_wait_before.setValue(float(profile.get("WAIT_BEFORE_NEXT_WP_S", 0.0)))

            if "LURE_MAX_TRIES" in profile:
                self.sp_lure_max.setValue(int(profile.get("LURE_MAX_TRIES", 10)))
            if "LURE_PAUSE_SEC" in profile:
                self.sp_lure_pause.setValue(float(profile.get("LURE_PAUSE_SEC", 1.5)))
            if "LURE_RESUME_SEC" in profile:
                self.sp_lure_resume.setValue(float(profile.get("LURE_RESUME_SEC", 1.5)))

            if "MAX_TRIES_PER_WP" in profile:
                self.sp_max_tries_wp.setValue(int(profile.get("MAX_TRIES_PER_WP", 30)))
            if "SLEEP_AFTER_CLICK" in profile:
                self.sp_sleep_after_click.setValue(float(profile.get("SLEEP_AFTER_CLICK", 0.05)))
        except Exception:
            pass

        # Si el perfil trae attach, úsalo; si no, default
        att = {}
        try:
            ap = getattr(self.controller, "active_profile", {}) or {}
            att = ap.get("ROUTE_ATTACH") or profile.get("ROUTE_ATTACH") or {}
        except Exception:
            pass
        if isinstance(att, dict) and att.get("tab") in [self.tabw.tabText(i) for i in range(self.tabw.count())]:
            self._set_attach(att.get("tab"), int(att.get("index", 0)))
        else:
            self._reset_default_attach()

    # ------------------ TABLA -> PERFIL (multi-tab) ------------------
    def to_profile_patch(self) -> dict:
        route_tabs: Dict[str, Any] = {}
        for idx, table in enumerate(self._tab_tables):
            tab_name = self.tabw.tabText(idx)
            route: List[str] = []
            actions: List[str] = []
            labels: List[str] = []
            gotos:  List[str] = []

            old_table = self.table
            self.table = table
            for r in range(table.rowCount()):
                route.append(self._get_name(r) or f"wp{r+1}")
                cb = self._combo_at(r)
                actions.append(cb.currentText().strip().lower() if cb else "none")
                labtxt = self._get_label(r)
                labels.append(labtxt)

                gd = self._get_goto(r)
                if not gd and isinstance(labtxt, str) and labtxt.lower().startswith("goto,") and ":" in labtxt:
                    try:
                        _, rest = labtxt.split(",", 1)
                        gtab, glabel = [s.strip() for s in rest.split(":", 1)]
                        gd = {"tab": gtab, "label": glabel}
                    except Exception:
                        gd = None
                gotos.append(f"{gd['tab']}:{gd['label']}" if gd else "")
            self.table = old_table

            route_tabs[tab_name] = {
                "ROUTE": route,
                "ROUTE_ACTIONS": actions,
                "ROUTE_LABELS": labels,
                "ROUTE_GOTO": gotos,
            }

        cur_idx = self.tabw.currentIndex()
        cur_name = self.tabw.tabText(cur_idx)
        cur = route_tabs.get(cur_name, {"ROUTE": [], "ROUTE_ACTIONS": [], "ROUTE_LABELS": [], "ROUTE_GOTO": []})

        patch = {
            "ROUTE_TABS": route_tabs,
            "ROUTE": cur["ROUTE"],
            "ROUTE_ACTIONS": cur["ROUTE_ACTIONS"],
            "ROUTE_LABELS": cur["ROUTE_LABELS"],
            "ROUTE_GOTO": cur["ROUTE_GOTO"],
            "ROUTE_ACTIVE_TAB": cur_name,
        }

        # ---- Guardar opciones de ruta
        patch.update({
            "WAIT_AFTER_ARRIVAL_S": float(self.sp_wait_after.value()),
            "WAIT_BEFORE_NEXT_WP_S": float(self.sp_wait_before.value()),
            "LURE_MAX_TRIES": int(self.sp_lure_max.value()),
            "LURE_PAUSE_SEC": float(self.sp_lure_pause.value()),
            "LURE_RESUME_SEC": float(self.sp_lure_resume.value()),
            "MAX_TRIES_PER_WP": int(self.sp_max_tries_wp.value()),
            "SLEEP_AFTER_CLICK": float(self.sp_sleep_after_click.value()),
        })

        # También incluimos el attach actual en el patch
        att = self._get_attach()
        if att:
            patch["ROUTE_ATTACH"] = {"tab": att.get("tab"), "index": int(att.get("index", 0))}

        return patch

    # ------------------ DEMO inicial ------------------
    def _setup_demo_initial_state(self):
        idx_123 = self._tab_index_by_name("123")
        if idx_123 != -1:
            self.tabw.setCurrentIndex(idx_123)
            self.table = self._tab_tables[idx_123]
            self._append_row("wp7", "none", label="")
            self._append_row("wp8", "none", label="here")
            self._append_row("wp9", "none", label="")

        idx_refill = self._tab_index_by_name("refill")
        if idx_refill != -1:
            self.tabw.setCurrentIndex(idx_refill)
            self.table = self._tab_tables[idx_refill]
            self._append_row("wp1", "none", label="")
            self._append_row("wp2", "none", label="")
            row = self.table.rowCount()
            self._append_row("wp3", "none", label="")
            cb = self._combo_at(row)
            if cb:
                block = cb.blockSignals(True)
                cb.setCurrentText("goto")
                cb.blockSignals(block)
            self._set_goto(row, "123", "here")

        idx_hunt = self._tab_index_by_name("hunt")
        if idx_hunt != -1:
            self.tabw.setCurrentIndex(idx_hunt)
            self.table = self._tab_tables[idx_hunt]

    def _tab_index_by_name(self, name: str) -> int:
        for i in range(self.tabw.count()):
            if self.tabw.tabText(i) == name:
                return i
        return -1
    
    def find_row_by_wp(self, tab_name: str, wp_name: str) -> int | None:
        """
        Devuelve el índice de fila cuyo WP (columna 1) coincide con 'wp_name'
        dentro del tab 'tab_name'. Si no existe, devuelve None.
        """
        idx = self._tab_index_by_name(tab_name)
        if idx == -1:
            return None
        tbl = self._tab_tables[idx]
        target = (wp_name or "").strip().lower()
        for r in range(tbl.rowCount()):
            it = tbl.item(r, 1)
            if not it:
                continue
            name = it.data(Qt.UserRole)
            if not isinstance(name, str) or not name:
                name = it.text() or ""
            if (name or "").strip().lower() == target:
                return r
        return None

    # ------------------ Selección: solo preview ------------------
    def _on_selection_preview(self, table: QTableWidget):
        # Solo preview visual; el ATTACH real se muestra en lbl_next_start
        self._update_next_start_label(selection_preview=table)
