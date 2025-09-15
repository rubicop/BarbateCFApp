import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os

class PlanningTab:
    def __init__(self, notebook, db):
        self.db = db
        self.frame = ttk.Frame(notebook)
        self.current_training_id = None
        self.image_popup = None
        self.popup_photo = None

        self.setup_ui()
        self.refresh_trainings_dropdown()

    def setup_ui(self):
        main_frame = ttk.Frame(self.frame, padding=10)
        main_frame.pack(fill="both", expand=True)

        selection_frame = ttk.LabelFrame(main_frame, text="Seleccionar Entrenamiento")
        selection_frame.pack(fill="x", pady=(0, 10))
        
        self.training_var = tk.StringVar()
        self.trainings_dropdown = ttk.Combobox(selection_frame, textvariable=self.training_var, state="readonly", width=40)
        self.trainings_dropdown.pack(fill="x", expand=True, padx=5, pady=5)
        self.trainings_dropdown.bind("<<ComboboxSelected>>", self.on_training_selected)

        players_frame = ttk.Frame(main_frame)
        players_frame.pack(fill="both", expand=True)

        available_frame = ttk.LabelFrame(players_frame, text="Jugadores Disponibles")
        available_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        self.available_tree = self.create_player_treeview(available_frame)
        self.available_tree.bind("<<TreeviewSelect>>", lambda e: self.show_player_image(self.available_tree))

        buttons_frame = ttk.Frame(players_frame)
        buttons_frame.pack(side="left", fill="y", padx=5)
        ttk.Button(buttons_frame, text=">", command=self.add_to_attendance).pack(pady=5)
        ttk.Button(buttons_frame, text="<", command=self.remove_from_attendance).pack(pady=5)

        attendance_frame = ttk.LabelFrame(players_frame, text="Convocatoria")
        attendance_frame.pack(side="left", fill="both", expand=True, padx=(5, 0))
        
        self.attendance_tree = self.create_player_treeview(attendance_frame)
        self.attendance_tree.bind("<<TreeviewSelect>>", lambda e: self.show_player_image(self.attendance_tree))

        self.attendance_tree.tag_configure('presente', background='#D4EDDA', foreground='#155724')
        self.attendance_tree.tag_configure('ausente', background='#FFF3CD', foreground='#856404')
        self.attendance_tree.tag_configure('lesionado', background='#F8D7DA', foreground='#721C24')

        status_frame = ttk.Frame(attendance_frame)
        status_frame.pack(fill="x", pady=5)
        ttk.Button(status_frame, text="Presente", command=lambda: self.set_status('presente')).pack(side="left", expand=True)
        ttk.Button(status_frame, text="Ausente", command=lambda: self.set_status('ausente')).pack(side="left", expand=True)
        ttk.Button(status_frame, text="Lesionado", command=lambda: self.set_status('lesionado')).pack(side="left", expand=True)

    def create_player_treeview(self, parent):
        cols = ("id", "name", "position")
        tree = ttk.Treeview(parent, columns=cols, show="headings")
        tree.heading("id", text="ID")
        tree.heading("name", text="Nombre")
        tree.heading("position", text="Posición")
        tree.column("id", width=0, stretch=tk.NO)
        tree.column("name", width=180)
        tree.column("position", width=100)
        tree.pack(fill="both", expand=True)
        return tree

    def refresh_trainings_dropdown(self):
        """Recarga la lista de entrenamientos desde la base de datos."""
        current_selection_id = self.current_training_id
        
        trainings = self.db.get_all_trainings_for_dropdown()
        self.trainings_map = {f"{t[1]} - Sesión {t[3]}": t[0] for t in trainings}
        self.trainings_dropdown['values'] = list(self.trainings_map.keys())
        
        # Intentar restaurar la selección anterior si todavía existe
        found_selection = False
        if current_selection_id:
            for text, tid in self.trainings_map.items():
                if tid == current_selection_id:
                    self.trainings_dropdown.set(text)
                    found_selection = True
                    break
        
        if not found_selection:
            self.trainings_dropdown.set('')
            self.on_training_selected()

    def on_training_selected(self, event=None):
        selected_text = self.training_var.get()
        if selected_text in self.trainings_map:
            self.current_training_id = self.trainings_map[selected_text]
            self.refresh_player_lists()
        else:
            self.current_training_id = None
            self.refresh_player_lists()

    def refresh_player_lists(self):
        for tree in [self.available_tree, self.attendance_tree]:
            for item in tree.get_children():
                tree.delete(item)

        if not self.current_training_id:
            return
        
        available_players = self.db.get_unassigned_players(self.current_training_id)
        for player in available_players:
            self.available_tree.insert("", "end", values=player[:3], iid=player[0])

        attendance_list = self.db.get_attendance_for_training(self.current_training_id)
        for player in attendance_list:
            self.attendance_tree.insert("", "end", values=player[:3], iid=player[0], tags=(player[3],))

    def add_to_attendance(self):
        selected_items = self.available_tree.selection()
        if not selected_items: return
        
        for item_id in selected_items:
            player_id = int(item_id)
            self.db.set_player_attendance(self.current_training_id, player_id, 'presente')
        self.refresh_player_lists()

    def remove_from_attendance(self):
        selected_items = self.attendance_tree.selection()
        if not selected_items: return

        for item_id in selected_items:
            player_id = int(item_id)
            self.db.remove_player_from_training(self.current_training_id, player_id)
        self.refresh_player_lists()

    def set_status(self, status):
        selected_items = self.attendance_tree.selection()
        if not selected_items:
            messagebox.showwarning("Sin selección", "Selecciona un jugador de la convocatoria para cambiar su estado.")
            return

        for item_id in selected_items:
            player_id = int(item_id)
            self.db.set_player_attendance(self.current_training_id, player_id, status)
        self.refresh_player_lists()

    def show_player_image(self, tree):
        if self.image_popup and self.image_popup.winfo_exists():
            self.image_popup.destroy()

        selected_item = tree.selection()
        if not selected_item: return

        player_id = int(selected_item[0])
        player_data = self.db.get_player_by_id(player_id)
        if not player_data: return
        
        photo_path = player_data[9]
        player_name = player_data[1]

        self.image_popup = tk.Toplevel(self.frame)
        self.image_popup.title(player_name)
        self.image_popup.geometry("150x180")
        self.image_popup.resizable(False, False)

        if photo_path and os.path.exists(photo_path):
            try:
                img = Image.open(photo_path)
                img.thumbnail((150, 150))
                self.popup_photo = ImageTk.PhotoImage(img)
                lbl = tk.Label(self.image_popup, image=self.popup_photo)
                lbl.pack()
            except Exception as e:
                lbl = tk.Label(self.image_popup, text="Error al\ncargar imagen")
                lbl.pack(pady=20)
        else:
            lbl = tk.Label(self.image_popup, text="Sin foto")
            lbl.pack(pady=20)
        
        ttk.Label(self.image_popup, text=player_name, justify="center").pack(pady=5)