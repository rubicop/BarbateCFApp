import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
import sys

def resource_path(relative_path):
    """ Obtiene la ruta absoluta al recurso, funciona para dev y para PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class SplashScreen:
    def __init__(self, root):
        self.root = root
        self.splash = tk.Toplevel(root)
        self.splash.overrideredirect(True) # Ventana sin bordes

        # --- Cargar y mostrar el logo ---
        try:
            logo_path = resource_path("logo.png")
            pil_image = Image.open(logo_path)
            # Redimensionar si es necesario para que no sea demasiado grande
            pil_image.thumbnail((400, 400), Image.LANCZOS)
            self.logo_image = ImageTk.PhotoImage(pil_image)
            
            logo_label = tk.Label(self.splash, image=self.logo_image, bg='white')
            logo_label.pack(pady=(20, 10))
            
            # --- Añadir el texto "Cargando..." ---
            loading_label = tk.Label(self.splash, text="Cargando...", font=("Arial", 12, "italic"), bg='white')
            loading_label.pack(pady=(0, 20))
            
            self.splash.config(bg='white')

        except Exception as e:
            print(f"Error al cargar logo: {e}")
            # Si no hay logo, mostrar solo texto
            fallback_label = tk.Label(self.splash, text="Barbate C.F. Gestión", font=("Arial", 20))
            fallback_label.pack(padx=50, pady=50)

        # --- Centrar la ventana en la pantalla ---
        self.center_window()

        # --- Programar el cierre y la apertura de la app principal ---
        # Después de 1500 milisegundos (1.5 segundos), llama a la función destroy_splash
        self.splash.after(1500, self.destroy_splash)

    def center_window(self):
        self.splash.update_idletasks()
        width = self.splash.winfo_width()
        height = self.splash.winfo_height()
        x = (self.splash.winfo_screenwidth() // 2) - (width // 2)
        y = (self.splash.winfo_screenheight() // 2) - (height // 2)
        self.splash.geometry(f'{width}x{height}+{x}+{y}')

    def destroy_splash(self):
        self.splash.destroy()
        # Muestra la ventana principal que estaba oculta
        self.root.deiconify()