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

class PlayersTab:
    def __init__(self, notebook, db):
        self.db = db
        self.frame = ttk.Frame(notebook)
        self.photo_path = None
        self.photo_image = None
        self.current_player_id = None
        self.form_widgets = []
        
        if not os.path.exists("data/player_photos"):
            os.makedirs("data/player_photos")
            
        self.setup_ui()
        self.load_players()
        self.set_form_state('disabled')

    def setup_ui(self):
        list_frame = ttk.LabelFrame(self.frame, text="Listado de Jugadores")
        list_frame.pack(side="left", fill="y", padx=10, pady=10)
        
        columns = ("id", "name", "position", "number")
        self.players_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=25)
        self.players_tree.heading("id", text="ID"); self.players_tree.column("id", width=40)
        self.players_tree.heading("name", text="Nombre"); self.players_tree.column("name", width=200)
        self.players_tree.heading("position", text="Posición"); self.players_tree.column("position", width=100)
        self.players_tree.heading("number", text="Nº"); self.players_tree.column("number", width=40)
        self.players_tree.pack(fill="y", expand=True)
        self.players_tree.bind("<<TreeviewSelect>>", self.on_player_select)
        
        list_btn_frame = ttk.Frame(list_frame)
        list_btn_frame.pack(fill="x", pady=5)
        ttk.Button(list_btn_frame, text="Nuevo Jugador", command=self.prepare_new_player).pack(side="left", expand=True)
        ttk.Button(list_btn_frame, text="Eliminar Jugador", command=self.delete_player).pack(side="left", expand=True)

        details_notebook = ttk.Notebook(self.frame)
        details_notebook.pack(side="right", fill="both", expand=True, pady=10)

        self.setup_personal_tab(details_notebook)
        self.setup_career_tab(details_notebook)
        self.setup_injuries_tab(details_notebook)

    def set_form_state(self, state):
        for widget in self.form_widgets:
            widget_type = widget.winfo_class()
            if widget_type == 'TCombobox':
                widget.config(state='readonly' if state == 'disabled' else 'normal')
            elif widget_type == 'Text':
                 widget.config(state=state)
            else:
                widget.config(state=state)

    def setup_personal_tab(self, notebook):
        personal_frame = ttk.Frame(notebook)
        notebook.add(personal_frame, text="Ficha Personal")
        
        p_frame = ttk.LabelFrame(personal_frame, text="Datos Personales y Ficha")
        p_frame.pack(fill="both", expand=True, padx=10, pady=10)

        top_frame = ttk.Frame(p_frame)
        top_frame.pack(fill="x", pady=5)
        
        photo_container = tk.Frame(top_frame, width=150, height=150, relief="solid", bd=1)
        photo_container.pack_propagate(False) 
        photo_container.pack(side="left", padx=10, anchor="n")

        self.photo_label = tk.Label(photo_container, text="Sin Foto", bg="lightgrey")
        self.photo_label.pack(fill="both", expand=True)
        
        self.select_photo_btn = ttk.Button(top_frame, text="Seleccionar Foto", command=self.select_photo)
        self.select_photo_btn.pack(side="left", anchor="n", pady=5)

        fields_frame = ttk.Frame(top_frame)
        fields_frame.pack(side="left", fill="x", expand=True, padx=10)
        
        ttk.Label(fields_frame, text="Nombre Completo:").grid(row=0, column=0, sticky="w", pady=2)
        self.player_name = ttk.Entry(fields_frame, width=40); self.player_name.grid(row=0, column=1, columnspan=3, sticky="ew")
        ttk.Label(fields_frame, text="Nombre en Camiseta:").grid(row=1, column=0, sticky="w", pady=2)
        self.player_shirt_name = ttk.Entry(fields_frame); self.player_shirt_name.grid(row=1, column=1, columnspan=3, sticky="ew")
        ttk.Label(fields_frame, text="Posición:").grid(row=2, column=0, sticky="w", pady=2)
        self.player_position = ttk.Combobox(fields_frame, values=["Portero", "Defensa", "Mediocentro", "Delantero"]); self.player_position.grid(row=2, column=1, sticky="ew")
        ttk.Label(fields_frame, text="Número:").grid(row=2, column=2, sticky="w", pady=2, padx=5)
        self.player_number = ttk.Entry(fields_frame); self.player_number.grid(row=2, column=3, sticky="ew")
        ttk.Label(fields_frame, text="Fecha de Nacimiento:").grid(row=3, column=0, sticky="w", pady=2)
        self.player_dob = ttk.Entry(fields_frame); self.player_dob.grid(row=3, column=1, sticky="ew")
        ttk.Label(fields_frame, text="Nacionalidad:").grid(row=3, column=2, sticky="w", pady=2, padx=5)
        self.player_nationality = ttk.Entry(fields_frame); self.player_nationality.grid(row=3, column=3, sticky="ew")
        ttk.Label(fields_frame, text="Pie Dominante:").grid(row=4, column=0, sticky="w", pady=2)
        self.player_foot = ttk.Combobox(fields_frame, values=["Derecho", "Izquierdo", "Ambidiestro"]); self.player_foot.grid(row=4, column=1, sticky="ew")
        ttk.Label(fields_frame, text="Altura (cm):").grid(row=5, column=0, sticky="w", pady=2)
        self.player_height = ttk.Entry(fields_frame); self.player_height.grid(row=5, column=1, sticky="ew")
        ttk.Label(fields_frame, text="Peso (kg):").grid(row=5, column=2, sticky="w", pady=2, padx=5)
        self.player_weight = ttk.Entry(fields_frame); self.player_weight.grid(row=5, column=3, sticky="ew")

        # --- NUEVOS CAMPOS ---
        contact_frame = ttk.LabelFrame(p_frame, text="Información de Contacto")
        contact_frame.pack(fill="x", pady=10, padx=5)
        ttk.Label(contact_frame, text="Teléfono:").grid(row=0, column=0, sticky="w", pady=2, padx=5)
        self.player_phone = ttk.Entry(contact_frame); self.player_phone.grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Label(contact_frame, text="Email:").grid(row=0, column=2, sticky="w", pady=2, padx=5)
        self.player_email = ttk.Entry(contact_frame, width=30); self.player_email.grid(row=0, column=3, sticky="ew", padx=5)
        ttk.Label(contact_frame, text="Dirección:").grid(row=1, column=0, sticky="w", pady=2, padx=5)
        self.player_address = ttk.Entry(contact_frame, width=40); self.player_address.grid(row=1, column=1, columnspan=3, sticky="ew", padx=5)
        ttk.Label(contact_frame, text="Población:").grid(row=2, column=0, sticky="w", pady=2, padx=5)
        self.player_town = ttk.Entry(contact_frame); self.player_town.grid(row=2, column=1, sticky="ew", padx=5)
        ttk.Label(contact_frame, text="Ciudad:").grid(row=2, column=2, sticky="w", pady=2, padx=5)
        self.player_city = ttk.Entry(contact_frame); self.player_city.grid(row=2, column=3, sticky="ew", padx=5)

        obs_frame = ttk.LabelFrame(p_frame, text="Observaciones"); obs_frame.pack(fill="both", expand=True, pady=10, padx=5)
        self.player_observations = tk.Text(obs_frame, height=4); self.player_observations.pack(fill="both", expand=True)
        
        bottom_frame = ttk.Frame(p_frame); bottom_frame.pack(fill="x", pady=10)
        self.mode_label = ttk.Label(bottom_frame, text="Seleccione un jugador o cree uno nuevo", font=("Arial", 10, "italic")); self.mode_label.pack(side="left", padx=5)
        self.edit_player_btn = ttk.Button(bottom_frame, text="Editar Ficha", command=self.enable_editing, state="disabled"); self.edit_player_btn.pack(side="right", padx=5)
        ttk.Button(bottom_frame, text="Guardar / Actualizar Ficha", command=self.save_player_changes).pack(side="right")
        
        self.form_widgets = [self.player_name, self.player_shirt_name, self.player_position, self.player_number, 
                             self.player_dob, self.player_nationality, self.player_foot, self.player_height, self.player_weight,
                             self.player_phone, self.player_email, self.player_address, self.player_town, self.player_city,
                             self.player_observations, self.select_photo_btn, self.edit_player_btn]

    def on_player_select(self, event=None):
        if not self.players_tree.selection(): return
        self.current_player_id = self.players_tree.item(self.players_tree.selection()[0])['values'][0]
        player_data = self.db.get_player_by_id(self.current_player_id)
        
        if player_data:
            self.set_form_state('normal')
            self.clear_form_fields()
            
            (pid, name, pos, num, dob, nat, foot, h, w, photo, obs, s_name, phone, email, addr, town, city) = player_data
            
            self.player_name.insert(0, name or ""); self.player_shirt_name.insert(0, s_name or "")
            self.player_position.set(pos or ""); self.player_number.insert(0, str(num) if num is not None else "")
            self.player_dob.insert(0, dob or ""); self.player_nationality.insert(0, nat or "")
            self.player_foot.set(foot or ""); self.player_height.insert(0, str(h) if h is not None else "")
            self.player_weight.insert(0, str(w) if w is not None else "")
            self.player_observations.insert("1.0", obs or "")
            self.player_phone.insert(0, phone or ""); self.player_email.insert(0, email or "")
            self.player_address.insert(0, addr or ""); self.player_town.insert(0, town or "")
            self.player_city.insert(0, city or "")
            
            self.photo_path = photo
            self.load_player_photo(self.photo_path)
            
            self.set_form_state('disabled')
            self.edit_player_btn.config(state='normal')
            self.mode_label.config(text=f"Modo: Viendo a {name}")
            
            self.load_career_history(); self.load_injuries()

    def save_player_changes(self):
        name = self.player_name.get()
        if not name: messagebox.showwarning("Faltan Datos", "El nombre es obligatorio."); return
        
        player_data = (
            name, self.player_position.get(),
            int(self.player_number.get()) if self.player_number.get().isdigit() else None,
            self.player_dob.get(), self.player_nationality.get(), self.player_foot.get(),
            int(self.player_height.get()) if self.player_height.get().isdigit() else None,
            int(self.player_weight.get()) if self.player_weight.get().isdigit() else None,
            self.photo_path, self.player_observations.get("1.0", tk.END).strip(), self.player_shirt_name.get(),
            self.player_phone.get(), self.player_email.get(), self.player_address.get(),
            self.player_town.get(), self.player_city.get()
        )

        if self.current_player_id: 
            self.db.update_player(self.current_player_id, *player_data)
            messagebox.showinfo("Éxito", "Jugador actualizado.")
        else: 
            self.current_player_id = self.db.insert_player(*player_data)
            messagebox.showinfo("Éxito", "Nuevo jugador creado.")
        
        self.load_players()
        self.set_form_state('disabled')
        self.edit_player_btn.config(state='normal'); self.mode_label.config(text=f"Modo: Viendo a {name}")

    def clear_form_fields(self):
        for widget in self.form_widgets:
            if isinstance(widget, tk.Text): widget.delete("1.0", tk.END)
            elif isinstance(widget, ttk.Combobox): widget.set('')
            elif isinstance(widget, ttk.Entry): widget.delete(0, tk.END)
        
        self.photo_path = None; self.load_player_photo(None)
        if hasattr(self, 'career_tree'):
            for item in self.career_tree.get_children(): self.career_tree.delete(item)
        if hasattr(self, 'injuries_tree'):
            for item in self.injuries_tree.get_children(): self.injuries_tree.delete(item)
            
    def load_player_photo(self, path):
        if not path:
             self.photo_label.config(image='', text="Sin Foto"); self.photo_image = None
             return
        try:
            full_path = resource_path(path)
            if os.path.exists(full_path):
                img = Image.open(full_path); img.thumbnail((150, 150), Image.LANCZOS)
                self.photo_image = ImageTk.PhotoImage(img)
                self.photo_label.config(image=self.photo_image, text="")
            else:
                self.photo_label.config(image='', text="Sin Foto"); self.photo_image = None
        except Exception as e:
            print(f"Error al cargar imagen de jugador: {e}"); self.photo_label.config(image='', text="Error Foto")

    def setup_career_tab(self, notebook):
        career_frame = ttk.Frame(notebook); notebook.add(career_frame, text="Trayectoria y Estadísticas")
        tree_frame = ttk.Frame(career_frame); tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        cols = ('id', 'season', 'team', 'matches', 'goals', 'assists', 'yc', 'rc')
        self.career_tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        for col in cols: self.career_tree.heading(col, text=col.capitalize())
        self.career_tree.column('id', width=0, stretch=tk.NO)
        self.career_tree.pack(fill="both", expand=True)
        btn_frame = ttk.Frame(career_frame); btn_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(btn_frame, text="Añadir Ficha", command=self.add_career_entry).pack(side="left")
        ttk.Button(btn_frame, text="Editar Ficha", command=self.edit_career_entry).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Eliminar Ficha", command=self.delete_career_entry).pack(side="left")

    def setup_injuries_tab(self, notebook):
        injuries_frame = ttk.Frame(notebook); notebook.add(injuries_frame, text="Historial de Lesiones")
        tree_frame = ttk.Frame(injuries_frame); tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        cols = ('id', 'date', 'type', 'recovery', 'notes')
        self.injuries_tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        for col in cols: self.injuries_tree.heading(col, text=col.capitalize())
        self.injuries_tree.column('id', width=0, stretch=tk.NO)
        self.injuries_tree.pack(fill="both", expand=True)
        btn_frame = ttk.Frame(injuries_frame); btn_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(btn_frame, text="Añadir Lesión", command=self.add_injury_entry).pack(side="left")
        ttk.Button(btn_frame, text="Editar Lesión", command=self.edit_injury_entry).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Eliminar Lesión", command=self.delete_injury_entry).pack(side="left")

    def load_players(self):
        for item in self.players_tree.get_children(): self.players_tree.delete(item)
        for p in self.db.get_all_players(): self.players_tree.insert("", tk.END, values=p[:4])

    def enable_editing(self):
        if not self.current_player_id: messagebox.showwarning("Sin selección", "No hay un jugador seleccionado."); return
        self.set_form_state('normal')
        self.mode_label.config(text=f"Modo: Editando a {self.player_name.get()}")
        self.edit_player_btn.config(state='disabled')

    def delete_player(self):
        if not self.current_player_id: messagebox.showwarning("Sin Selección", "Selecciona un jugador para eliminar."); return
        if messagebox.askyesno("Confirmar", f"¿Seguro que quieres eliminar a {self.player_name.get()} y toda su información asociada?"):
            self.db.delete_player(self.current_player_id); self.prepare_new_player(); self.load_players()
            messagebox.showinfo("Eliminado", "Jugador eliminado.")

    def prepare_new_player(self):
        self.current_player_id = None; self.set_form_state('normal'); self.clear_form_fields()
        self.mode_label.config(text="Modo: Creando Nuevo Jugador"); self.edit_player_btn.config(state='disabled')
        if self.players_tree.selection(): self.players_tree.selection_remove(self.players_tree.selection())

    def select_photo(self):
        path = filedialog.askopenfilename(filetypes=[("Archivos de imagen", "*.jpg *.jpeg *.png")])
        if path:
            filename = os.path.basename(path)
            dest_folder = "data/player_photos"
            if not os.path.exists(dest_folder): os.makedirs(dest_folder)
            dest_path = os.path.join(dest_folder, filename)
            shutil.copy(path, dest_path); self.photo_path = dest_path
            self.load_player_photo(self.photo_path)

    def load_career_history(self):
        for item in self.career_tree.get_children(): self.career_tree.delete(item)
        if self.current_player_id:
            for entry in self.db.get_career_history_for_player(self.current_player_id): self.career_tree.insert("", tk.END, values=entry)

    def add_career_entry(self):
        if not self.current_player_id: messagebox.showwarning("Sin Jugador", "Debes seleccionar o crear un jugador primero."); return
        CareerWindow(self.frame, self.db, self.current_player_id, self.load_career_history)

    def edit_career_entry(self):
        if not self.career_tree.selection(): messagebox.showwarning("Sin Selección", "Selecciona una ficha de la trayectoria."); return
        entry_id = self.career_tree.item(self.career_tree.selection()[0])['values'][0]
        entry_data = next((item for item in self.db.get_career_history_for_player(self.current_player_id) if item[0] == entry_id), None)
        CareerWindow(self.frame, self.db, self.current_player_id, self.load_career_history, entry_data)

    def delete_career_entry(self):
        if not self.career_tree.selection(): messagebox.showwarning("Sin Selección", "Selecciona una ficha para eliminar."); return
        entry_id = self.career_tree.item(self.career_tree.selection()[0])['values'][0]
        if messagebox.askyesno("Confirmar", "¿Eliminar esta ficha de la trayectoria?"): self.db.delete_career_entry(entry_id); self.load_career_history()
    
    def load_injuries(self):
        for item in self.injuries_tree.get_children(): self.injuries_tree.delete(item)
        if self.current_player_id:
            for injury in self.db.get_injuries_for_player(self.current_player_id): self.injuries_tree.insert("", tk.END, values=injury)

    def add_injury_entry(self):
        if not self.current_player_id: messagebox.showwarning("Sin Jugador", "Debes seleccionar o crear un jugador primero."); return
        InjuryWindow(self.frame, self.db, self.current_player_id, self.load_injuries)

    def edit_injury_entry(self):
        if not self.injuries_tree.selection(): messagebox.showwarning("Sin Selección", "Selecciona una lesión para editar."); return
        injury_id = self.injuries_tree.item(self.injuries_tree.selection()[0])['values'][0]
        injury_data = next((item for item in self.db.get_injuries_for_player(self.current_player_id) if item[0] == injury_id), None)
        InjuryWindow(self.frame, self.db, self.current_player_id, self.load_injuries, injury_data)

    def delete_injury_entry(self):
        if not self.injuries_tree.selection(): messagebox.showwarning("Sin Selección", "Selecciona una lesión para eliminar."); return
        injury_id = self.injuries_tree.item(self.injuries_tree.selection()[0])['values'][0]
        if messagebox.askyesno("Confirmar", "¿Eliminar esta lesión del historial?"): self.db.delete_injury(injury_id); self.load_injuries()

# --- CLASES DE VENTANAS EMERGENTES RESTAURADAS ---
class CareerWindow(tk.Toplevel):
    def __init__(self, parent, db, player_id, refresh_callback, data=None):
        super().__init__(parent); self.db=db; self.player_id=player_id; self.refresh_callback=refresh_callback; self.entry_id=data[0] if data else None
        self.title("Ficha de Trayectoria"); self.geometry("400x350"); self.transient(parent); self.grab_set()
        frame=ttk.Frame(self,padding=10); frame.pack(fill="both",expand=True)
        labels = ["Temporada (ej: 2024-25):", "Nombre del Equipo:", "Partidos Jugados:", "Goles Marcados:", "Asistencias:", "Tarjetas Amarillas:", "Tarjetas Rojas:", "*Paradas (portero):", "*Goles Encajados (portero):"]
        self.entries = {}
        for i, label_text in enumerate(labels):
            ttk.Label(frame, text=label_text).grid(row=i, column=0, sticky="w", pady=2)
            entry = ttk.Entry(frame); entry.grid(row=i, column=1, sticky="ew")
            self.entries[label_text] = entry
        if data:
            values = data[2:];
            for i, key in enumerate(self.entries): self.entries[key].insert(0, values[i] or "")
        ttk.Button(frame, text="Guardar", command=self.save).grid(row=len(labels), column=0, columnspan=2, pady=10)
    def save(self):
        def to_int(v): return int(v) if str(v).isdigit() else 0
        data = {'player_id': self.player_id, 'season': self.entries[next(iter(self.entries))].get(), **{k.split(' ')[0].lower(): (to_int(v.get()) if 'Tarjetas' in k or 'Partidos' in k or 'Goles' in k or 'Asistencias' in k or 'Paradas' in k else v.get()) for k, v in list(self.entries.items())[1:]}}
        if self.entry_id: self.db.update_career_entry(self.entry_id, data)
        else: self.db.insert_career_entry(data)
        self.refresh_callback(); self.destroy()

class InjuryWindow(tk.Toplevel):
    def __init__(self, parent, db, player_id, refresh_callback, data=None):
        super().__init__(parent); self.db=db; self.player_id=player_id; self.refresh_callback=refresh_callback; self.injury_id=data[0] if data else None
        self.title("Registro de Lesión"); self.geometry("400x300"); self.transient(parent); self.grab_set()
        frame=ttk.Frame(self,padding=10); frame.pack(fill="both",expand=True)
        ttk.Label(frame, text="Fecha de la Lesión:").grid(row=0, column=0, sticky="w", pady=2); self.date=ttk.Entry(frame); self.date.grid(row=0, column=1, sticky="ew")
        ttk.Label(frame, text="Tipo de Lesión:").grid(row=1, column=0, sticky="w", pady=2); self.type=ttk.Entry(frame); self.type.grid(row=1, column=1, sticky="ew")
        ttk.Label(frame, text="Periodo de Recuperación:").grid(row=2, column=0, sticky="w", pady=2); self.recovery=ttk.Entry(frame); self.recovery.grid(row=2, column=1, sticky="ew")
        ttk.Label(frame, text="Notas Adicionales:").grid(row=3, column=0, sticky="w", pady=2); self.notes=tk.Text(frame, height=5); self.notes.grid(row=4, column=0, columnspan=2, sticky="ew")
        if data: self.date.insert(0, data[2]); self.type.insert(0, data[3]); self.recovery.insert(0, data[4]); self.notes.insert("1.0", data[5])
        ttk.Button(frame, text="Guardar", command=self.save).grid(row=5, column=0, columnspan=2, pady=10)
    def save(self):
        data = {'player_id': self.player_id, 'injury_date': self.date.get(), 'injury_type': self.type.get(), 'recovery_period': self.recovery.get(), 'notes': self.notes.get("1.0", tk.END).strip()}
        if self.injury_id: self.db.update_injury(self.injury_id, data)
        else: self.db.insert_injury(data)
        self.refresh_callback(); self.destroy()