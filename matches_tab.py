import tkinter as tk
from tkinter import ttk, messagebox

class MatchesTab:
    def __init__(self, notebook, db):
        self.db = db
        self.frame = ttk.Frame(notebook)
        self.current_match_id = None
        self.form_widgets = {}
        self.stats_tree = None
        self.entry_popup = None
        self.setup_ui()
        self.load_all_matches()
        self.enable_form(False)

    def setup_ui(self):
        main_frame = ttk.Frame(self.frame, padding=10)
        main_frame.pack(fill="both", expand=True)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # Columna Izquierda: Lista de Partidos
        list_frame = ttk.LabelFrame(main_frame, text="Partidos Registrados")
        list_frame.grid(row=0, column=0, sticky="ns", padx=(0, 10))
        
        self.matches_tree = ttk.Treeview(list_frame, columns=("id", "date", "rival", "result"), show="headings", height=25)
        self.matches_tree.heading("id", text="ID"); self.matches_tree.column("id", width=0, stretch=tk.NO)
        self.matches_tree.heading("date", text="Fecha"); self.matches_tree.column("date", width=80)
        self.matches_tree.heading("rival", text="Rival"); self.matches_tree.column("rival", width=120)
        self.matches_tree.heading("result", text="Resultado"); self.matches_tree.column("result", width=70, anchor='center')
        self.matches_tree.pack(fill="y", expand=True, side="top")
        self.matches_tree.bind("<<TreeviewSelect>>", self.on_match_select)

        list_btn_frame = ttk.Frame(list_frame)
        list_btn_frame.pack(fill="x", pady=5)
        ttk.Button(list_btn_frame, text="Nuevo Partido", command=self.prepare_new_match).pack(side="left", expand=True)
        ttk.Button(list_btn_frame, text="Eliminar", command=self.delete_match).pack(side="right", expand=True)

        # Columna Derecha: Pestañas de Detalles y Estadísticas
        details_notebook = ttk.Notebook(main_frame)
        details_notebook.grid(row=0, column=1, sticky="nsew")

        details_tab = ttk.Frame(details_notebook, padding=10)
        stats_tab = ttk.Frame(details_notebook, padding=10)
        details_notebook.add(details_tab, text="Detalles del Partido")
        details_notebook.add(stats_tab, text="Estadísticas de Jugadores")

        # Pestaña de Detalles del Partido
        form_frame = ttk.LabelFrame(details_tab, text="Información del Partido")
        form_frame.pack(fill="x", padx=10, pady=10)
        fields = {"Fecha:": "match_date", "Competición:": "competition", "Rival:": "rival", "Estadio/Lugar:": "venue", "Ciudad:": "city", "Resultado:": "result"}
        for i, (text, name) in enumerate(fields.items()):
            ttk.Label(form_frame, text=text).grid(row=i, column=0, sticky="w", padx=5, pady=2)
            entry = ttk.Entry(form_frame, width=40)
            entry.grid(row=i, column=1, sticky="ew", padx=5)
            self.form_widgets[name] = entry
        self.is_home_var = tk.BooleanVar()
        home_check = ttk.Checkbutton(form_frame, text="Juega en Casa", variable=self.is_home_var)
        home_check.grid(row=len(fields), column=0, columnspan=2, pady=5)
        self.form_widgets['is_home'] = home_check
        ttk.Button(details_tab, text="Guardar Detalles", command=self.save_match_details).pack(pady=10)

        # Pestaña de Estadísticas
        stats_frame = ttk.LabelFrame(stats_tab, text="Estadísticas por Jugador (Doble clic para editar)")
        stats_frame.pack(fill="both", expand=True)
        
        cols = ("id", "name", "num", "mins", "goals", "assists", "shots", "yc", "rc")
        self.stats_tree = ttk.Treeview(stats_frame, columns=cols, show="headings")
        self.stats_tree.heading("id", text="ID"); self.stats_tree.column("id", width=0, stretch=tk.NO)
        self.stats_tree.heading("name", text="Nombre"); self.stats_tree.column("name", width=180)
        self.stats_tree.heading("num", text="Nº"); self.stats_tree.column("num", width=40, anchor='center')
        self.stats_tree.heading("mins", text="Min"); self.stats_tree.column("mins", width=40, anchor='center')
        self.stats_tree.heading("goals", text="G"); self.stats_tree.column("goals", width=40, anchor='center')
        self.stats_tree.heading("assists", text="A"); self.stats_tree.column("assists", width=40, anchor='center')
        self.stats_tree.heading("shots", text="Tiros"); self.stats_tree.column("shots", width=50, anchor='center')
        self.stats_tree.heading("yc", text="TA"); self.stats_tree.column("yc", width=40, anchor='center')
        self.stats_tree.heading("rc", text="TR"); self.stats_tree.column("rc", width=40, anchor='center')
        self.stats_tree.pack(fill="both", expand=True)
        self.stats_tree.bind("<Double-1>", self.edit_cell)
        ttk.Button(stats_tab, text="Guardar Estadísticas", command=self.save_stats).pack(pady=10)

    def edit_cell(self, event):
        if self.entry_popup: self.entry_popup.destroy()
        item_id = self.stats_tree.identify_row(event.y)
        column_id = self.stats_tree.identify_column(event.x)
        if not item_id or column_id in ("#1", "#2", "#3"): return # No editar ID, Nombre o Nº

        x, y, width, height = self.stats_tree.bbox(item_id, column_id)
        value = self.stats_tree.set(item_id, column_id)
        
        self.entry_popup = ttk.Entry(self.stats_tree)
        self.entry_popup.place(x=x, y=y, width=width, height=height)
        self.entry_popup.insert(0, value)
        self.entry_popup.focus_force()
        self.entry_popup.bind("<Return>", lambda e, i=item_id, c=column_id: self.update_cell_value(e, i, c))
        self.entry_popup.bind("<FocusOut>", lambda e, i=item_id, c=column_id: self.update_cell_value(e, i, c))

    def update_cell_value(self, event, item_id, column_id):
        new_value = event.widget.get()
        self.stats_tree.set(item_id, column_id, new_value)
        event.widget.destroy()
        self.entry_popup = None

    def load_all_matches(self):
        for item in self.matches_tree.get_children(): self.matches_tree.delete(item)
        for match in self.db.get_all_matches():
            self.matches_tree.insert("", "end", values=match, iid=match[0])

    def on_match_select(self, event=None):
        selected_items = self.matches_tree.selection()
        if not selected_items: return
        self.current_match_id = int(selected_items[0])
        self.load_match_details()

    def load_match_details(self):
        if not self.current_match_id: return
        self.enable_form(True)
        self.clear_form()
        details = self.db.get_match_details(self.current_match_id)
        if not details: return
        
        _, date, comp, rival, venue, is_home, result = details
        self.form_widgets['match_date'].insert(0, date or "")
        self.form_widgets['competition'].insert(0, comp or "")
        self.form_widgets['rival'].insert(0, rival or "")
        self.form_widgets['venue'].insert(0, venue or "")
        self.form_widgets['city'].insert(0, venue.split(',')[-1].strip() if venue else "") # Intenta autocompletar ciudad
        self.form_widgets['result'].insert(0, result or "")
        self.is_home_var.set(bool(is_home))
        self.load_stats()
    
    def load_stats(self):
        for item in self.stats_tree.get_children(): self.stats_tree.delete(item)
        stats = self.db.get_stats_for_match(self.current_match_id)
        for row in stats:
            self.stats_tree.insert("", "end", values=row, iid=row[0])

    def save_match_details(self):
        if self.form_widgets['rival'].get() == "":
            messagebox.showwarning("Faltan Datos", "El campo 'Rival' es obligatorio.")
            return
        details = {
            'id': self.current_match_id,
            'match_date': self.form_widgets['match_date'].get(),
            'competition': self.form_widgets['competition'].get(),
            'rival': self.form_widgets['rival'].get(),
            'venue': self.form_widgets['venue'].get(),
            'is_home': self.is_home_var.get(),
            'result': self.form_widgets['result'].get(),
        }
        new_id = self.db.save_match(details)
        if not self.current_match_id:
            self.current_match_id = new_id
            self.load_stats() # Cargar la lista de jugadores para el nuevo partido
        self.load_all_matches()
        messagebox.showinfo("Éxito", "Detalles del partido guardados.")

    def save_stats(self):
        if not self.current_match_id:
            messagebox.showwarning("Sin Partido", "Guarde primero los detalles del partido.")
            return
        stats_to_save = []
        for item_id in self.stats_tree.get_children():
            values = self.stats_tree.item(item_id)['values']
            # player_id y las 6 estadísticas (mins, goals, assists, shots, yc, rc)
            stats_to_save.append(values[0:1] + values[3:9]) 
        self.db.save_player_stats_for_match(self.current_match_id, stats_to_save)
        messagebox.showinfo("Éxito", "Estadísticas guardadas correctamente.")

    def delete_match(self):
        selected_items = self.matches_tree.selection()
        if not selected_items:
            messagebox.showwarning("Sin Selección", "Seleccione un partido para eliminar.")
            return
        match_id = int(selected_items[0])
        if messagebox.askyesno("Confirmar", "¿Seguro que quiere eliminar este partido y todas sus estadísticas asociadas?"):
            self.db.delete_match(match_id)
            self.load_all_matches()
            self.prepare_new_match()
            messagebox.showinfo("Eliminado", "Partido eliminado.")

    def prepare_new_match(self):
        self.current_match_id = None
        self.matches_tree.selection_set('')
        self.clear_form()
        self.enable_form(True)
        for item in self.stats_tree.get_children(): self.stats_tree.delete(item)

    def clear_form(self):
        for widget in self.form_widgets.values():
            if isinstance(widget, ttk.Entry): widget.delete(0, tk.END)
            elif isinstance(widget, ttk.Checkbutton): self.is_home_var.set(False)

    def enable_form(self, status):
        state = "normal" if status else "disabled"
        for widget in self.form_widgets.values():
            widget.config(state=state)