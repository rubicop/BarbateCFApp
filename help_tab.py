import tkinter as tk
from tkinter import ttk, messagebox

class HelpTab:
    def __init__(self, notebook):
        self.frame = ttk.Frame(notebook, padding="10")
        self.setup_ui()

    def setup_ui(self):
        main_frame = ttk.LabelFrame(self.frame, text="Soporte y Ayuda", padding="20")
        main_frame.pack(expand=True)

        ttk.Button(main_frame, text="Ayuda de la App", command=self.show_app_help, width=30).pack(pady=10, ipady=5)
        ttk.Button(main_frame, text="Acerca de", command=self.show_about_info, width=30).pack(pady=10, ipady=5)

    def show_app_help(self):
        help_text = """
        GUÍA RÁPIDA DE LA APLICACIÓN

        • Jugadores:
          Gestiona la ficha completa de cada jugador, incluyendo datos personales, de contacto, trayectoria y lesiones.

        • Entrenamientos:
          Crea, edita y elimina sesiones de entrenamiento. Guarda y carga plantillas para reutilizar sesiones completas.

        • Convocatorias:
          Organiza las convocatorias para los partidos. Asigna a cada jugador un estado (convocado, suplente, lesionado, etc.).

        • Partidos y Estadísticas:
          Registra partidos y las estadísticas detalladas de cada jugador (minutos, goles, asistencias, etc.).

        • Planificación:
          Asigna jugadores a un entrenamiento específico y define su estado (presente, ausente, lesionado).

        • Ejercicios:
          Crea una base de datos de ejercicios con categorías y todos sus detalles (duración, descripción, imagen, etc.).

        • Editor de Campo:
          Dibuja esquemas tácticos y jugadas en un campo virtual con herramientas de dibujo avanzadas.

        • Reportes:
          Genera PDFs profesionales de entrenamientos, convocatorias, estadísticas y de la plantilla completa.
        """
        messagebox.showinfo("Ayuda de la Aplicación", help_text)

    def show_about_info(self):
        # --- VERSIÓN ACTUALIZADA ---
        about_text = """
        Barbate C.F. - Gestión Deportiva
        Versión 2.0

        Aplicación creada por:
        Manuel Jesús Tocino Gómez

        (Software sin ánimo de lucro)
        """
        messagebox.showinfo("Acerca de la Aplicación", about_text)