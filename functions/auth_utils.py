# functions/auth_utils.py
from __future__ import annotations
from typing import Tuple
import json
import traceback
from pathlib import Path

def map_firebase_error_code(code: str) -> str:
    """
    Traduce el 'error.message' que devuelve Firebase a un texto para el usuario.
    """
    code = (code or "").upper()
    mapping = {
        "INVALID_LOGIN_CREDENTIALS": "Correo o contraseña incorrectos.",
        "INVALID_PASSWORD": "Correo o contraseña incorrectos.",
        "EMAIL_NOT_FOUND": "No existe una cuenta con ese correo.",
        "USER_DISABLED": "Esta cuenta fue deshabilitada.",
        "TOO_MANY_ATTEMPTS_TRY_LATER": "Demasiados intentos. Intenta más tarde.",
        "OPERATION_NOT_ALLOWED": "Inicio de sesión no permitido para este proyecto.",
        "INVALID_EMAIL": "El correo no tiene un formato válido.",
    }
    return mapping.get(code, "No pudimos iniciar sesión. Verifica tus datos e inténtalo nuevamente.")

def parse_pyrebase_error(exc: Exception) -> Tuple[str, str]:
    """
    Devuelve (mensaje_para_usuario, detalle_tecnico).

    Si viene de requests.HTTPError, intenta leer JSON:
      {'error': {'message': 'INVALID_LOGIN_CREDENTIALS', ...}}
    """
    user_msg = "No pudimos iniciar sesión. Verifica tus datos e inténtalo nuevamente."
    tech = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))

    resp = getattr(exc, "response", None)
    if resp is not None:
        try:
            data = resp.json()
            code = (data.get("error") or {}).get("message") or ""
            user_msg = map_firebase_error_code(code)
            tech = json.dumps(data, ensure_ascii=False, indent=2)
        except Exception:
            # Si no es JSON, dejamos mensaje genérico y stack.
            pass
    return user_msg, tech

def log_auth_error(tech_detail: str, logfile: Path = Path("auth_error.log")) -> None:
    try:
        logfile.write_text(tech_detail, encoding="utf-8")
    except Exception:
        pass
