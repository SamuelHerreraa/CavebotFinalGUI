# tabs/overlay_picker.py
# Overlay a pantalla completa para elegir un pixel (x,y) y leer su color (RGB)
# Sin librerías externas: usa ctypes con Win32 GetPixel. Diseñado para Windows.

import tkinter as tk
from ctypes import windll, wintypes

# Win32 APIs
user32 = windll.user32
gdi32 = windll.gdi32

def get_pixel_color(x: int, y: int):
    """Lee el color del pixel en (x,y) (coordenadas de pantalla) usando Win32 GetPixel."""
    hdc = user32.GetDC(0)  # DC de toda la pantalla
    colorref = gdi32.GetPixel(hdc, x, y)
    user32.ReleaseDC(0, hdc)
    if colorref == -1:  # GetPixel puede devolver -1 en error
        return (0, 0, 0)
    # COLORREF: 0x00BBGGRR
    r = colorref & 0x0000FF
    g = (colorref & 0x00FF00) >> 8
    b = (colorref & 0xFF0000) >> 16
    return (r, g, b)


class PixelPickerOverlay(tk.Toplevel):
    """
    Overlay semi-transparente y 'topmost' que captura un click.
    - Muestra coords + RGB en vivo (arriba centrado).
    - click izquierdo: confirma (llama callback y cierra)
    - click derecho o Esc: cancela (cierra)
    """

    def __init__(self, parent, on_pick):
        """
        on_pick: callable (x:int, y:int, rgb:tuple[int,int,int]) -> None
        """
        super().__init__(parent)
        self.withdraw()
        self.overrideredirect(True)
        self.attributes("-alpha", 0.15)
        self.attributes("-topmost", True)
        try:
            # Algunos WM soportan -fullscreen; en Windows va bien
            self.attributes("-fullscreen", True)
        except Exception:
            # Fallback: cubrir la pantalla primaria
            self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")

        self.configure(bg="black")
        self["cursor"] = "crosshair"
        self._on_pick = on_pick

        # HUD superior (coords + rgb)
        self.hud = tk.Label(
            self,
            text="x=0, y=0  |  RGB=(0,0,0)  |  Click izq: elegir  |  Click der/Esc: cancelar",
            font=("Segoe UI", 12, "bold"),
            fg="white",
            bg="#000000",
            padx=12, pady=8
        )
        self.hud.place(relx=0.5, y=18, anchor="n")

        # Vinculaciones
        self.bind("<Motion>", self._on_motion)
        self.bind("<Button-1>", self._on_left_click)
        self.bind("<Button-3>", self._on_cancel)
        self.bind("<Escape>", self._on_cancel)

        # Mostrar
        self.deiconify()
        self.lift()
        self.focus_set()

    def _update_hud(self, x, y, rgb):
        r, g, b = rgb
        self.hud.configure(text=f"x={x}, y={y}  |  RGB=({r},{g},{b})  |  Click izq: elegir  |  Click der/Esc: cancelar")

    def _on_motion(self, _evt):
        x = self.winfo_pointerx()
        y = self.winfo_pointery()
        rgb = get_pixel_color(x, y)
        self._update_hud(x, y, rgb)

    def _on_left_click(self, _evt):
        x = self.winfo_pointerx()
        y = self.winfo_pointery()
        rgb = get_pixel_color(x, y)
        try:
            if callable(self._on_pick):
                self._on_pick(x, y, rgb)
        finally:
            self.destroy()

    def _on_cancel(self, _evt=None):
        self.destroy()
