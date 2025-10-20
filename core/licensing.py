# core/licensing.py
from __future__ import annotations

import hashlib
import platform
import secrets
import time
import uuid
from typing import Any, Dict, Tuple

import pyrebase
from core.firebase_config import FIREBASE_CONFIG


# ------------------ Firebase helpers ------------------
def _firebase():
    return pyrebase.initialize_app(FIREBASE_CONFIG)


def sign_in(email: str, password: str) -> Tuple[str, str, Dict[str, Any]]:
    """
    Inicia sesión con email/password y devuelve:
      - uid (str)
      - id_token (str)
      - state (dict): { refreshToken, auth, db }
    """
    fb = _firebase()
    auth = fb.auth()
    user = auth.sign_in_with_email_and_password(email, password)
    info = auth.get_account_info(user["idToken"])
    uid = info["users"][0]["localId"]
    return uid, user["idToken"], {
        "refreshToken": user["refreshToken"],
        "auth": auth,
        "db": fb.database(),
    }


def refresh_id_token(state: Dict[str, Any]) -> str:
    """
    Renueva el idToken usando refreshToken (útil si corre muchas horas).
    Actualiza el refreshToken dentro de state y devuelve el nuevo idToken.
    """
    auth = state["auth"]
    rtok = state["refreshToken"]
    refreshed = auth.refresh(rtok)
    state["refreshToken"] = refreshed["refreshToken"]
    return refreshed["idToken"]


# ------------------ Utilidades de licencia ------------------
def compute_expires_at(days: int) -> int:
    """Epoch (segundos) dentro de 'days' días a partir de ahora."""
    return int(time.time()) + int(days) * 86400


def _normalize_expires(expires_at: int | float | None) -> int:
    """
    Normaliza expiresAt a segundos:
    - Si viene en milisegundos (>= 1e12), lo divide entre 1000.
    - Si viene None o inválido, devuelve 0.
    """
    try:
        v = int(expires_at or 0)
    except Exception:
        return 0
    return v // 1000 if v >= 10**12 else v


def check_license(db, uid: str, id_token: str, grace_s: int = 60) -> Tuple[bool, str, int, str]:
    """
    Verifica la licencia en Realtime DB: licenses/{uid}
    Devuelve: ok, msg, remaining_days, plan
    """
    rec = db.child("licenses").child(uid).get(id_token).val()
    if not rec:
        return False, "No existe licencia para este usuario.", 0, ""

    if not bool(rec.get("active")):
        return False, "Licencia inactiva.", 0, rec.get("plan", "unknown")

    expires_at = _normalize_expires(rec.get("expiresAt", 0))
    now = int(time.time())

    if now + grace_s >= expires_at:
        return False, "Licencia expirada.", 0, rec.get("plan", "unknown")

    plan = rec.get("plan", "unknown")
    remaining_days = max(0, (expires_at - now) // 86400)
    return True, f"OK — plan: {plan} | días restantes: {remaining_days}", remaining_days, plan


def check_license_details(db, uid: str, id_token: str, grace_s: int = 60) -> Tuple[bool, Dict[str, Any], str]:
    """
    Versión estructurada para usar desde app.py.
    Devuelve:
      - ok (bool)
      - details (dict): {active, plan, expires_at, days_remaining, notes}
      - msg (str amigable)
    """
    rec = db.child("licenses").child(uid).get(id_token).val()
    if not rec:
        return False, {}, "No existe licencia para este usuario."

    active = bool(rec.get("active"))
    plan = rec.get("plan", "unknown")
    notes = rec.get("notes", "")
    expires_at = _normalize_expires(rec.get("expiresAt", 0))
    now = int(time.time())
    days_remaining = max(0, (expires_at - now) // 86400)

    if not active:
        return False, {
            "active": active,
            "plan": plan,
            "expires_at": expires_at,
            "days_remaining": days_remaining,
            "notes": notes,
        }, "Licencia inactiva."

    if now + grace_s >= expires_at:
        return False, {
            "active": active,
            "plan": plan,
            "expires_at": expires_at,
            "days_remaining": 0,
            "notes": notes,
        }, "Licencia expirada."

    msg = f"OK — plan: {plan} | días restantes: {days_remaining}"
    details = {
        "active": active,
        "plan": plan,
        "expires_at": expires_at,
        "days_remaining": days_remaining,
        "notes": notes,
    }
    return True, details, msg


# ------------------ Huella de dispositivo ------------------
def compute_device_id() -> str:
    """
    Genera un identificador estable por equipo.
    Combina hostname + MAC + sistema y lo hashea (no guarda datos crudos).
    """
    host = platform.node()
    mac = uuid.getnode()  # int
    plat = f"{platform.system()}|{platform.release()}|{platform.version()}"
    raw = f"{host}|{mac}|{plat}".encode("utf-8", errors="ignore")
    return hashlib.sha256(raw).hexdigest()[:32]  # 32 hex chars


# ------------------ Single-login (sessions/{uid}) ------------------
# --- Single-login helpers (versión robusta de rutas) ---
import secrets
import time

def acquire_session(
    db,
    uid: str,
    id_token: str,
    device_id: str,
    device_name: str,
    timeout_s: int = 120,
    strict_single: bool = True,
):
    """
    Intenta tomar la sesión exclusiva del usuario.

    - Si strict_single=True: bloquea SIEMPRE si ya hay una sesión activa, aunque sea el MISMO device.
    - Si strict_single=False: solo bloquea si la sesión activa pertenece a OTRO device.

    Devuelve:
      (False, mensaje) si no puede tomar la sesión.
      (True, session_token) si pudo tomarla (crea/actualiza sessions/{uid}).
    """
    now = int(time.time())

    sess_base = db.child(f"sessions/{uid}")

    # Lee sesión actual (si falla por token vencido, el caller hará refresh y reintentará)
    try:
        current = sess_base.get(id_token).val() or {}
    except Exception:
        current = {}

    if current:
        last = int(current.get("lastHeartbeat", 0))
        active = (now - last) < int(timeout_s)

        if active:
            # Si queremos 1 sola instancia global, bloquea siempre
            if strict_single:
                name = current.get("deviceName", "otro equipo")
                secs = now - last
                return False, f"Cuenta en uso por {name} (hace {secs}s). Intenta más tarde."

            # Modo laxo: solo bloquea si es OTRO device
            other_device = current.get("deviceId") and current.get("deviceId") != device_id
            if other_device:
                name = current.get("deviceName", "otro equipo")
                secs = now - last
                return False, f"Cuenta en uso por {name} (hace {secs}s). Intenta más tarde."

    # Tomar/pisar sesión: escribe campo por campo con rutas completas
    session_token = secrets.token_hex(16)
    try:
        db.child(f"sessions/{uid}/deviceId").set(device_id, id_token)
        db.child(f"sessions/{uid}/deviceName").set(device_name, id_token)
        db.child(f"sessions/{uid}/sessionToken").set(session_token, id_token)
        db.child(f"sessions/{uid}/lastHeartbeat").set(now, id_token)
    except Exception as e:
        raise e

    return True, session_token


def heartbeat(db, uid: str, id_token: str, session_token: str, timeout_s: int = 120) -> bool:
    """
    Mantiene viva la sesión. False si no existe, token no coincide o está expirada.
    """
    now = int(time.time())
    sess_base = db.child(f"sessions/{uid}")

    try:
        curr = sess_base.get(id_token).val()
    except Exception:
        return False

    if not curr:
        return False

    if str(curr.get("sessionToken")) != str(session_token):
        return False

    last = int(curr.get("lastHeartbeat", 0))
    if (now - last) >= int(timeout_s):
        return False  # expirada

    try:
        db.child(f"sessions/{uid}/lastHeartbeat").set(now, id_token)
    except Exception:
        return False

    return True


def release_session(db, uid: str, id_token: str, session_token: str) -> None:
    """
    Libera la sesión solo si el token coincide (evita borrar sesiones de otros).
    """
    sess_ref = db.child("sessions").child(uid)
    try:
        curr = sess_ref.get(id_token).val()
        if curr and str(curr.get("sessionToken")) == str(session_token):
            sess_ref.remove(id_token)
    except Exception:
        pass

# === Helpers de UX (mensajes legibles) ===
def friendly_auth_error(exc: Exception) -> str:
    """
    Convierte errores crudos de pyrebase/Firebase en mensajes amigables.
    """
    s = str(exc) or ""
    S = s.upper()
    if "INVALID_LOGIN_CREDENTIALS" in S or "EMAIL_NOT_FOUND" in S or "INVALID_PASSWORD" in S:
        return "Email o contraseña inválidos."
    if "USER_DISABLED" in S:
        return "Tu cuenta está deshabilitada."
    if "TOO_MANY_ATTEMPTS_TRY_LATER" in S or "TOO MANY" in S:
        return "Demasiados intentos. Intenta más tarde."
    if "NETWORK" in S or "CONNECTION" in S or "TIMEOUT" in S:
        return "No hay conexión. Verifica tu internet."
    # genérico
    return "No se pudo iniciar sesión. Revisa tus datos o tu conexión."

# === Estado global de sesión activa (para reutilizarla) ===
from dataclasses import dataclass
import threading

@dataclass
class ActiveSession:
    uid: str = ""
    id_token: str = ""
    refresh_token: str = ""
    db: object = None
    session_token: str = ""
    device_id: str = ""
    device_name: str = ""

_ACTIVE = ActiveSession()
_HB_THREAD_STARTED = False
_HB_LOCK = threading.Lock()

def set_active_session(uid, id_token, refresh_token, db, session_token, device_id, device_name):
    global _ACTIVE
    _ACTIVE = ActiveSession(
        uid=uid, id_token=id_token, refresh_token=refresh_token,
        db=db, session_token=session_token, device_id=device_id, device_name=device_name
    )

def get_active_session() -> ActiveSession:
    return _ACTIVE

def mark_heartbeat_thread_started():
    global _HB_THREAD_STARTED
    with _HB_LOCK:
        if not _HB_THREAD_STARTED:
            _HB_THREAD_STARTED = True
            return True
        return False
