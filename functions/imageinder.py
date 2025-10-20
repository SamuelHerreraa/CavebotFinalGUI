# imagefinder.py
# Requisitos:
#   pip install pyautogui opencv-python pillow
#
# Uso:
#   python imagefinder.py ruta/a/imagen.png
#   (Si no pasas ruta, usa ./img/target.png)
#
# Nota:
# - Usa matching con "confidence" (OpenCV) si está disponible.
# - Escala de pantalla: ideal 100% para que el template match sea fiel.

import sys
import time
import pyautogui as pg

IMG_PATH = sys.argv[1] if len(sys.argv) > 1 else "./img/deaddragon.png"
INTERVAL_S = 1.0
CONFIDENCE = 0.85  # ajusta si hace falta (requiere opencv-python)

def main():
    print(f"[imagefinder] Buscando: {IMG_PATH}  (cada {INTERVAL_S:.1f}s)")
    print("[imagefinder] Ctrl+C para salir.")

    # Opcional: desactivar failsafe si te teletransporta a (0,0) con movimiento rápido
    pg.FAILSAFE = True   # ponlo en False si prefieres

    while True:
        try:
            center = None
            try:
                # Modo con confidence (requiere OpenCV)
                center = pg.locateCenterOnScreen(IMG_PATH, confidence=CONFIDENCE)
            except TypeError:
                # Fallback sin confidence si no está OpenCV
                center = pg.locateCenterOnScreen(IMG_PATH)

            if center:
                print(f"[imagefinder] Encontrada en ({center.x}, {center.y}). Moviendo cursor…")
                pg.moveTo(center.x, center.y, duration=0.10)
            else:
                print("[imagefinder] Imagen no encontrada en pantalla.")

            time.sleep(INTERVAL_S)

        except KeyboardInterrupt:
            print("\n[imagefinder] Saliendo por Ctrl+C. ¡Bye!")
            break
        except Exception as e:
            print(f"[imagefinder] Error: {e}")
            time.sleep(INTERVAL_S)

if __name__ == "__main__":
    main()
