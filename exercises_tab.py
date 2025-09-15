import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import os
import shutil
import sys

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class ExercisesTab:
    def __init__(self, notebook, db):
        self.db = db
        self.frame = ttk.Frame(notebook)
        self.image_path = None
        self.current_exercise_id = None
        self.exercise_image = None
        
        if not os.path.exists("data/exercise_images"):
            os.makedirs("data/exercise_images")

        self.setup_ui()
        self.refresh_trainings_dropdown()
        self.load_all_exercises()
        self.set_form_state('disabled')

    def setup_ui(self):
        main_frame = ttk.Frame(self.frame, padding=10)
        main_frame.pack(fill="both", expand=True)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        list_frame = ttk.LabelFrame(main_frame, text="Listado de Ejercicios")
        list_frame.grid(row=0, column=0, sticky="ns", padx=(0, 10))
        
        cols = ("id", "name")
        self.exercises_tree = ttk.Treeview(list_frame, columns=cols, show="headings", height=25)
        self.exercises_tree.heading("id", text="ID"); self.exercises_tree.column("id", width=40)
        self.exercises_tree.heading("name", text="Nombre del Ejercicio"); self.exercises_tree.column("name", width=250)
        self.exercises_tree.pack(fill="y", expand=True, side="top")
        self.exercises_tree.bind("<<TreeviewSelect>>", self.on_exercise_select)
        
        list_btn_frame = ttk.Frame(list_frame)
        list_btn_frame.pack(fill="x", pady=5)
        ttk.Button(list_btn_frame, text="Nuevo Ejercicio", command=self.prepare_new_exercise).pack(side="left", expand=True)
        ttk.Button(list_btn_frame, text="Eliminar", command=self.delete_exercise).pack(side="left", expand=True)

        details_frame = ttk.LabelFrame(main_frame, text="Detalles del Ejercicio")
        details_frame.grid(row=0, column=1, sticky="nsew")

        form_frame = ttk.Frame(details_frame, padding=10)
        form_frame.pack(fill="both", expand=True)
        form_frame.columnconfigure(1, weight=1)

        ttk.Label(form_frame, text="Categoría:").grid(row=0, column=0, sticky="w", pady=3)
        self.exercise_category = ttk.Combobox(form_frame, values=["Calentamiento", "Físico", "Técnico", "Táctico", "Estrategia", "Vuelta a la Calma"])
        self.exercise_category.grid(row=0, column=1, sticky="ew")

        ttk.Label(form_frame, text="Asociar a Entrenamiento:").grid(row=1, column=0, sticky="w", pady=3)
        self.training_dropdown = ttk.Combobox(form_frame, state="readonly")
        self.training_dropdown.grid(row=1, column=1, sticky="ew")
        
        ttk.Label(form_frame, text="Nombre del Ejercicio:").grid(row=2, column=0, sticky="w", pady=3)
        self.exercise_name = ttk.Entry(form_frame)
        self.exercise_name.grid(row=2, column=1, sticky="ew")
        
        ttk.Label(form_frame, text="Duración (min):").grid(row=3, column=0, sticky="w", pady=3)
        self.exercise_duration = ttk.Entry(form_frame)
        self.exercise_duration.grid(row=3, column=1, sticky="ew")
        
        ttk.Label(form_frame, text="Repeticiones/Series:").grid(row=4, column=0, sticky="w", pady=3)
        self.exercise_repetitions = ttk.Entry(form_frame)
        self.exercise_repetitions.grid(row=4, column=1, sticky="ew")
        
        ttk.Label(form_frame, text="Espacio/Dimensiones:").grid(row=5, column=0, sticky="w", pady=3)
        self.exercise_space = ttk.Entry(form_frame)
        self.exercise_space.grid(row=5, column=1, sticky="ew")

        notebook = ttk.Notebook(form_frame); notebook.grid(row=6, column=0, columnspan=2, sticky="ew", pady=10)
        
        desc_frame = ttk.Frame(notebook); notebook.add(desc_frame, text='Descripción')
        self.exercise_description = tk.Text(desc_frame, height=4); self.exercise_description.pack(fill="x")
        
        obj_frame = ttk.Frame(notebook); notebook.add(obj_frame, text='Objetivos')
        self.exercise_objectives = tk.Text(obj_frame, height=4); self.exercise_objectives.pack(fill="x")
        
        rules_frame = ttk.Frame(notebook); notebook.add(rules_frame, text='Reglas')
        self.exercise_rules = tk.Text(rules_frame, height=4); self.exercise_rules.pack(fill="x")
        
        var_frame = ttk.Frame(notebook); notebook.add(var_frame, text='Variantes')
        self.exercise_variants = tk.Text(var_frame, height=4); self.exercise_variants.pack(fill="x")
        
        bottom_frame = ttk.Frame(form_frame)
        bottom_frame.grid(row=7, column=0, columnspan=2, sticky="ew")
        
        image_container = tk.Frame(bottom_frame, width=300, height=200, relief="solid", bd=1)
        image_container.pack_propagate(False)
        image_container.pack(side="left", padx=(0, 10))
        self.image_label = tk.Label(image_container, text="Sin Imagen", bg="lightgrey")
        self.image_label.pack(fill="both", expand=True)

        btn_container = ttk.Frame(bottom_frame)
        btn_container.pack(side="left")
        self.select_image_btn = ttk.Button(btn_container, text="Seleccionar Imagen", command=self.select_image)
        self.select_image_btn.pack(pady=5)
        
        action_buttons_frame = ttk.Frame(form_frame)
        action_buttons_frame.grid(row=8, column=0, columnspan=2, sticky="ew", pady=10)
        
        self.mode_label = ttk.Label(action_buttons_frame, text="Seleccione o cree un ejercicio", font=("Arial", 9, "italic"))
        self.mode_label.pack(side="left", padx=5)
        
        self.save_update_btn = ttk.Button(action_buttons_frame, text="Guardar / Actualizar", command=self.save_exercise_changes)
        self.save_update_btn.pack(side="right")
        
        self.edit_exercise_btn = ttk.Button(action_buttons_frame, text="Editar Ejercicio", command=self.enable_editing)
        self.edit_exercise_btn.pack(side="right", padx=5)
        
        self.form_widgets = [self.training_dropdown, self.exercise_category, self.exercise_name, self.exercise_duration,
                             self.exercise_repetitions, self.exercise_space, self.exercise_objectives,
                             self.exercise_rules, self.exercise_variants, self.exercise_description,
                             self.select_image_btn, self.save_update_btn]

    def set_form_state(self, state):
        for widget in self.form_widgets:
            widget_type = widget.winfo_class()
            if widget_type == 'TCombobox':
                if widget == self.training_dropdown:
                    widget.config(state='readonly' if state == 'normal' else 'disabled')
                else: 
                    widget.config(state='normal' if state == 'normal' else 'disabled')
            elif widget_type == 'Text':
                widget.config(state=state)
            else:
                widget.config(state=state)

    def on_exercise_select(self, event=None):
        selected_item = self.exercises_tree.selection()
        if not selected_item: return
        self.current_exercise_id = self.exercises_tree.item(selected_item[0])['values'][0]
        
        exercise_data = self.db.get_exercise_by_id(self.current_exercise_id)
        
        if exercise_data:
            (eid, tid, name, desc, dur, rep, space, obj, rules, var, img_path, category) = exercise_data
            
            self.clear_form_fields()
            
            training_key_to_set = ""
            if tid is not None:
                for key, value in self.training_data.items():
                    if value == tid:
                        training_key_to_set = key
                        break
            self.training_dropdown.set(training_key_to_set)

            self.exercise_category.set(category or "")
            self.exercise_name.insert(0, name or "")
            self.exercise_duration.insert(0, str(dur) if dur is not None else "")
            self.exercise_repetitions.insert(0, str(rep) if rep is not None else "")
            self.exercise_space.insert(0, space or "")
            self.exercise_description.insert("1.0", desc or "")
            self.exercise_objectives.insert("1.0", obj or "")
            self.exercise_rules.insert("1.0", rules or "")
            self.exercise_variants.insert("1.0", var or "")
            self.image_path = img_path
            self.load_exercise_image(self.image_path)
            
            self.set_form_state('disabled')
            self.edit_exercise_btn.config(state='normal')
            self.mode_label.config(text=f"Viendo: '{name}'")

    def save_exercise_changes(self):
        if not self.exercise_name.get():
            messagebox.showwarning("Faltan Datos", "El nombre del ejercicio es obligatorio.")
            return
        
        selected_training_key = self.training_dropdown.get()
        training_id = self.training_data.get(selected_training_key, None)
        duration = int(self.exercise_duration.get()) if self.exercise_duration.get().isdigit() else 0
        
        data = (
            training_id, self.exercise_name.get(), self.exercise_description.get("1.0", tk.END).strip(), 
            duration, self.exercise_repetitions.get(), self.exercise_space.get(), 
            self.exercise_objectives.get("1.0", tk.END).strip(), self.exercise_rules.get("1.0", tk.END).strip(), 
            self.exercise_variants.get("1.0", tk.END).strip(), self.image_path, self.exercise_category.get()
        )
        
        if self.current_exercise_id is not None:
            self.db.update_exercise(self.current_exercise_id, *data)
            messagebox.showinfo("Éxito", "Ejercicio actualizado correctamente.")
        else:
            self.current_exercise_id = self.db.insert_exercise(*data)
            messagebox.showinfo("Éxito", "Nuevo ejercicio creado correctamente.")
        
        self.load_all_exercises()
        self.set_form_state('disabled')
        self.edit_exercise_btn.config(state='normal')
        self.mode_label.config(text=f"Viendo: '{self.exercise_name.get()}'")

    def clear_form_fields(self):
        self.training_dropdown.set('')
        self.exercise_category.set('')
        self.exercise_name.delete(0, tk.END)
        self.exercise_description.delete("1.0", tk.END)
        self.exercise_duration.delete(0, tk.END)
        self.exercise_repetitions.delete(0, tk.END)
        self.exercise_space.delete(0, tk.END)
        self.exercise_objectives.delete("1.0", tk.END)
        self.exercise_rules.delete("1.0", tk.END)
        self.exercise_variants.delete("1.0", tk.END)
        self.image_path = None
        self.load_exercise_image(None)

    def refresh_trainings_dropdown(self):
        trainings = self.db.get_all_trainings_for_dropdown()
        self.training_data = {f"{t[1]} (Sesión {t[3]})": t[0] for t in trainings}
        self.training_dropdown['values'] = list(self.training_data.keys())

    def load_all_exercises(self):
        for item in self.exercises_tree.get_children(): self.exercises_tree.delete(item)
        all_exercises = self.db.get_exercises_by_training(None)
        for ex in all_exercises:
            self.exercises_tree.insert("", tk.END, values=(ex[0], ex[2]))

    def load_exercise_image(self, path):
        if not path:
            self.image_label.config(image='', text="Sin Imagen")
            self.exercise_image = None
            return
        try:
            full_path = resource_path(path)
            if os.path.exists(full_path):
                img = Image.open(full_path)
                img.thumbnail((300, 200), Image.LANCZOS)
                self.exercise_image = ImageTk.PhotoImage(img)
                self.image_label.config(image=self.exercise_image, text="")
            else:
                self.image_label.config(image='', text="Sin Imagen")
                self.exercise_image = None
        except Exception as e:
            print(f"Error al cargar imagen de ejercicio: {e}")
            self.image_label.config(image='', text="Error Imagen")

    def enable_editing(self):
        if self.current_exercise_id is None: 
            messagebox.showwarning("Sin selección", "No hay ningún ejercicio seleccionado para editar.")
            return
        self.set_form_state('normal')
        self.mode_label.config(text=f"Editando: '{self.exercise_name.get()}'")
        self.edit_exercise_btn.config(state='disabled')

    def delete_exercise(self):
        if self.current_exercise_id is None: 
            messagebox.showwarning("Sin Selección", "Selecciona un ejercicio para eliminar.")
            return
        if messagebox.askyesno("Confirmar", f"¿Seguro que quieres eliminar el ejercicio '{self.exercise_name.get()}'?"):
            self.db.delete_exercise(self.current_exercise_id)
            self.prepare_new_exercise()
            self.load_all_exercises()
            messagebox.showinfo("Eliminado", "El ejercicio ha sido eliminado.")

    def prepare_new_exercise(self):
        self.current_exercise_id = None
        self.clear_form_fields()
        self.set_form_state('normal')
        self.mode_label.config(text="Modo: Creando Nuevo Ejercicio")
        self.edit_exercise_btn.config(state='disabled')
        if self.exercises_tree.selection(): 
            self.exercises_tree.selection_remove(self.exercises_tree.selection())

    def select_image(self):
        path = filedialog.askopenfilename(filetypes=[("Archivos de imagen", "*.jpg *.jpeg *.png")])
        if not path:
            return

        filename = os.path.basename(path)
        dest_folder = "data/exercise_images"
        dest_path = os.path.join(dest_folder, filename)

        try:
            is_same_file = os.path.exists(dest_path) and os.path.samefile(path, dest_path)
        except FileNotFoundError:
            is_same_file = False

        if not is_same_file:
            if not os.path.exists(dest_folder):
                os.makedirs(dest_folder)
            shutil.copy(path, dest_path)
        
        self.image_path = dest_path
        self.load_exercise_image(self.image_path)