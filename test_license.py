import time
from getpass import getpass

import pyrebase
from core.firebase_config import FIREBASE_CONFIG

def sign_in(email: str, password: str):
    firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
    auth = firebase.auth()
    user = auth.sign_in_with_email_and_password(email, password)
    info = auth.get_account_info(user["idToken"])
    uid = info["users"][0]["localId"]
    return uid, user["idToken"], firebase.database()

def check_license(db, uid: str, id_token: str, grace_s: int = 60):
    # Lee el nodo autenticado
    rec = db.child("licenses").child(uid).get(id_token).val()
    if not rec:
        return False, "No existe licencia para este usuario."

    active = bool(rec.get("active"))
    if not active:
        return False, "Licencia inactiva."

    # Normaliza expiresAt (segundos vs milisegundos)
    try:
        expires_at = int(rec.get("expiresAt", 0))
    except Exception:
        return False, "Campo expiresAt inválido."

    # Si parece milisegundos (>= 10^12), conviértelo a segundos
    if expires_at >= 10**12:
        expires_at //= 1000

    now = int(time.time())
    if now + grace_s >= expires_at:
        return False, "Licencia expirada."

    plan = rec.get("plan", "unknown")
    remaining_days = max(0, (expires_at - now) // 86400)
    return True, f"OK — plan: {plan} | días restantes: {remaining_days}"

if __name__ == "__main__":
    print("== Prueba de licencia Firebase ==")
    email = input("Email: ").strip()
    password = getpass("Password: ")
    try:
        uid, id_token, db = sign_in(email, password)
        print(f"Login OK. UID: {uid}")
        ok, msg = check_license(db, uid, id_token)  # ⬅️ pasar id_token
        print("Licencia:", "VÁLIDA ✅" if ok else "INVÁLIDA ❌", "-", msg)
    except Exception as e:
        print("Error:", e)
