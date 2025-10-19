# core/config_manager.py
from __future__ import annotations
from pathlib import Path
import json
from typing import Any, Dict, List, Tuple

class ConfigManager:
    def __init__(self, base_dir: Path | None = None):
        self.base_dir = Path(base_dir or Path.cwd())
        self.config_dir = self.base_dir / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Carpeta sugerida para perfiles
        self.profiles_dir = self.base_dir / "profiles"
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

        self.active_profile_path: Path | None = None

    # --- Load ---
    def load_profile(self, path: Path) -> Tuple[bool, Dict[str, Any] | None, str | None]:
        try:
            p = Path(path)
            with p.open("r", encoding="utf-8") as f:
                data = json.load(f)
            self.active_profile_path = p
            return True, data, None
        except Exception as e:
            return False, None, str(e)

    # --- Save to explicit path ---
    def save_profile(self, path: Path, data: Dict[str, Any]) -> Tuple[bool, str | None]:
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            with p.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.active_profile_path = p
            return True, None
        except Exception as e:
            return False, str(e)

    # --- Save to last loaded/saved path ---
    def save_current(self, data: Dict[str, Any]) -> Tuple[bool, str | None]:
        if not self.active_profile_path:
            return False, "No hay un archivo de destino activo (usa 'Guardar como…')."
        return self.save_profile(self.active_profile_path, data)

    # --- Validaciones opcionales (warnings en consola GUI) ---
    def validate_profile_images(self, data: Dict[str, Any]) -> List[str]:
        warnings: List[str] = []
        marcas = self.base_dir / "marcas"

        # Mana / health potion icons (si el usuario quiere revisar)
        mana_img = str(data.get("POTION_CHECK_MANA_IMG") or "").strip()
        health_img = str(data.get("POTION_CHECK_HEALTH_IMG") or "").strip()
        for fname in (mana_img, health_img):
            if fname:
                fp = marcas / fname
                if not fp.exists():
                    warnings.append(f"[WARN] Imagen no encontrada: {fp}")

        # Waypoint icons (si usas galería wp*.png)
        route_tabs = data.get("ROUTE_TABS") or {}
        used_icons = set()
        for tabname, tabdata in route_tabs.items():
            for nm in (tabdata or {}).get("ROUTE", []) or []:
                nm = (nm or "").strip()
                if nm:
                    used_icons.add(nm + ".png")
        for img in sorted(used_icons):
            fp = marcas / img
            if not fp.exists():
                warnings.append(f"[WARN] Falta icono de WP: {fp}")

        return warnings
