import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkcalendar import DateEntry
from datetime import datetime

class TemplateManagerWindow(tk.Toplevel):
    """Ventana para Cargar y Eliminar plantillas."""
    def __init__(self, parent, db, target_training_id, refresh_callback):
        super().__init__(parent)
        self.db = db
        self.target_training_id = target_training_id
        self.refresh_callback = refresh_callback
        
        self.title("Gestionar Plantillas")
        self.geometry("400x350")
        self.transient(parent)
        self.grab_set()

        list_frame = ttk.LabelFrame(self, text="Plantillas Guardadas")
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.template_list = tk.Listbox(list_frame)
        self.template_list.pack(fill="both", expand=True)
        self.populate_list()

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(btn_frame, text="Cargar", command=self.load_selected).pack(side="left", expand=True)
        ttk.Button(btn_frame, text="Eliminar", command=self.delete_selected).pack(side="left", expand=True)

    def populate_list(self):
        self.template_list.delete(0, tk.END)
        self.templates = self.db.get_all_templates()
        for t_id, name in self.templates:
            self.template_list.insert(tk.END, name)

    def get_selected_template_id(self):
        selected_indices = self.template_list.curselection()
        if not selected_indices:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione una plantilla.", parent=self)
            return None
        return self.templates[selected_indices[0]][0]

    def load_selected(self):
        template_id = self.get_selected_template_id()
        if not template_id: return

        if not self.target_training_id:
            messagebox.showerror("Error", "No hay un entrenamiento de destino seleccionado.", parent=self)
            return

        if messagebox.askyesno("Confirmar Carga", 
                               "¿Seguro? Esto reemplazará todos los ejercicios y la planificación del entrenamiento de destino.", 
                               parent=self):
            success = self.db.load_template_to_training(template_id, self.target_training_id)
            if success:
                messagebox.showinfo("Éxito", "Plantilla cargada correctamente.", parent=self)
                self.refresh_callback()
                self.destroy()
            else:
                messagebox.showerror("Error", "No se pudo cargar la plantilla.", parent=self)

    def delete_selected(self):
        template_id = self.get_selected_template_id()
        if not template_id: return
        
        if messagebox.askyesno("Confirmar Eliminación", "¿Está seguro de que desea eliminar esta plantilla?", parent=self):
            self.db.delete_template(template_id)
            messagebox.showinfo("Eliminado", "Plantilla eliminada.", parent=self)
            self.populate_list()

class TrainingsTab:
    def __init__(self, notebook, db):
        self.db = db
        self.frame = ttk.Frame(notebook)
        self.current_editing_id = None
        self.setup_ui()
        self.refresh_data()
    
    def setup_ui(self):
        add_frame = ttk.LabelFrame(self.frame, text="Detalles del Entrenamiento")
        add_frame.pack(fill="x", padx=10, pady=10)

        add_frame.columnconfigure(1, weight=1)
        add_frame.columnconfigure(4, weight=1)

        # --- Fila 1: Fecha y Hora ---
        ttk.Label(add_frame, text="Fecha y Hora:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        datetime_frame = ttk.Frame(add_frame)
        datetime_frame.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.training_date = DateEntry(datetime_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd/MM/yyyy')
        self.training_date.pack(side="left")

        # Selectores para hora y minutos
        hours = [f"{h:02}" for h in range(24)]
        minutes = [f"{m:02}" for m in range(0, 60, 5)]
        self.training_hour = ttk.Combobox(datetime_frame, values=hours, width=3)
        self.training_hour.pack(side="left", padx=(5, 2))
        ttk.Label(datetime_frame, text=":").pack(side="left")
        self.training_minute = ttk.Combobox(datetime_frame, values=minutes, width=3)
        self.training_minute.pack(side="left", padx=2)
        
        # --- Fila 1 (continuación): Mesociclo y Sesión ---
        ttk.Label(add_frame, text="Mesociclo:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.training_mesocycle = ttk.Entry(add_frame)
        self.training_mesocycle.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        ttk.Label(add_frame, text="Nº Sesión:").grid(row=0, column=4, padx=(10, 5), pady=5, sticky="w")
        self.training_session = ttk.Entry(add_frame, width=10)
        self.training_session.grid(row=0, column=5, padx=5, pady=5, sticky="w")

        # --- Fila 2: Entrenadores ---
        ttk.Label(add_frame, text="Entrenador Principal:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.training_coach = ttk.Combobox(add_frame)
        self.training_coach.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(add_frame, text="Asistente:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.training_assistant = ttk.Combobox(add_frame)
        self.training_assistant.grid(row=1, column=3, columnspan=3, padx=5, pady=5, sticky="ew")

        # --- Fila 3: Material ---
        ttk.Label(add_frame, text="Material Necesario:").grid(row=2, column=0, padx=5, pady=5, sticky="nw")
        material_frame = ttk.Frame(add_frame)
        material_frame.grid(row=2, column=1, columnspan=5, padx=5, pady=5, sticky="nsew")
        material_frame.rowconfigure(0, weight=1)
        material_frame.columnconfigure(0, weight=1)
        self.training_material = tk.Text(material_frame, height=4, wrap="word")
        self.training_material.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(material_frame, orient="vertical", command=self.training_material.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.training_material.config(yscrollcommand=scrollbar.set)
        
        # --- Fila 4: Botones ---
        btn_frame_add = ttk.Frame(add_frame)
        btn_frame_add.grid(row=3, column=0, columnspan=6, pady=10, sticky="e")
        ttk.Button(btn_frame_add, text="Limpiar Formulario", command=self.clear_form).pack(side="left", padx=5)
        ttk.Button(btn_frame_add, text="Guardar Cambios", command=self.save_training).pack(side="left", padx=5)
        ttk.Button(btn_frame_add, text="Crear Nuevo Entrenamiento", command=self.add_training).pack(side="left", padx=5)
        
        # --- Listado ---
        list_frame = ttk.LabelFrame(self.frame, text="Entrenamientos Programados")
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        columns = ("id", "date", "mesociclo", "session", "coach", "assistant", "material")
        self.trainings_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        for col in columns: self.trainings_tree.heading(col, text=col.capitalize())
        self.trainings_tree.column("id", width=40)
        self.trainings_tree.pack(fill="both", expand=True)
        
        bottom_frame = ttk.Frame(list_frame)
        bottom_frame.pack(fill="x", pady=5)

        actions_frame = ttk.LabelFrame(bottom_frame, text="Acciones de Entrenamiento")
        actions_frame.pack(side="left", padx=5, fill="x", expand=True)
        ttk.Button(actions_frame, text="Recargar Datos", command=self.refresh_data).pack(side="left", padx=5)
        ttk.Button(actions_frame, text="Editar Seleccionado", command=self.edit_training).pack(side="left", padx=5)
        ttk.Button(actions_frame, text="Eliminar Seleccionado", command=self.delete_training).pack(side="left", padx=5)

        template_frame = ttk.LabelFrame(bottom_frame, text="Acciones de Plantilla")
        template_frame.pack(side="right", padx=5, fill="x", expand=True)
        ttk.Button(template_frame, text="Guardar como Plantilla", command=self.save_as_template).pack(side="left", padx=5)
        ttk.Button(template_frame, text="Gestionar Plantillas", command=self.open_template_manager).pack(side="left", padx=5)

    def load_coaches_into_dropdowns(self):
        """Carga los nombres del cuerpo técnico en los menús desplegables."""
        coach_names = self.db.get_all_coach_names()
        self.training_coach['values'] = coach_names
        self.training_assistant['values'] = coach_names

    def refresh_data(self):
        """Recarga tanto la lista de entrenamientos como la de entrenadores."""
        self.load_trainings()
        self.load_coaches_into_dropdowns()

    def clear_form(self):
        """Limpia todos los campos del formulario de detalles."""
        self.current_editing_id = None
        self.training_date.set_date(datetime.now())
        self.training_hour.set(f"{datetime.now().hour:02}")
        self.training_minute.set('00')
        self.training_mesocycle.delete(0, tk.END)
        self.training_session.delete(0, tk.END)
        self.training_coach.set('')
        self.training_assistant.set('')
        self.training_material.delete("1.0", tk.END)
        if self.trainings_tree.selection():
            self.trainings_tree.selection_remove(self.trainings_tree.selection())
    
    def get_datetime_from_form(self):
        """Combina la fecha y la hora de los widgets en un solo string."""
        date_str = self.training_date.get()
        hour_str = self.training_hour.get() or "00"
        minute_str = self.training_minute.get() or "00"
        return f"{date_str} {hour_str}:{minute_str}"

    def add_training(self):
        """Añade un nuevo entrenamiento a la base de datos."""
        date_time_str = self.get_datetime_from_form()
        meso = self.training_mesocycle.get()
        sess = self.training_session.get()
        material = self.training_material.get("1.0", tk.END).strip()

        if date_time_str and meso and sess:
            self.db.insert_training(date_time_str, meso, sess, self.training_coach.get(), self.training_assistant.get(), material)
            self.clear_form()
            self.refresh_data()
            messagebox.showinfo("Éxito", "Entrenamiento añadido correctamente.")
        else:
            messagebox.showwarning("Campos Requeridos", "Debe rellenar los campos: Fecha, Mesociclo y Nº Sesión.")
    
    def save_training(self):
        """Actualiza un entrenamiento existente o pregunta si se quiere crear uno nuevo."""
        if self.current_editing_id is None:
            if messagebox.askyesno("Crear Nuevo Entrenamiento", "No hay ningún entrenamiento seleccionado para editar. ¿Desea crear un nuevo entrenamiento con los datos del formulario?"):
                self.add_training()
            return

        date_time_str = self.get_datetime_from_form()
        meso = self.training_mesocycle.get()
        sess = self.training_session.get()
        material = self.training_material.get("1.0", tk.END).strip()

        if date_time_str and meso and sess:
            self.db.update_training(self.current_editing_id, date_time_str, meso, sess, self.training_coach.get(), self.training_assistant.get(), material)
            self.clear_form()
            self.refresh_data()
            messagebox.showinfo("Éxito", "Entrenamiento actualizado correctamente.")
        else:
            messagebox.showwarning("Campos Requeridos", "Debe rellenar los campos: Fecha, Mesociclo y Nº Sesión.")

    def load_trainings(self):
        for item in self.trainings_tree.get_children(): self.trainings_tree.delete(item)
        for training in self.db.get_all_trainings():
            self.trainings_tree.insert("", tk.END, values=training)
    
    def get_selected_training_id(self):
        selected_items = self.trainings_tree.selection()
        if not selected_items:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un entrenamiento de la lista.")
            return None
        return self.trainings_tree.item(selected_items[0])['values'][0]

    def edit_training(self):
        """Carga los datos del entrenamiento seleccionado en el formulario de detalles."""
        selected_items = self.trainings_tree.selection()
        if not selected_items:
            messagebox.showwarning("Advertencia", "Seleccione un entrenamiento para editar.")
            return
        
        values = self.trainings_tree.item(selected_items[0])['values']
        tid, date_str, meso, sess, coach, assist, mat = values
        
        self.clear_form()
        self.current_editing_id = tid
        
        # Separar fecha y hora
        try:
            dt_obj = datetime.strptime(date_str, '%d/%m/%Y %H:%M')
            self.training_date.set_date(dt_obj)
            self.training_hour.set(f"{dt_obj.hour:02}")
            self.training_minute.set(f"{dt_obj.minute:02}")
        except (ValueError, TypeError):
            # Si el formato es antiguo o incorrecto, intenta solo con la fecha
            try:
                dt_obj = datetime.strptime(date_str, '%d/%m/%Y')
                self.training_date.set_date(dt_obj)
                self.training_hour.set("00")
                self.training_minute.set("00")
            except (ValueError, TypeError):
                self.training_date.set_date(datetime.now()) # Valor por defecto
                self.training_hour.set(f"{datetime.now().hour:02}")
                self.training_minute.set("00")

        self.training_mesocycle.insert(0, meso or "")
        self.training_session.insert(0, str(sess) if sess is not None else "")
        self.training_coach.set(coach or "")
        self.training_assistant.set(assist or "")
        self.training_material.insert("1.0", mat or "")

    def delete_training(self):
        """Elimina el entrenamiento seleccionado."""
        tid = self.get_selected_training_id()
        if not tid: return
        
        if messagebox.askyesno("Confirmar Eliminación", 
                               "¿Seguro que quieres eliminar este entrenamiento?\nSe borrarán todos sus ejercicios y planificaciones de asistencia asociados de forma permanente."):
            try:
                self.db.delete_training(tid)
                self.refresh_data()
                self.clear_form()
                messagebox.showinfo("Eliminado", "El entrenamiento ha sido eliminado correctamente.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar el entrenamiento.\n\nError: {e}")

    def save_as_template(self):
        training_id = self.get_selected_training_id()
        if not training_id: return

        name = simpledialog.askstring("Guardar Plantilla", "Introduce un nombre para la plantilla:", parent=self.frame)
        if name and name.strip():
            success = self.db.save_training_as_template(training_id, name.strip())
            if success:
                messagebox.showinfo("Éxito", f"Plantilla '{name}' guardada correctamente.")
            else:
                messagebox.showerror("Error", "No se pudo guardar la plantilla. ¿Ya existe una con ese nombre?")
    
    def open_template_manager(self):
        target_id = self.get_selected_training_id()
        if not target_id: return
        TemplateManagerWindow(self.frame, self.db, target_id, self.refresh_data)