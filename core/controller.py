# core/controller.py
from __future__ import annotations
from pathlib import Path
import json
import os
import subprocess
from typing import Dict, Any, List, Tuple, Optional
import sys

class Controller:
    """
    Orquestador de la GUI:
    - Gestiona perfil activo
    - Lanza main.py con un runtime_cfg.py generado desde el perfil
    - Modela estado (running/paused/threads) para los LEDs
    """

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir: Path = Path(base_dir or Path.cwd()).resolve()
        self.config_manager = None  # inyectado desde app.py
        self.active_profile: Dict[str, Any] = {}
        self.active_profile_name: str = ""
        self._logs: List[str] = []

        self.state: Dict[str, Any] = {
            "running": False,
            "paused": False,
            "profile_name": "",
            "threads": {
                "cavebot": False,
                "healing": False,
                "food": False,
                "anti_paralyze": False,
            },
            "creatures": 0,
            "red": 0,
        }

        self._last_profile_file = self.base_dir / "profiles" / "_last_profile.txt"
        self._child: Optional[subprocess.Popen] = None
        self._ensure_dirs()

    # ---------------------- utils base ----------------------
    def _ensure_dirs(self):
        (self.base_dir / "profiles").mkdir(parents=True, exist_ok=True)

    def log(self, msg: str):
        self._logs.append(msg)

    def pop_logs(self) -> List[str]:
        out, self._logs = self._logs, []
        return out

    # ---------------------- estado ----------------------
    def get_state(self) -> Dict[str, Any]:
        return dict(self.state)

    # ---------------------- perfiles ----------------------
    def _remember_last_profile(self, name: str):
        try:
            self._last_profile_file.write_text(name.strip(), encoding="utf-8")
        except Exception:
            pass

    def get_last_profile_name(self) -> str:
        try:
            return self._last_profile_file.read_text(encoding="utf-8").strip()
        except Exception:
            return ""

    def load_profile_from_disk(self, name_or_stem: str) -> Dict[str, Any]:
        if self.config_manager:
            p = self.config_manager.profiles_dir / f"{name_or_stem}.json"
            ok, data, err = self.config_manager.load_profile(p)
            if not ok:
                raise RuntimeError(err or f"No se pudo cargar {p.name}")
            return data

        p = self.base_dir / "profiles" / f"{name_or_stem}.json"
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)

    # ---------------------- config caliente ----------------------
    def update_config(self, patch: Dict[str, Any]):
        if not isinstance(patch, dict):
            return
        self.active_profile = {**(self.active_profile or {}), **patch}
        self.log(f"[Controller] Config actualizada ({len(patch)} clave/s).")

    # ---------------------- helpers de lanzamiento ----------------------
    def _compute_threads_from_profile(self, prof: Dict[str, Any]) -> Dict[str, bool]:
        def _is_set(key: str) -> bool:
            v = prof.get(key, "")
            return bool(str(v).strip())

        healing_on = _is_set("HK_HIGH_HEALING") or _is_set("HK_LOW_HEALING") or _is_set("HK_MANA_POTION")
        food_on    = _is_set("HK_FOOD")
        anti_on    = _is_set("HK_REMOVE_PARALYZE")

        return {
            "cavebot": True,             # siempre vivo; arranca en PAUSE
            "healing": healing_on,
            "food": food_on,
            "anti_paralyze": anti_on,
        }

    def _write_runtime_cfg(self, prof: Dict[str, Any]) -> Path:
        """
        Escribe runtime_cfg.py en la raíz del proyecto.
        Normaliza claves conocidas de minúsculas -> MAYÚSCULAS para que main.py las lea.
        Si existen ambas variantes, la minúscula sobreescribe a la MAYÚSCULA.
        """
        # Mapa de normalización para opciones de ruta
        keymap = {
            "wait_after_arrival_s": "WAIT_AFTER_ARRIVAL_S",
            "wait_before_next_wp_s": "WAIT_BEFORE_NEXT_WP_S",
            "lure_max_tries": "LURE_MAX_TRIES",
            "lure_pause_sec": "LURE_PAUSE_SEC",
            "lure_resume_sec": "LURE_RESUME_SEC",
            "max_tries_per_wp": "MAX_TRIES_PER_WP",
            "sleep_after_click": "SLEEP_AFTER_CLICK",
        }

        # 1) Copiamos y normalizamos claves
        normalized: Dict[str, Any] = {}
        for k, v in prof.items():
            nk = keymap.get(k, k)  # si es minúscula conocida -> a MAYÚSCULA
            normalized[nk] = v     # si luego aparece la minúscula, pisa a la mayúscula previa

        # 2) Escribimos el archivo
        dst = self.base_dir / "runtime_cfg.py"
        lines: list[str] = [
            "# === Archivo auto-generado por la GUI ===",
            "from __future__ import annotations",
            "",
        ]

        # Orden estable (solo cosmético)
        for k in sorted(normalized.keys()):
            try:
                lines.append(f"{k} = {repr(normalized[k])}")
            except Exception:
                # último recurso, stringify
                lines.append(f"{k} = {repr(str(normalized[k]))}")

        content = "\n".join(lines) + "\n"
        dst.write_text(content, encoding="utf-8")

        self.log(f"[Controller] runtime_cfg.py escrito ({dst}).")
        return dst

    def _spawn_main(self) -> None:
        """
        Lanza main.py sin búfer (-u + PYTHONUNBUFFERED) para que los prints lleguen
        a la GUI al instante. Además forzamos UTF-8.
        """
        try:
            if self._child and self._child.poll() is None:
                return
        except Exception:
            pass

        py = os.environ.get("PYTHON_EXE") or sys.executable or "python"
        main_py = str(self.base_dir / "main.py")
        env = dict(os.environ)
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUNBUFFERED"] = "1"  # <- clave

        self._child = subprocess.Popen(
            [py, "-u", main_py],               # <- -u clave
            cwd=str(self.base_dir),
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,                         # intenta line-buffering
        )

        import threading
        def _tail():
            try:
                for line in self._child.stdout:
                    if not line:
                        break
                    self.log(line.rstrip("\n\r"))
            except Exception as e:
                self.log(f"[Controller] tail error: {e}")

        threading.Thread(target=_tail, daemon=True).start()
        self.log("[Controller] main.py lanzado. Arranca en PAUSA SUAVE.")

    # ---------------------- run/pausa/stop ----------------------
    def start(self, profile: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Arranca en PAUSA SUAVE.
        Global ON, Cavebot LED 'paused', Healing/Food/Anti según hotkeys.
        La GUI puede haber escrito runtime_cfg.py justo antes de llamarnos.
        Si fue así, saltamos la escritura aquí para no 'resetear' opciones.
        """
        try:
            if profile:
                self.active_profile = dict(profile)
            self.active_profile_name = self.active_profile.get("profile_name", self.active_profile_name) or "perfil"

            # Estado inicial
            self.state["running"] = True
            self.state["paused"]  = True
            self.state["profile_name"] = self.active_profile_name
            self.state["threads"] = self._compute_threads_from_profile(self.active_profile)

            # Recordar último perfil
            name_for_memory = self.active_profile_name
            if self.config_manager and getattr(self.config_manager, "active_profile_path", None):
                try:
                    name_for_memory = Path(self.config_manager.active_profile_path).stem
                except Exception:
                    pass
            self._remember_last_profile(name_for_memory)

            # 1) runtime_cfg desde el perfil SOLO si la GUI no lo acaba de escribir
            skip_write = bool(getattr(self, "_skip_runtime_write", False))
            if not skip_write:
                self._write_runtime_cfg(self.active_profile)
            else:
                # Consumir el flag (solo salta una vez)
                try:
                    delattr(self, "_skip_runtime_write")
                except Exception:
                    try:
                        self._skip_runtime_write = False
                    except Exception:
                        pass

            # 2) lanzar main.py con UTF-8
            self._spawn_main()

            self.log("[Controller] Start: RUN (paused=TRUE). Presiona HOME para correr cavebot.")
            return True, ""
        except Exception as e:
            return False, str(e)

    def pause(self):
        if not self.state["running"]:
            return
        self.state["paused"] = True
        self.log("[Controller] Pausa suave activada.")

    def resume(self):
        if not self.state["running"]:
            return
        self.state["paused"] = False
        self.log("[Controller] Reanudado (RUN).")

    def stop(self):
        # Estado base
        self.state["running"] = False
        self.state["paused"]  = False
        self.state["threads"] = {k: False for k in self.state["threads"].keys()}

        # Terminar el main si sigue vivo
        try:
            if self._child and self._child.poll() is None:
                self._child.terminate()
        except Exception:
            pass

        # IMPORTANTE:
        # No volvemos a escribir runtime_cfg.py aquí para NO pisar
        # los valores de opciones de ruta guardados con Ctrl+S.
        # Solo limpiamos el attach en memoria para que el próximo start
        # arranque desde el inicio si el usuario no adjunta una fila.
        try:
            if isinstance(self.active_profile, dict):
                self.active_profile.pop("ROUTE_ATTACH", None)
                # ¡OJO! No llamar a _write_runtime_cfg aquí.
        except Exception:
            pass

        self.log("[Controller] Stop.")
