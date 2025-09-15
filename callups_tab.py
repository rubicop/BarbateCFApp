import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os
import sys
import json

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- Ventana para el Editor de Tácticas (sin cambios) ---
class FormationEditorWindow(tk.Toplevel):
    def __init__(self, parent, db, refresh_callback):
        super().__init__(parent)
        self.db = db
        self.refresh_callback = refresh_callback
        self.title("Editor de Tácticas")
        self.geometry("350x400")
        self.transient(parent)
        self.grab_set()
        ttk.Label(self, text="Gestiona tus formaciones tácticas.").pack(pady=10)
        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.formations_listbox = tk.Listbox(list_frame)
        self.formations_listbox.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.formations_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.formations_listbox.config(yscrollcommand=scrollbar.set)
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=10)
        ttk.Button(btn_frame, text="Nueva", command=self.add_formation).pack(side="left", expand=True)
        ttk.Button(btn_frame, text="Editar", command=self.edit_formation).pack(side="left", expand=True)
        ttk.Button(btn_frame, text="Eliminar", command=self.delete_formation).pack(side="left", expand=True)
        self.load_formations()

    def load_formations(self):
        self.formations_listbox.delete(0, tk.END)
        self.formations = self.db.get_all_formations()
        for f_id, name, data in self.formations:
            self.formations_listbox.insert(tk.END, name)

    def add_formation(self):
        FormationDetailWindow(self, self.db, None, self.on_editor_closed)

    def edit_formation(self):
        selected_index = self.formations_listbox.curselection()
        if not selected_index:
            messagebox.showwarning("Sin selección", "Por favor, selecciona una formación para editar.", parent=self)
            return
        formation_data = self.formations[selected_index[0]]
        FormationDetailWindow(self, self.db, formation_data, self.on_editor_closed)

    def delete_formation(self):
        selected_index = self.formations_listbox.curselection()
        if not selected_index:
            messagebox.showwarning("Sin selección", "Por favor, selecciona una formación para eliminar.", parent=self)
            return
        formation_id = self.formations[selected_index[0]][0]
        formation_name = self.formations[selected_index[0]][1]
        if messagebox.askyesno("Confirmar", f"¿Seguro que quieres eliminar la formación '{formation_name}'?", parent=self):
            self.db.delete_formation(formation_id)
            self.load_formations()
            self.refresh_callback()

    def on_editor_closed(self):
        self.load_formations()
        self.refresh_callback()

class FormationDetailWindow(tk.Toplevel):
    def __init__(self, parent, db, formation_data=None, close_callback=None):
        super().__init__(parent)
        self.db = db; self.formation_data = formation_data; self.close_callback = close_callback; self.positions = []
        self.title("Detalle de Formación"); self.geometry("400x600"); self.transient(parent); self.grab_set()
        top_frame = ttk.Frame(self); top_frame.pack(fill="x", padx=10, pady=10)
        ttk.Label(top_frame, text="Nombre:").pack(side="left")
        self.name_entry = ttk.Entry(top_frame); self.name_entry.pack(side="left", fill="x", expand=True, padx=5)
        canvas_frame = ttk.Frame(self, relief="sunken", borderwidth=1); canvas_frame.pack(fill="both", expand=True, padx=10)
        self.canvas = tk.Canvas(canvas_frame, bg="#2ECC71"); self.canvas.pack(fill="both", expand=True)
        bottom_frame = ttk.Frame(self); bottom_frame.pack(fill="x", padx=10, pady=10)
        self.pos_label = ttk.Label(bottom_frame, text="Posiciones: 0/11"); self.pos_label.pack(side="left")
        ttk.Button(bottom_frame, text="Guardar", command=self.save).pack(side="right")
        ttk.Button(bottom_frame, text="Limpiar", command=self.clear_canvas).pack(side="right", padx=5)
        self.canvas.bind("<Configure>", lambda e: self.draw_vertical_field()); self.canvas.bind("<Button-1>", self.on_canvas_click)
        if self.formation_data:
            self.name_entry.insert(0, self.formation_data[1])
            if self.formation_data[2]: self.positions = json.loads(self.formation_data[2])
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def draw_vertical_field(self):
        self.canvas.delete("all"); w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        self.canvas.create_rectangle(w*0.05, h*0.05, w*0.95, h*0.95, outline="white", width=1)
        self.canvas.create_line(w*0.05, h/2, w*0.95, h/2, fill="white", width=1)
        self.canvas.create_oval(w/2-w*0.15, h/2-h*0.1, w/2+w*0.15, h/2+h*0.1, outline="white", width=1)
        self.canvas.create_rectangle(w/2-w*0.3, h*0.05, w/2+w*0.3, h*0.05+h*0.15, outline="white", width=1)
        self.canvas.create_rectangle(w/2-w*0.3, h*0.95-h*0.15, w/2+w*0.3, h*0.95, outline="white", width=1)
        self.redraw_positions()
    
    def on_canvas_click(self, event):
        norm_x = event.x / self.canvas.winfo_width(); norm_y = event.y / self.canvas.winfo_height()
        for pos in self.positions:
            px, py = pos[0] * self.canvas.winfo_width(), pos[1] * self.canvas.winfo_height()
            if (event.x - px)**2 + (event.y - py)**2 < 10**2:
                self.positions.remove(pos); self.redraw_positions(); return
        if len(self.positions) < 11:
            self.positions.append((norm_x, norm_y)); self.redraw_positions()

    def redraw_positions(self):
        self.canvas.delete("pos"); w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        for x, y in self.positions:
            self.canvas.create_oval(x*w-8, y*h-8, x*w+8, y*h+8, fill="yellow", outline="black", tags="pos")
        self.pos_label.config(text=f"Posiciones: {len(self.positions)}/11")

    def clear_canvas(self):
        self.positions = []; self.redraw_positions()

    def save(self):
        name = self.name_entry.get().strip()
        if not name: messagebox.showwarning("Falta nombre", "La formación debe tener un nombre.", parent=self); return
        positions_json = json.dumps(self.positions)
        if self.formation_data: self.db.update_formation(self.formation_data[0], name, positions_json)
        else: self.db.insert_formation(name, positions_json)
        self.on_close()

    def on_close(self):
        if self.close_callback: self.close_callback()
        self.destroy()

# --- Pestaña Principal de Convocatorias ---
class CallupsTab:
    def __init__(self, notebook, db):
        self.db = db
        self.frame = ttk.Frame(notebook)
        self.current_callup_id = None
        self.player_tokens = {}
        self.formation_guides = []
        self.images = {}
        self.pickup_data = None # Almacena datos del jugador "cogido"
        self.load_images()
        self.setup_ui()
        self.load_callups_dropdown()

    def load_images(self):
        try:
            path = resource_path("data/pitch_vertical.png") 
            self.images['pitch'] = Image.open(path)
        except Exception:
            self.images['pitch'] = None

    def setup_ui(self):
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        main_frame.grid_columnconfigure(0, weight=2, minsize=280)
        main_frame.grid_columnconfigure(1, weight=4, minsize=450)
        main_frame.grid_columnconfigure(2, weight=2, minsize=280)
        main_frame.grid_rowconfigure(0, weight=1)

        # --- Columna 1: Izquierda (Info de Convocatoria) ---
        left_pane = ttk.Frame(main_frame)
        left_pane.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        callups_list_frame = ttk.LabelFrame(left_pane, text="Convocatorias")
        callups_list_frame.pack(fill="both", expand=True, pady=(0, 10))
        cols = ("id", "date", "rival")
        self.callups_tree = ttk.Treeview(callups_list_frame, columns=cols, show="headings")
        self.callups_tree.heading("date", text="Fecha"); self.callups_tree.column("date", width=90)
        self.callups_tree.heading("rival", text="Rival"); self.callups_tree.column("rival", width=120)
        self.callups_tree.column("id", width=0, stretch=tk.NO)
        self.callups_tree.pack(fill="both", expand=True)
        self.callups_tree.bind("<<TreeviewSelect>>", self.on_callup_select)

        details_frame = ttk.LabelFrame(left_pane, text="Detalles del Partido")
        details_frame.pack(fill="x")
        details_frame.grid_columnconfigure(1, weight=1)
        ttk.Label(details_frame, text="Fecha:").grid(row=0, column=0, sticky="w", padx=5, pady=3)
        self.date_entry = ttk.Entry(details_frame); self.date_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=3)
        ttk.Label(details_frame, text="Rival:").grid(row=1, column=0, sticky="w", padx=5, pady=3)
        self.rival_entry = ttk.Entry(details_frame); self.rival_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=3)
        ttk.Label(details_frame, text="Lugar:").grid(row=2, column=0, sticky="w", padx=5, pady=3)
        self.venue_entry = ttk.Entry(details_frame); self.venue_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=3)
        ttk.Label(details_frame, text="Ciudad:").grid(row=3, column=0, sticky="w", padx=5, pady=3)
        self.city_entry = ttk.Entry(details_frame); self.city_entry.grid(row=3, column=1, sticky="ew", padx=5, pady=3)
        self.is_home_var = tk.BooleanVar()
        ttk.Checkbutton(details_frame, text="Juega en Casa", variable=self.is_home_var).grid(row=4, column=0, columnspan=2, sticky="w", padx=5, pady=3)
        btn_container = ttk.Frame(details_frame)
        btn_container.grid(row=5, column=0, columnspan=2, pady=10, sticky="ew")
        ttk.Button(btn_container, text="Guardar", command=self.save_callup).pack(side="left", fill="x", expand=True, padx=2)
        ttk.Button(btn_container, text="Nueva", command=self.prepare_new_callup).pack(side="left", fill="x", expand=True, padx=2)
        ttk.Button(btn_container, text="Eliminar", command=self.delete_callup).pack(side="left", fill="x", expand=True, padx=2)
        
        # --- Columna 2: Centro (Campo de Fútbol) ---
        center_pane = ttk.Frame(main_frame)
        center_pane.grid(row=0, column=1, sticky="nsew", padx=(0, 10))
        formation_container = ttk.Frame(center_pane)
        formation_container.pack(fill="x", pady=(0, 5))
        ttk.Label(formation_container, text="Formación Táctica:").pack(side="left")
        self.formation_var = tk.StringVar()
        self.formation_dropdown = ttk.Combobox(formation_container, textvariable=self.formation_var, state="readonly", width=12)
        self.formation_dropdown.pack(side="left", padx=5)
        self.formation_dropdown.bind("<<ComboboxSelected>>", self.on_formation_select)
        ttk.Button(formation_container, text="Gestionar...", command=self.open_formation_editor).pack(side="left")
        self.canvas = tk.Canvas(center_pane, bg="#2ECC71", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, pady=5)
        self.canvas.bind("<Configure>", self.draw_field_background)
        self.canvas.bind("<Button-1>", self.on_click_handler)

        # --- Columna 3: Derecha (Listas de Personal) ---
        right_pane = ttk.Frame(main_frame)
        right_pane.grid(row=0, column=2, sticky="nsew")
        right_paned_window = ttk.PanedWindow(right_pane, orient=tk.VERTICAL)
        right_paned_window.pack(fill="both", expand=True)
        available_frame = ttk.Frame(right_paned_window); status_frame = ttk.Frame(right_paned_window)
        right_paned_window.add(available_frame, weight=1); right_paned_window.add(status_frame, weight=1)
        available_notebook = ttk.Notebook(available_frame)
        available_notebook.pack(fill="both", expand=True)
        players_avail_frame = ttk.Frame(available_notebook); coaches_avail_frame = ttk.Frame(available_notebook)
        available_notebook.add(players_avail_frame, text="Jugadores Disponibles")
        available_notebook.add(coaches_avail_frame, text="C. Técnico Disponible")
        self.players_tree = self.create_list_tree(players_avail_frame)
        self.coaches_tree = self.create_list_tree(coaches_avail_frame)
        status_notebook = ttk.Notebook(status_frame)
        status_notebook.pack(fill="both", expand=True)
        self.status_trees = {}
        for status in ["Suplentes", "Lesionados", "Dudosos", "Sancionados", "Cuerpo Técnico Asignado"]:
            frame = ttk.Frame(status_notebook)
            status_notebook.add(frame, text=status)
            tree = self.create_list_tree(frame)
            self.status_trees[status] = tree
        
        self.load_available_personnel()
        self.load_formations_dropdown()

    def create_list_tree(self, parent):
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill="both", expand=True)
        tree = ttk.Treeview(tree_frame, columns=("id", "name", "info"), show="headings", height=5)
        tree.heading("name", text="Nombre"); tree.column("name", width=120)
        tree.heading("info", text="Nº/Rol"); tree.column("info", width=60)
        tree.column("id", width=0, stretch=tk.NO)
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        tree.bind("<Button-1>", self.on_click_handler)
        return tree

    # --- LÓGICA DE PULSAR-PARA-MOVER (NUEVA Y ROBUSTA) ---

    def on_click_handler(self, event):
        """Gestiona todos los clics para coger o soltar un jugador."""
        widget = event.widget
        
        if self.pickup_data is None:
            # --- FASE 1: COGER UN JUGADOR ---
            if widget == self.canvas:
                item_tuple = self.canvas.find_closest(event.x, event.y)
                if not item_tuple: return
                item = item_tuple[0]
                if "player_token" not in self.canvas.gettags(item): return
                
                player_id = self.player_tokens[item]['player_id']
                player_data = self.db.get_player_by_id(player_id)
                if not player_data: return

                self.pickup_data = {
                    'source': 'canvas', 'canvas_id': item,
                    'values': (player_data[0], player_data[1], player_data[3] or '')
                }
            else: # Es un Treeview
                tree = widget
                item_iid = tree.identify_row(event.y)
                if not item_iid: return
                self.pickup_data = {
                    'source': 'tree', 'source_tree': tree, 'item_iid': item_iid,
                    'values': tree.item(item_iid)['values']
                }
            self.frame.config(cursor="hand2") # Feedback visual
        else:
            # --- FASE 2: SOLTAR UN JUGADOR ---
            values_to_drop = self.pickup_data['values']
            
            # Determinar si el destino es válido
            is_coach = self.pickup_data['values'][0] in [c[0] for c in self.db.get_all_coaches()]
            
            if widget == self.canvas and not is_coach:
                self.place_player_token(values_to_drop[0], event.x, event.y)
                self._remove_from_source()
            else:
                parent = widget
                while parent:
                    if isinstance(parent, ttk.Treeview):
                        is_coach_drop = parent in [self.coaches_tree, self.status_trees["Cuerpo Técnico Asignado"]]
                        if (is_coach and is_coach_drop) or (not is_coach and not is_coach_drop):
                            if not any(parent.item(i, 'values')[0] == values_to_drop[0] for i in parent.get_children()):
                                parent.insert("", "end", values=values_to_drop)
                                self._remove_from_source()
                        break
                    parent = parent.master
            
            # Limpiar estado
            self.pickup_data = None
            self.frame.config(cursor="")

    def _remove_from_source(self):
        """Función auxiliar para eliminar el jugador de su origen."""
        if self.pickup_data['source'] == 'canvas':
            canvas_id = self.pickup_data['canvas_id']
            self.canvas.delete(canvas_id)
            if canvas_id in self.player_tokens:
                del self.player_tokens[canvas_id]
        elif self.pickup_data['source'] == 'tree':
            self.pickup_data['source_tree'].delete(self.pickup_data['item_iid'])

    # --- Resto de funciones (sin cambios) ---
    
    def on_callup_select(self, event=None):
        self.pickup_data = None; self.frame.config(cursor="")
        selected_item = self.callups_tree.selection()
        if not selected_item: return
        self.current_callup_id = self.callups_tree.item(selected_item)['values'][0]
        details = self.db.get_match_callup_details(self.current_callup_id)
        self.clear_form_and_field()
        if not details: return
        self.date_entry.insert(0, details[1] or ""); self.rival_entry.insert(0, details[2] or "")
        self.venue_entry.insert(0, details[3] or ""); self.is_home_var.set(bool(details[4]))
        self.city_entry.insert(0, details[5] or "")
        for status_name, tree in self.status_trees.items():
            db_status = status_name.lower().replace(' ', '_').replace('asignado','')
            if "cuerpo_técnico" in db_status:
                 coaches = self.db.get_coaches_for_callup(self.current_callup_id)
                 for cid, name, role in coaches: tree.insert("", "end", values=(cid, name, role))
            else:
                players = self.db.get_players_for_callup(self.current_callup_id, db_status)
                for pid, name, pos, num, x, y in players:
                    if db_status == 'convocado' and x is not None and y is not None:
                        self.place_player_token(pid, x, y)
                    else:
                        tree.insert("", "end", values=(pid, name, num or ''))
        self.load_available_personnel()

    def prepare_new_callup(self):
        self.pickup_data = None; self.frame.config(cursor="")
        self.current_callup_id = None; self.clear_form_and_field()
        if self.callups_tree.selection(): self.callups_tree.selection_remove(self.callups_tree.selection())
        self.load_available_personnel()
    
    def save_callup(self):
        details = {'id': self.current_callup_id, 'match_date': self.date_entry.get(), 'rival': self.rival_entry.get(), 'venue': self.venue_entry.get(), 'is_home': self.is_home_var.get(), 'city': self.city_entry.get()}
        if not details['match_date'] or not details['rival']: messagebox.showwarning("Faltan datos", "Fecha y Rival son obligatorios."); return
        player_lists = {}
        convocados = []
        for canvas_id, data in self.player_tokens.items():
            x, y = self.canvas.coords(canvas_id)
            convocados.append((data['player_id'], int(x), int(y)))
        player_lists['convocado'] = convocados
        for status_name, tree in self.status_trees.items():
            if "cuerpo_técnico" in status_name.lower(): continue
            db_status = status_name.lower().replace(' ', '_')
            player_ids = [tree.item(item, "values")[0] for item in tree.get_children()]
            player_lists[db_status] = player_ids
        coach_tree = self.status_trees["Cuerpo Técnico Asignado"]
        coach_ids = [coach_tree.item(item, "values")[0] for item in coach_tree.get_children()]
        try:
            new_id = self.db.save_match_callup(details, player_lists, coach_ids)
            if not self.current_callup_id: self.current_callup_id = new_id
            messagebox.showinfo("Éxito", "Convocatoria guardada.")
            self.load_callups_dropdown()
        except Exception as e: messagebox.showerror("Error", f"No se pudo guardar la convocatoria.\n{e}")

    def delete_callup(self):
        if not self.current_callup_id: messagebox.showwarning("Sin selección", "Selecciona una convocatoria para eliminar."); return
        if messagebox.askyesno("Confirmar", "¿Seguro que quieres eliminar esta convocatoria?"):
            self.db.delete_match_callup(self.current_callup_id); self.prepare_new_callup(); self.load_callups_dropdown()

    def open_formation_editor(self):
        FormationEditorWindow(self.frame, self.db, self.load_formations_dropdown)

    def load_formations_dropdown(self):
        self.formations = self.db.get_all_formations()
        formation_names = [f[1] for f in self.formations]
        self.formation_dropdown['values'] = ["Limpiar"] + formation_names

    def on_formation_select(self, event=None):
        for guide in self.formation_guides: self.canvas.delete(guide)
        self.formation_guides.clear()
        selected_name = self.formation_var.get()
        if not selected_name or selected_name == "Limpiar": return
        formation = next((f for f in self.formations if f[1] == selected_name), None)
        if formation and formation[2]:
            positions = json.loads(formation[2])
            w, h = self.canvas.winfo_width() or 450, self.canvas.winfo_height() or 650
            for x_norm, y_norm in positions:
                x, y = x_norm * w, y_norm * h
                guide_id = self.canvas.create_oval(x-15, y-15, x+15, y+15, outline="yellow", dash=(4, 2), width=2)
                self.formation_guides.append(guide_id)

    def clear_form_and_field(self):
        self.date_entry.delete(0, tk.END); self.rival_entry.delete(0, tk.END); self.venue_entry.delete(0, tk.END)
        self.city_entry.delete(0, tk.END); self.is_home_var.set(False); self.formation_dropdown.set('')
        for token_id in list(self.player_tokens.keys()): self.canvas.delete(token_id)
        self.player_tokens.clear()
        for guide_id in self.formation_guides: self.canvas.delete(guide_id)
        self.formation_guides.clear()
        for tree in self.status_trees.values():
            for item in tree.get_children(): tree.delete(item)
        self.load_available_personnel()

    def load_callups_dropdown(self):
        for item in self.callups_tree.get_children(): self.callups_tree.delete(item)
        callups = self.db.get_all_match_callups()
        for c_id, date, rival in callups: self.callups_tree.insert("", "end", values=(c_id, date, rival))

    def load_available_personnel(self):
        all_db_players = self.db.get_all_players()
        all_db_coaches = self.db.get_all_coaches()
        used_player_ids = set(data['player_id'] for data in self.player_tokens.values())
        for tree in self.status_trees.values():
            if "cuerpo" not in tree.winfo_parent().lower():
                for item in tree.get_children():
                    try: used_player_ids.add(int(tree.item(item, "values")[0]))
                    except (ValueError, IndexError): pass
        self.players_tree.delete(*self.players_tree.get_children())
        for p in all_db_players:
            if p[0] not in used_player_ids: self.players_tree.insert("", "end", values=(p[0], p[1], p[3] or ''))
        used_coach_ids = set()
        coach_tree = self.status_trees["Cuerpo Técnico Asignado"]
        for item in coach_tree.get_children():
            try: used_coach_ids.add(int(coach_tree.item(item, 'values')[0]))
            except (ValueError, IndexError): pass
        self.coaches_tree.delete(*self.coaches_tree.get_children())
        for c in all_db_coaches:
            if c[0] not in used_coach_ids: self.coaches_tree.insert("", "end", values=(c[0], c[1], c[2]))

    def place_player_token(self, player_id, x, y):
        photo_image = self._create_player_pil(player_id)
        if photo_image:
            canvas_id = self.canvas.create_image(x, y, image=photo_image, tags=("player_token",))
            self.player_tokens[canvas_id] = {'player_id': player_id, 'photo_image': photo_image}
        
    def _create_player_pil(self, player_id):
        player_data = self.db.get_player_by_id(player_id);
        if not player_data: return None
        size = (50, 50); img = Image.new('RGBA', size, (0,0,0,0)); draw = ImageDraw.Draw(img)
        draw.ellipse((0, 0, size[0]-1, size[1]-1), fill="#2e2e2e", outline="white", width=2)
        photo_path = player_data[9]
        if photo_path and os.path.exists(resource_path(photo_path)):
            try:
                player_photo = Image.open(resource_path(photo_path)).convert("RGBA")
                mask = Image.new('L', size, 0); mask_draw = ImageDraw.Draw(mask); mask_draw.ellipse((4, 4, size[0]-5, size[1]-5), fill=255)
                player_photo = player_photo.resize(size, Image.LANCZOS); img.paste(player_photo, (0,0), mask)
            except Exception: pass
        number = str(player_data[3] or '?')
        try: font = ImageFont.truetype("arialbd.ttf", 14)
        except IOError: font = ImageFont.load_default()
        text_bbox = draw.textbbox((0,0), number, font=font); text_w, text_h = text_bbox[2]-text_bbox[0], text_bbox[3]-text_bbox[1]
        draw.text(((size[0]-text_w)/2+1, (size[1]-text_h)/2+1), number, font=font, fill="black")
        draw.text(((size[0]-text_w)/2, (size[1]-text_h)/2), number, font=font, fill="white")
        return ImageTk.PhotoImage(img)

    def draw_field_background(self, event=None):
        self.canvas.delete("field_bg", "field_lines"); canvas_width = self.canvas.winfo_width(); canvas_height = self.canvas.winfo_height()
        if self.images.get('pitch') and canvas_width > 1 and canvas_height > 1:
            try:
                resized_img = self.images['pitch'].resize((canvas_width, canvas_height), Image.LANCZOS)
                self.images['pitch_resized'] = ImageTk.PhotoImage(resized_img); self.canvas.create_image(0, 0, image=self.images['pitch_resized'], anchor="nw", tags="field_bg")
            except Exception as e:
                print(f"Error al redimensionar la imagen del campo: {e}"); self.images['pitch'] = None
        if not self.images.get('pitch'):
            w, h = canvas_width, canvas_height
            if w < 1 or h < 1: return
            self.canvas.create_rectangle(w*0.05, h*0.05, w*0.95, h*0.95, outline="white", width=2, tags="field_lines")
            self.canvas.create_line(w*0.05, h/2, w*0.95, h/2, fill="white", width=2, tags="field_lines")
            self.canvas.create_oval(w/2-w*0.2, h/2-h*0.1, w/2+w*0.2, h/2+h*0.1, outline="white", width=2, tags="field_lines")
            self.canvas.create_rectangle(w/2-w*0.35, h*0.05, w/2+w*0.35, h*0.05+h*0.15, outline="white", width=2, tags="field_lines")
            self.canvas.create_rectangle(w/2-w*0.35, h*0.95-h*0.15, w/2+w*0.35, h*0.95, outline="white", width=2, tags="field_lines")