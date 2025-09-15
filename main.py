import tkinter as tk
from tkinter import ttk, messagebox
from database import Database
from players_tab import PlayersTab
from coaches_tab import CoachesTab
from trainings_tab import TrainingsTab
from exercises_tab import ExercisesTab
from reports_tab import ReportsTab
from field_editor_tab import FieldEditorTab
from planning_tab import PlanningTab
from callups_tab import CallupsTab
from matches_tab import MatchesTab
from splash_screen import SplashScreen
from help_tab import HelpTab

class BarbateCFApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Barbate C.F. - Gestión Deportiva")
        self.root.withdraw() 
        splash = SplashScreen(self.root)

        self.root.geometry("1200x800")
        self.root.overrideredirect(True)
        
        self.taskbar_icon = None
        self.x = None
        self.y = None

        self.create_custom_title_bar()
        self.db = Database()
        container = ttk.Frame(self.root)
        container.pack(fill='both', expand=True)
        self.notebook = ttk.Notebook(container)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # --- Pestañas ---
        self.players_tab = PlayersTab(self.notebook, self.db)
        self.notebook.add(self.players_tab.frame, text='Jugadores')
        self.coaches_tab = CoachesTab(self.notebook, self.db)
        self.notebook.add(self.coaches_tab.frame, text='Cuerpo Técnico')
        self.trainings_tab = TrainingsTab(self.notebook, self.db)
        self.notebook.add(self.trainings_tab.frame, text='Entrenamientos')
        self.callups_tab = CallupsTab(self.notebook, self.db)
        self.notebook.add(self.callups_tab.frame, text='Convocatorias')
        self.matches_tab = MatchesTab(self.notebook, self.db)
        self.notebook.add(self.matches_tab.frame, text='Partidos y Estadísticas')
        self.planning_tab = PlanningTab(self.notebook, self.db)
        self.notebook.add(self.planning_tab.frame, text='Planificación')
        self.exercises_tab = ExercisesTab(self.notebook, self.db)
        self.notebook.add(self.exercises_tab.frame, text='Ejercicios')
        self.field_editor_tab = FieldEditorTab(self.notebook, self.db)
        self.notebook.add(self.field_editor_tab.frame, text='Editor de Campo')
        self.reports_tab = ReportsTab(self.notebook, self.db, self.field_editor_tab)
        self.notebook.add(self.reports_tab.frame, text='Reportes')
        self.help_tab = HelpTab(self.notebook)
        self.notebook.add(self.help_tab.frame, text='Ayuda')
        
        # --- NUEVA LÍNEA --- Asocia el evento de cambio de pestaña a una función
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
        self.root.protocol("WM_DELETE_WINDOW", self.confirm_close)
        
        self.toggle_maximize(init=True)

    def on_tab_changed(self, event):
        """Función que se ejecuta cada vez que el usuario cambia de pestaña."""
        try:
            selected_tab_text = self.notebook.tab(self.notebook.select(), "text")

            # Si la pestaña seleccionada es Planificación o Ejercicios, se actualiza su lista de entrenamientos
            if selected_tab_text == 'Planificación':
                self.planning_tab.refresh_trainings_dropdown()
            elif selected_tab_text == 'Ejercicios':
                self.exercises_tab.refresh_trainings_dropdown()
            # Opcional: recargar también la pestaña de entrenamientos por si hay cambios en otras áreas
            elif selected_tab_text == 'Entrenamientos':
                self.trainings_tab.refresh_data()
        except tk.TclError:
            # Esto puede ocurrir si las pestañas aún no están completamente cargadas, es seguro ignorarlo
            pass

    def create_custom_title_bar(self):
        self.is_maximized = False
        self.previous_geometry = "1200x800"
        
        title_bar = tk.Frame(self.root, bg='#2e2e2e', relief='raised', bd=0)
        title_bar.pack(fill='x')

        title_label = tk.Label(title_bar, text="Barbate C.F. - Gestión Deportiva", bg='#2e2e2e', fg='white', padx=10)
        title_label.pack(side='left')

        close_button = tk.Button(title_bar, text=' X ', command=self.confirm_close, bg='#2e2e2e', fg='white', relief='flat', activebackground='red')
        close_button.pack(side='right', padx=2, pady=2)
        
        maximize_button = tk.Button(title_bar, text=' □ ', command=self.toggle_maximize, bg='#2e2e2e', fg='white', relief='flat')
        maximize_button.pack(side='right', padx=2, pady=2)

        minimize_button = tk.Button(title_bar, text=' - ', command=self.minimize_app, bg='#2e2e2e', fg='white', relief='flat')
        minimize_button.pack(side='right', padx=2, pady=2)

        title_bar.bind("<ButtonPress-1>", self.start_move)
        title_bar.bind("<ButtonRelease-1>", self.stop_move)
        title_bar.bind("<B1-Motion>", self.do_move)
        title_label.bind("<ButtonPress-1>", self.start_move)
        title_label.bind("<ButtonRelease-1>", self.stop_move)
        title_label.bind("<B1-Motion>", self.do_move)
    
    def confirm_close(self):
        if messagebox.askyesno("Confirmar Salida", "¿Estás seguro de que quieres cerrar la aplicación?"):
            self.root.destroy()

    def minimize_app(self):
        self.root.withdraw()
        self.taskbar_icon = tk.Toplevel(self.root)
        self.taskbar_icon.geometry("1x1-100-100") 
        self.taskbar_icon.title("Barbate C.F. - Gestión Deportiva")
        try:
            self.taskbar_icon.iconbitmap('logo.ico')
        except tk.TclError:
            pass
        
        self.taskbar_icon.bind("<Unmap>", self.restore_app)
        self.taskbar_icon.bind("<FocusIn>", self.restore_app)

    def restore_app(self, event=None):
        if self.taskbar_icon:
            self.taskbar_icon.unbind("<Unmap>")
            self.taskbar_icon.unbind("<FocusIn>")
            self.taskbar_icon.destroy()
            self.taskbar_icon = None
        
        self.root.deiconify()

    def toggle_maximize(self, init=False):
        if self.is_maximized:
            self.root.geometry(self.previous_geometry)
            self.is_maximized = False
        else:
            if not init:
                self.previous_geometry = self.root.geometry()
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            self.root.geometry(f"{screen_width}x{screen_height-40}+0+0")
            self.is_maximized = True

    def start_move(self, event):
        if self.is_maximized:
            self.toggle_maximize()
            self.root.after(50, lambda: self.start_move_drag(event))
            return
        self.start_move_drag(event)

    def start_move_drag(self, event):
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.x = None
        self.y = None

    def do_move(self, event):
        if self.is_maximized: return
        if self.x is None or self.y is None:
            return
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

if __name__ == "__main__":
    root = tk.Tk()
    app = BarbateCFApp(root)
    root.mainloop()