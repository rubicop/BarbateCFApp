import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from PIL import Image, ImageTk
import os
import shutil
import sys

def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except Exception: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class TrainingManagementTab:
    def __init__(self, parent, db):
        self.db = db
        self.frame = ttk.Frame(parent)
        self.current_training_id = None

        main_pane = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        main_pane.pack(fill="both", expand=True)

        list_frame_container = ttk.Frame(main_pane, width=350)
        main_pane.add(list_frame_container, weight=1)

        details_pane_container = ttk.Frame(main_pane)
        main_pane.add(details_pane_container, weight=3)

        self.setup_list_pane(list_frame_container)
        self.setup_details_pane(details_pane_container)
        
        self.load_trainings_list()

    def setup_list_pane(self, parent):
        list_frame = ttk.LabelFrame(parent, text="Sesiones de Entrenamiento")
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        columns = ("id", "date", "mesocycle", "session")
        headers = {"id": "ID", "date": "Fecha", "mesocycle": "Mesociclo", "session": "Sesión"}
        self.trainings_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        for col in columns: self.trainings_tree.heading(col, text=headers[col])
        self.trainings_tree.column("id", width=40, anchor="center")
        self.trainings_tree.column("session", width=60, anchor="center")
        self.trainings_tree.pack(fill="both", expand=True)
        self.trainings_tree.bind("<<TreeviewSelect>>", self.on_training_select)

        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="Nuevo", command=self.add_training).pack(side="left", expand=True, padx=5)
        ttk.Button(btn_frame, text="Eliminar", command=self.delete_training).pack(side="right", expand=True, padx=5)

    def setup_details_pane(self, parent):
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill="both", expand=True, padx=(0, 10), pady=10)

        self.details_frame_manager = TrainingDetailsFrame(self.notebook, self.db, self.load_trainings_list)
        self.attendance_frame_manager = AttendanceFrame(self.notebook, self.db)
        self.exercises_frame_manager = ExercisesFrame(self.notebook, self.db)

        self.notebook.add(self.details_frame_manager, text="Detalles y Material")
        self.notebook.add(self.attendance_frame_manager, text="Planificación de Asistencia")
        self.notebook.add(self.exercises_frame_manager, text="Ejercicios de la Sesión")

    def load_trainings_list(self):
        selected_id = self.current_training_id
        for item in self.trainings_tree.get_children(): self.trainings_tree.delete(item)
        for training in self.db.get_all_trainings():
            iid = training[0]
            self.trainings_tree.insert("", tk.END, values=(iid, training[1], training[2], training[3]), iid=iid)
            if iid == selected_id:
                self.trainings_tree.selection_set(iid)

    def on_training_select(self, event=None):
        selected_items = self.trainings_tree.selection()
        if not selected_items:
            self.current_training_id = None
        else:
            self.current_training_id = self.trainings_tree.item(selected_items[0])['values'][0]
        
        self.details_frame_manager.load_training_data(self.current_training_id)
        self.attendance_frame_manager.load_attendance_data(self.current_training_id)
        self.exercises_frame_manager.load_exercises(self.current_training_id)

    def add_training(self):
        TrainingDialog(self.frame, self.db, self.load_trainings_list)

    def delete_training(self):
        if not self.current_training_id:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un entrenamiento para eliminar.")
            return
        if messagebox.askyesno("Confirmar", "Se borrarán también sus ejercicios y planificación asociados. ¿Continuar?"):
            self.db.delete_training(self.current_training_id)
            self.load_trainings_list()
            self.details_frame_manager.load_training_data(None)
            self.attendance_frame_manager.load_attendance_data(None)
            self.exercises_frame_manager.load_exercises(None)

class TrainingDetailsFrame(ttk.Frame):
    def __init__(self, parent, db, refresh_callback):
        super().__init__(parent)
        self.db = db; self.refresh_main_list = refresh_callback; self.training_id = None
        ttk.Button(self, text="Editar Detalles de la Sesión", command=self.edit_training).pack(anchor="ne", padx=10, pady=10)
        self.info_frame = ttk.LabelFrame(self, text="Información de la Sesión")
        self.info_frame.pack(fill="x", expand=True, padx=10)
        self.labels = {}
        fields = ["Fecha", "Mesociclo", "Nº Sesión", "Entrenador", "Asistente"]
        for i, field in enumerate(fields):
            ttk.Label(self.info_frame, text=f"{field}:", font=('Arial', 10, 'bold')).grid(row=i, column=0, sticky="w", padx=10, pady=5)
            self.labels[field] = ttk.Label(self.info_frame, text="-"); self.labels[field].grid(row=i, column=1, sticky="w", padx=10)
        self.material_frame = ttk.LabelFrame(self, text="Material")
        self.material_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.material_text = tk.Text(self.material_frame, height=5, state="disabled", bg="whitesmoke", wrap="word")
        self.material_text.pack(fill="both", expand=True, padx=5, pady=5)

    def load_training_data(self, training_id):
        self.training_id = training_id
        if not training_id:
            self.labels["Fecha"].config(text="-"); self.labels["Mesociclo"].config(text="-"); self.labels["Nº Sesión"].config(text="-")
            self.labels["Entrenador"].config(text="-"); self.labels["Asistente"].config(text="-")
            self.material_text.config(state="normal"); self.material_text.delete("1.0", tk.END); self.material_text.config(state="disabled")
            return
        training = self.db.get_training_by_id(training_id)
        if training:
            tid, date, meso, sess, coach, assist, mat = training
            self.labels["Fecha"].config(text=date); self.labels["Mesociclo"].config(text=meso); self.labels["Nº Sesión"].config(text=str(sess))
            self.labels["Entrenador"].config(text=coach); self.labels["Asistente"].config(text=assist)
            self.material_text.config(state="normal"); self.material_text.delete("1.0", tk.END); self.material_text.insert("1.0", mat or ""); self.material_text.config(state="disabled")
    
    def refresh_and_reload(self):
        self.refresh_main_list()
        self.load_training_data(self.training_id)

    def edit_training(self):
        if not self.training_id: messagebox.showwarning("Sin Selección", "Seleccione un entrenamiento para editar."); return
        training_data = self.db.get_training_by_id(self.training_id)
        if training_data: TrainingDialog(self, self.db, self.refresh_and_reload, training_data)

class AttendanceFrame(ttk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db; self.training_id = None
        players_frame = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        players_frame.pack(fill="both", expand=True, padx=10, pady=10)
        available_frame = ttk.LabelFrame(players_frame, text="Jugadores Disponibles")
        players_frame.add(available_frame, weight=1)
        self.available_tree = self._create_player_treeview(available_frame)
        buttons_frame = ttk.Frame(players_frame, width=50); buttons_frame.pack_propagate(False); players_frame.add(buttons_frame)
        ttk.Button(buttons_frame, text=">", command=self.move_to_status).pack(pady=5, ipadx=5, anchor="center")
        ttk.Button(buttons_frame, text="<", command=self.move_to_available).pack(pady=5, ipadx=5, anchor="center")
        status_notebook = ttk.Notebook(players_frame); players_frame.add(status_notebook, weight=2)
        self.status_notebook = status_notebook
        self.status_trees = {}
        for status in ["Presente", "Ausente", "Lesionado"]:
            frame = ttk.Frame(status_notebook); status_notebook.add(frame, text=status)
            tree = self._create_player_treeview(frame); self.status_trees[status.lower()] = tree

    def _create_player_treeview(self, parent):
        cols = ("id", "name", "position")
        tree = ttk.Treeview(parent, columns=cols, show="headings", selectmode="extended")
        tree.heading("name", text="Nombre"); tree.column("name", width=180)
        tree.heading("position", text="Posición"); tree.column("position", width=100)
        tree.column("id", width=0, stretch=tk.NO)
        tree.pack(fill="both", expand=True)
        return tree

    def load_attendance_data(self, training_id):
        self.training_id = training_id
        for tree in [self.available_tree] + list(self.status_trees.values()):
            for item in tree.get_children(): tree.delete(item)
        if not training_id: return
        for player in self.db.get_unassigned_players(training_id):
            self.available_tree.insert("", "end", values=player[:3], iid=player[0])
        for player in self.db.get_attendance_for_training(training_id):
            status = player[3]
            if status in self.status_trees: self.status_trees[status].insert("", "end", values=player[:3], iid=player[0])
    
    def move_to_status(self):
        if not self.training_id: return
        selected_items = self.available_tree.selection()
        if not selected_items: return
        active_tab_index = self.status_notebook.index(self.status_notebook.select())
        status = list(self.status_trees.keys())[active_tab_index]
        for item_id in selected_items: self.db.set_player_attendance(self.training_id, int(item_id), status)
        self.load_attendance_data(self.training_id)

    def move_to_available(self):
        if not self.training_id: return
        active_tab_index = self.status_notebook.index(self.status_notebook.select())
        active_tree = list(self.status_trees.values())[active_tab_index]
        selected_items = active_tree.selection()
        if not selected_items: return
        for item_id in selected_items: self.db.remove_player_from_training(self.training_id, int(item_id))
        self.load_attendance_data(self.training_id)

class ExercisesFrame(ttk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db; self.training_id = None
        main_frame = ttk.Frame(self, padding=10); main_frame.pack(fill="both", expand=True)
        cols = ("id", "name", "category", "duration")
        self.exercises_tree = tttk.Treeview(main_frame, columns=cols, show="headings")
        self.exercises_tree.heading("id", text="ID"); self.exercises_tree.column("id", width=40)
        self.exercises_tree.heading("name", text="Nombre del Ejercicio"); self.exercises_tree.column("name", width=300)
        self.exercises_tree.heading("category", text="Categoría"); self.exercises_tree.column("category", width=120)
        self.exercises_tree.heading("duration", text="Duración (min)"); self.exercises_tree.column("duration", width=100)
        self.exercises_tree.pack(fill="both", expand=True)
        self.exercises_tree.bind("<Double-1>", self.edit_exercise)

        btn_frame = ttk.Frame(main_frame); btn_frame.pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="Añadir/Crear Ejercicio", command=self.open_add_exercise_dialog).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Quitar de la Sesión", command=self.unassign_exercise).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Editar Detalles", command=self.edit_exercise).pack(side="left", padx=5)
    
    def load_exercises(self, training_id):
        self.training_id = training_id
        for item in self.exercises_tree.get_children(): self.exercises_tree.delete(item)
        if not training_id: return
        for ex in self.db.get_exercises_by_training(training_id):
            self.exercises_tree.insert("", "end", values=(ex[0], ex[2], ex[11], ex[4]))

    def open_add_exercise_dialog(self):
        if not self.training_id: messagebox.showwarning("Sin Selección", "Seleccione un entrenamiento primero."); return
        AddExerciseDialog(self, self.db, self.training_id, self.load_exercises)
    
    def unassign_exercise(self):
        selected_items = self.exercises_tree.selection()
        if not selected_items: messagebox.showwarning("Sin Selección", "Seleccione un ejercicio para quitar."); return
        if messagebox.askyesno("Confirmar", "Esto quitará el ejercicio de esta sesión, pero no lo borrará de la base de datos. ¿Continuar?"):
            for item_id in selected_items: self.db.unassign_exercise(self.exercises_tree.item(item_id)['values'][0])
            self.load_exercises(self.training_id)
            
    def edit_exercise(self, event=None):
        selected_items = self.exercises_tree.selection()
        if not selected_items: messagebox.showwarning("Sin Selección", "Seleccione un ejercicio para ver/editar sus detalles."); return
        ex_id = self.exercises_tree.item(selected_items[0])['values'][0]
        ExerciseDetailsDialog(self, self.db, ex_id, lambda: self.load_exercises(self.training_id))

class TrainingDialog(tk.Toplevel):
    def __init__(self, parent, db, refresh_callback, training_data=None):
        super().__init__(parent)
        self.db = db; self.refresh_callback = refresh_callback; self.training_data = training_data
        self.title("Editar Entrenamiento" if training_data else "Añadir Entrenamiento"); self.geometry("450x300")
        self.transient(parent); self.grab_set(); self.resizable(False, False)
        
        self.entries = {}
        form_frame = ttk.Frame(self, padding=20); form_frame.pack(fill="both", expand=True)
        fields = {"Fecha:": "date", "Mesociclo:": "mesocycle", "Nº Sesión:": "session", "Entrenador:": "coach", "Asistente:": "assistant", "Material:": "material"}
        
        coach_names = self.db.get_all_coach_names()

        for i, (text, name) in enumerate(fields.items()):
            ttk.Label(form_frame, text=text).grid(row=i, column=0, sticky="w", padx=5, pady=5)
            if name in ["coach", "assistant"]:
                entry = ttk.Combobox(form_frame, values=coach_names)
            else:
                entry = ttk.Entry(form_frame)
            entry.grid(row=i, column=1, sticky="ew", padx=5, pady=5); self.entries[name] = entry
        
        form_frame.grid_columnconfigure(1, weight=1)
        if self.training_data: self.populate_form()
        btn_frame = ttk.Frame(self); btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Guardar", command=self.save).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side="left", padx=10)

    def populate_form(self):
        tid, date, meso, sess, coach, assist, mat = self.training_data
        self.entries["date"].insert(0, date); self.entries["mesocycle"].insert(0, meso); self.entries["session"].insert(0, str(sess))
        self.entries["coach"].set(coach); self.entries["assistant"].set(assist); self.entries["material"].insert(0, mat)

    def save(self):
        date = self.entries["date"].get(); meso = self.entries["mesocycle"].get(); sess = self.entries["session"].get()
        if not all([date, meso, sess]): messagebox.showwarning("Faltan Datos", "Fecha, Mesociclo y Nº Sesión son obligatorios.", parent=self); return
        coach = self.entries["coach"].get(); assist = self.entries["assistant"].get(); mat = self.entries["material"].get()
        if self.training_data:
            self.db.update_training(self.training_data[0], date, meso, sess, coach, assist, mat)
        else:
            self.db.insert_training(date, meso, sess, coach, assist, mat)
        self.refresh_callback(); self.destroy()

class AddExerciseDialog(tk.Toplevel):
    def __init__(self, parent, db, training_id, refresh_callback):
        super().__init__(parent)
        self.db = db; self.training_id = training_id; self.refresh_callback = refresh_callback
        self.title("Añadir Ejercicio a la Sesión"); self.geometry("600x400"); self.transient(parent); self.grab_set()
        notebook = ttk.Notebook(self); notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        existing_frame = ttk.Frame(notebook); notebook.add(existing_frame, text="Añadir Ejercicio Existente")
        cols = ("id", "name", "category"); self.existing_tree = ttk.Treeview(existing_frame, columns=cols, show="headings", selectmode="extended")
        self.existing_tree.heading("name", text="Nombre"); self.existing_tree.heading("category", text="Categoría")
        self.existing_tree.column("id", width=0, stretch=tk.NO); self.existing_tree.pack(fill="both", expand=True, pady=5)
        ttk.Button(existing_frame, text="Añadir Seleccionados", command=self.add_selected_exercises).pack(pady=5)
        
        new_frame = ttk.Frame(notebook, padding=10); notebook.add(new_frame, text="Crear Nuevo Ejercicio para esta Sesión")
        ttk.Label(new_frame, text="Nombre:").grid(row=0, column=0, sticky="w", pady=3)
        self.new_ex_name = ttk.Entry(new_frame); self.new_ex_name.grid(row=0, column=1, sticky="ew")
        ttk.Label(new_frame, text="Categoría:").grid(row=1, column=0, sticky="w", pady=3)
        self.new_ex_cat = ttk.Combobox(new_frame, values=["Calentamiento", "Físico", "Técnico", "Táctico", "Estrategia", "Vuelta a la Calma"]); self.new_ex_cat.grid(row=1, column=1, sticky="ew")
        new_frame.grid_columnconfigure(1, weight=1)
        ttk.Button(new_frame, text="Crear y Añadir Ejercicio", command=self.create_and_add_exercise).pack(pady=10)
        
        self.load_unassigned_exercises()

    def load_unassigned_exercises(self):
        for item in self.existing_tree.get_children(): self.existing_tree.delete(item)
        for ex in self.db.get_unassigned_exercises():
            self.existing_tree.insert("", "end", values=(ex[0], ex[2], ex[11]), iid=ex[0])
            
    def add_selected_exercises(self):
        selected_iids = self.existing_tree.selection()
        if not selected_iids: return
        for iid in selected_iids:
            self.db.assign_exercise_to_training(int(iid), self.training_id)
        self.refresh_callback(self.training_id); self.destroy()

    def create_and_add_exercise(self):
        name = self.new_ex_name.get(); category = self.new_ex_cat.get()
        if not name: messagebox.showwarning("Faltan Datos", "El nombre es obligatorio.", parent=self); return
        self.db.insert_exercise(self.training_id, name, "", 0, "", "", "", "", "", "", category)
        messagebox.showinfo("Éxito", "Ejercicio creado y añadido. Puedes editar los detalles completos más tarde.", parent=self)
        self.refresh_callback(self.training_id); self.destroy()

class ExerciseDetailsDialog(tk.Toplevel):
    def __init__(self, parent, db, exercise_id, refresh_callback):
        super().__init__(parent)
        self.db = db; self.exercise_id = exercise_id; self.refresh_callback = refresh_callback
        self.image_path = None; self.exercise_image = None
        self.title("Detalles del Ejercicio"); self.geometry("700x600"); self.transient(parent); self.grab_set()

        form_frame = ttk.Frame(self, padding=10); form_frame.pack(fill="both", expand=True)
        form_frame.columnconfigure(1, weight=1)

        ttk.Label(form_frame, text="Categoría:").grid(row=0, column=0, sticky="w", pady=3)
        self.ex_category = ttk.Combobox(form_frame, values=["Calentamiento", "Físico", "Técnico", "Táctico", "Estrategia", "Vuelta a la Calma"]); self.ex_category.grid(row=0, column=1, sticky="ew")
        ttk.Label(form_frame, text="Nombre:").grid(row=1, column=0, sticky="w", pady=3); self.ex_name = ttk.Entry(form_frame); self.ex_name.grid(row=1, column=1, sticky="ew")
        ttk.Label(form_frame, text="Duración (min):").grid(row=2, column=0, sticky="w", pady=3); self.ex_duration = ttk.Entry(form_frame); self.ex_duration.grid(row=2, column=1, sticky="ew")
        ttk.Label(form_frame, text="Repeticiones/Series:").grid(row=3, column=0, sticky="w", pady=3); self.ex_repetitions = ttk.Entry(form_frame); self.ex_repetitions.grid(row=3, column=1, sticky="ew")
        ttk.Label(form_frame, text="Espacio/Dimensiones:").grid(row=4, column=0, sticky="w", pady=3); self.ex_space = ttk.Entry(form_frame); self.ex_space.grid(row=4, column=1, sticky="ew")

        notebook = ttk.Notebook(form_frame); notebook.grid(row=5, column=0, columnspan=2, sticky="ew", pady=10)
        text_widgets = {}; names = {"Descripción": "description", "Objetivos": "objectives", "Reglas": "rules", "Variantes": "variants"}
        for text, name in names.items():
            frame = ttk.Frame(notebook); notebook.add(frame, text=text)
            widget = tk.Text(frame, height=4, wrap="word"); widget.pack(fill="x"); text_widgets[name] = widget
        self.text_widgets = text_widgets
        
        bottom_frame = ttk.Frame(form_frame); bottom_frame.grid(row=6, column=0, columnspan=2, sticky="ew")
        image_container = tk.Frame(bottom_frame, width=300, height=200, relief="solid", bd=1); image_container.pack_propagate(False); image_container.pack(side="left", padx=(0, 10))
        self.image_label = tk.Label(image_container, text="Sin Imagen", bg="lightgrey"); self.image_label.pack(fill="both", expand=True)
        btn_container = ttk.Frame(bottom_frame); btn_container.pack(side="left")
        ttk.Button(btn_container, text="Seleccionar Imagen", command=self.select_image).pack(pady=5)
        
        ttk.Button(form_frame, text="Guardar Cambios", command=self.save).grid(row=7, column=1, sticky="e", pady=10)
        self.load_exercise_data()
        
    def load_exercise_data(self):
        ex = self.db.get_exercise_by_id(self.exercise_id)
        if not ex: self.destroy(); return
        (eid, tid, name, desc, dur, rep, space, obj, rules, var, img_path, category) = ex
        self.ex_category.set(category or ""); self.ex_name.insert(0, name or ""); self.ex_duration.insert(0, str(dur or "")); self.ex_repetitions.insert(0, rep or ""); self.ex_space.insert(0, space or "")
        self.text_widgets["description"].insert("1.0", desc or ""); self.text_widgets["objectives"].insert("1.0", obj or ""); self.text_widgets["rules"].insert("1.0", rules or ""); self.text_widgets["variants"].insert("1.0", var or "")
        self.image_path = img_path; self.load_image(img_path)

    def select_image(self):
        path = filedialog.askopenfilename(filetypes=[("Archivos de imagen", "*.jpg *.jpeg *.png")])
        if path:
            filename = os.path.basename(path); dest_folder = "data/exercise_images"; dest_path = os.path.join(dest_folder, filename)
            if not os.path.exists(dest_folder): os.makedirs(dest_folder)
            if os.path.normpath(path) != os.path.normpath(os.path.abspath(dest_path)):
                shutil.copy(path, dest_path)
            self.image_path = dest_path; self.load_image(dest_path)

    def load_image(self, path):
        if not path: self.image_label.config(image='', text="Sin Imagen"); self.exercise_image = None; return
        try:
            full_path = resource_path(path)
            if os.path.exists(full_path):
                img = Image.open(full_path); img.thumbnail((300, 200), Image.LANCZOS)
                self.exercise_image = ImageTk.PhotoImage(img); self.image_label.config(image=self.exercise_image, text="")
            else: self.image_label.config(image='', text="Sin Imagen"); self.exercise_image = None
        except Exception as e:
            print(f"Error al cargar imagen: {e}"); self.image_label.config(image='', text="Error Imagen")

    def save(self):
        duration = int(self.ex_duration.get()) if self.ex_duration.get().isdigit() else 0
        data = (None, self.ex_name.get(), self.text_widgets["description"].get("1.0", tk.END).strip(),
                duration, self.ex_repetitions.get(), self.ex_space.get(), self.text_widgets["objectives"].get("1.0", tk.END).strip(),
                self.text_widgets["rules"].get("1.0", tk.END).strip(), self.text_widgets["variants"].get("1.0", tk.END).strip(),
                self.image_path, self.ex_category.get())
        self.db.update_exercise(self.exercise_id, *data)
        messagebox.showinfo("Éxito", "Ejercicio actualizado.", parent=self)
        self.refresh_callback(); self.destroy()