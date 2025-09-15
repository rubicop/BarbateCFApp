import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, colorchooser, filedialog
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

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
    def show_tooltip(self, event):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip_window, text=self.text, background="#ffffe0", relief="solid", borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)
    def hide_tooltip(self, event):
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None

class LayoutManagerWindow(tk.Toplevel):
    def __init__(self, parent, db, load_callback):
        super().__init__(parent)
        self.db = db; self.load_callback = load_callback
        self.title("Gestor de Diseños"); self.geometry("400x350"); self.transient(parent); self.grab_set()
        list_frame = ttk.LabelFrame(self, text="Diseños Guardados"); list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.layout_list = tk.Listbox(list_frame); self.layout_list.pack(fill="both", expand=True)
        btn_frame = ttk.Frame(self); btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(btn_frame, text="Cargar", command=self.load_selected).pack(side="left", expand=True)
        ttk.Button(btn_frame, text="Renombrar", command=self.rename_selected).pack(side="left", expand=True)
        ttk.Button(btn_frame, text="Eliminar", command=self.delete_selected).pack(side="left", expand=True)
        self.populate_list()
    def populate_list(self):
        self.layout_list.delete(0, tk.END); self.layouts = self.db.get_all_layouts()
        for lid, name in self.layouts: self.layout_list.insert(tk.END, name)
    def get_selected_id_and_name(self):
        if not self.layout_list.curselection():
            messagebox.showwarning("Sin Selección", "Por favor, selecciona un diseño.", parent=self)
            return None, None
        selected_index = self.layout_list.curselection()[0]
        layout_id, layout_name = self.layouts[selected_index]
        return layout_id, layout_name
    def load_selected(self):
        layout_id, _ = self.get_selected_id_and_name()
        if layout_id:
            json_data = self.db.get_layout_data_by_id(layout_id)
            if json_data: self.load_callback(json.loads(json_data)); self.destroy()
    def rename_selected(self):
        layout_id, old_name = self.get_selected_id_and_name()
        if layout_id:
            new_name = simpledialog.askstring("Renombrar", "Nuevo nombre:", initialvalue=old_name, parent=self)
            if new_name and new_name.strip() and new_name != old_name:
                try: self.db.update_layout_name(layout_id, new_name); self.populate_list()
                except Exception as e: messagebox.showerror("Error", f"No se pudo renombrar. ¿Ya existe un diseño con ese nombre?\n{e}", parent=self)
    def delete_selected(self):
        layout_id, name = self.get_selected_id_and_name()
        if layout_id:
            if messagebox.askyesno("Confirmar", f"¿Seguro que quieres eliminar '{name}'?", parent=self):
                self.db.delete_layout(layout_id); self.populate_list()

class FieldEditorTab:
    def __init__(self, notebook, db):
        self.db = db; self.frame = ttk.Frame(notebook); self.elements = []
        self.selected_tool = "move"; self.images = {}; self.toolbar_icons = {}; self.icon_references = {}
        self.dragging = False; self.drag_element_id = None; self.drag_start_x, self.drag_start_y = 0, 0
        self.selected_element_id = None; self.highlight_rect = None
        self.current_color = "yellow"
        self.current_width = tk.IntVar(value=3)
        self.line_style = tk.StringVar(value="solid")
        self.load_toolbar_icons()
        self.load_custom_icons()
        self.setup_ui()

    def load_toolbar_icons(self):
        icon_size = (24, 24)
        icon_files = {"move": "move.png", "player_own": "player_red.png", "player_opponent": "player_yellow.png", "cono": "cone.png", "porteria": "goal.png", "ball": "ball.png", "arrow": "arrow.png", "text": "text.png", "rotate": "rotate.png", "delete": "delete.png", "clear": "clear.png", "save_layout": "save.png", "load_layout": "load.png", "capture": "camera.png"}
        for name, filename in icon_files.items():
            try:
                path = resource_path(os.path.join("icons", filename))
                img = Image.open(path).resize(icon_size, Image.LANCZOS)
                self.toolbar_icons[name] = ImageTk.PhotoImage(img)
            except Exception as e:
                print(f"No se pudo cargar el icono: {filename} ({e})")

    def load_custom_icons(self):
        icon_paths = {"ball": ("ball.png", (20, 20)), "cono": ("cone.png", (25, 25)), "porteria": ("porteria.png", (60, 25))}
        fallback_drawings = {"ball": lambda d, s: d.ellipse((0,0,s[0]-2,s[1]-2),fill='white',outline='black'), "cono": lambda d, s: d.polygon([(s[0]/2,0),(0,s[1]),(s[0],s[1])],fill='orange'), "porteria": lambda d, s: d.rectangle((0,0,s[0]-1,s[1]-1),outline='white',width=3)}
        for name, (path, size) in icon_paths.items():
            try:
                full_path = resource_path(path)
                if not os.path.exists(full_path): raise FileNotFoundError
                pil_img = Image.open(full_path).convert("RGBA").resize(size, Image.LANCZOS)
            except (FileNotFoundError, IOError):
                pil_img = Image.new('RGBA', size); draw = ImageDraw.Draw(pil_img); fallback_drawings[name](draw, size)
            self.images[f'{name}_pil'] = pil_img
            self.images[name] = ImageTk.PhotoImage(pil_img)

    def _create_player_icon_pil(self, text, team):
        size = (25, 50); combined_size = (size[0] + 25, size[1]); combined_img = Image.new('RGBA', combined_size, (0, 0, 0, 0))
        path = resource_path("player_red_base.png") if team == 'own' else resource_path("player_yellow_base.png")
        try:
            player_img_only = Image.open(path).convert("RGBA").resize(size, Image.LANCZOS)
        except FileNotFoundError:
            color = "#C0392B" if team == 'own' else "#F1C40F"
            player_img_only = Image.new('RGBA', size); draw = ImageDraw.Draw(player_img_only)
            draw.ellipse((2, 12, size[0]-2, size[1]-2), fill=color, outline="black"); draw.ellipse((5, 0, size[0]-5, 15), fill="gray", outline="black")
        combined_img.paste(player_img_only, (0, (combined_size[1] - size[1]) // 2), player_img_only)
        draw = ImageDraw.Draw(combined_img)
        try: font = ImageFont.truetype(resource_path("arialbd.ttf"), 14)
        except IOError: font = ImageFont.load_default()
        text_bbox = draw.textbbox((0,0), text, font=font); text_height = text_bbox[3] - text_bbox[1]
        draw.text((size[0] + 3, (combined_size[1] - text_height) / 2), text, font=font, fill="black")
        return combined_img

    def setup_ui(self):
        options_bar = ttk.LabelFrame(self.frame, text="Opciones de Dibujo"); options_bar.pack(fill="x", padx=10, pady=5)
        self.color_swatch = tk.Label(options_bar, bg=self.current_color, width=2, relief="sunken"); self.color_swatch.pack(side="left", padx=5)
        ttk.Button(options_bar, text="Color", command=self.choose_color).pack(side="left", padx=5)
        ttk.Label(options_bar, text="Grosor:").pack(side="left", padx=5)
        ttk.Scale(options_bar, from_=1, to=10, variable=self.current_width, orient="horizontal").pack(side="left", padx=5)
        ttk.Label(options_bar, text="Estilo Flecha:").pack(side="left", padx=(15, 5))
        ttk.Radiobutton(options_bar, text="Continua", variable=self.line_style, value="solid").pack(side="left")
        ttk.Radiobutton(options_bar, text="Discontinua", variable=self.line_style, value="dashed").pack(side="left")
        tools = ttk.LabelFrame(self.frame, text="Herramientas"); tools.pack(fill="x", padx=10, pady=5)
        buttons = {"Mover": "move", "Jugador (Local)": "player_own", "Jugador (Peto)": "player_opponent", "Cono": "cono", "Portería": "porteria", "Balón": "ball", "Flecha": "arrow", "Texto": "text", "Rotar": "rotate", "Eliminar": "delete", "Limpiar": "clear", "Guardar Diseño": "save_layout", "Cargar Diseño": "load_layout", "Capturar Imagen": "capture"}
        row, col, max_cols = 0, 0, 8
        for text, tool in buttons.items():
            cmd = (lambda t=tool: self.select_tool(t))
            if tool == "clear": cmd = self.clear_canvas
            elif tool == "save_layout": cmd = self.save_layout
            elif tool == "load_layout": cmd = self.open_layout_manager
            elif tool == "capture": cmd = self.capture_and_save_image
            icon = self.toolbar_icons.get(tool)
            btn = ttk.Button(tools, image=icon, command=cmd); btn.grid(row=row, column=col, padx=3, pady=3); ToolTip(btn, text)
            col += 1
            if col >= max_cols: col = 0; row += 1
        canvas_frame = ttk.Frame(self.frame); canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.canvas = tk.Canvas(canvas_frame, bg="#2ECC71"); self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self.draw_field)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)

    def get_field_geometry(self, area_w, area_h):
        if area_w < 1 or area_h < 1: return 0, 0, 0, 0
        FIELD_ASPECT_RATIO = 105 / 68.0
        if area_w / area_h > FIELD_ASPECT_RATIO:
            field_h = area_h * 0.95; field_w = field_h * FIELD_ASPECT_RATIO
        else:
            field_w = area_w * 0.95; field_h = field_w / FIELD_ASPECT_RATIO
        offset_x = (area_w - field_w) / 2; offset_y = (area_h - field_h) / 2
        return offset_x, offset_y, field_w, field_h

    def choose_color(self):
        color_code = colorchooser.askcolor(title="Elige un color", initialcolor=self.current_color)
        if color_code and color_code[1]: self.current_color = color_code[1]; self.color_swatch.config(bg=self.current_color)

    def on_canvas_release(self, event):
        if self.dragging: self.dragging = False; self.drag_element_id = None
        elif self.selected_tool == "arrow":
            offset_x, offset_y, field_w, field_h = self.get_field_geometry(self.canvas.winfo_width(), self.canvas.winfo_height())
            if field_w == 0 or field_h == 0: return
            coords = (self.drag_start_x, self.drag_start_y, event.x, event.y)
            rel_coords = ((coords[0]-offset_x)/field_w, (coords[1]-offset_y)/field_h, (coords[2]-offset_x)/field_w, (coords[3]-offset_y)/field_h)
            options = {"arrow": tk.LAST, "fill": self.current_color, "width": self.current_width.get()}
            if self.line_style.get() == "dashed": options["dash"] = (5, 3)
            arrow_id = self.canvas.create_line(coords, **options)
            self.elements.append({"id": arrow_id, "data": {"type": "arrow", "rel_coords": rel_coords, "options": options}})

    def select_tool(self, tool): self.selected_tool = tool; self._clear_selection()
    
    def draw_field(self, event=None):
        self.canvas.delete("field")
        canvas_w = self.canvas.winfo_width(); canvas_h = self.canvas.winfo_height()
        offset_x, offset_y, field_w, field_h = self.get_field_geometry(canvas_w, canvas_h)
        if field_w == 0: return
        x1, y1, x2, y2 = offset_x, offset_y, offset_x + field_w, offset_y + field_h
        self.canvas.create_rectangle(x1, y1, x2, y2, outline="white", width=2, tags="field")
        self.canvas.create_line(x1 + field_w/2, y1, x1 + field_w/2, y2, fill="white", width=2, tags="field")
        radius = field_w * 0.1
        self.canvas.create_oval(x1 + field_w/2 - radius, y1 + field_h/2 - radius, x1 + field_w/2 + radius, y1 + field_h/2 + radius, outline="white", width=2, tags="field")
        area_w = field_w * 0.17; area_h = field_h * 0.5
        self.canvas.create_rectangle(x1, y1 + field_h/2 - area_h/2, x1 + area_w, y1 + field_h/2 + area_h/2, outline="white", width=2, tags="field")
        self.canvas.create_rectangle(x2 - area_w, y1 + field_h/2 - area_h/2, x2, y1 + field_h/2 + area_h/2, outline="white", width=2, tags="field")

    def find_element_by_id(self, canvas_id): return next((el for el in self.elements if el['id'] == canvas_id), None)
    def _select_element(self, canvas_id): self._clear_selection(); self.selected_element_id = canvas_id; bbox = self.canvas.bbox(canvas_id); self.highlight_rect = self.canvas.create_rectangle(bbox, outline="red", width=2) if bbox else None
    def _clear_selection(self):
        if self.highlight_rect: self.canvas.delete(self.highlight_rect)
        self.selected_element_id = None; self.highlight_rect = None
    
    def on_canvas_click(self, event):
        x, y = event.x, event.y
        overlapping = self.canvas.find_overlapping(x-1, y-1, x+1, y+1)
        target_id = overlapping[-1] if overlapping else None
        element = self.find_element_by_id(target_id) if target_id else None
        if self.selected_tool == "delete" and element: self.delete_element_by_id(target_id)
        elif self.selected_tool == "move" and element: self._select_element(target_id); self.dragging, self.drag_element_id = True, target_id; self.drag_start_x, self.drag_start_y = x, y
        elif self.selected_tool == "rotate" and element and element.get('image_pil'): self.rotate_element(element)
        elif self.selected_tool in ("player_own", "player_opponent"): self.select_player_dialog(x, y, "own" if self.selected_tool == "player_own" else "opponent")
        elif self.selected_tool in ("cono", "porteria", "ball"): self.add_element(x, y, self.selected_tool, image_pil=self.images[f'{self.selected_tool}_pil'])
        elif self.selected_tool == "arrow": self.drag_start_x, self.drag_start_y = x, y
        elif self.selected_tool == "text": text = simpledialog.askstring("Texto", "Introduce el texto:"); self.add_element(x, y, "text", text=text, options={"fill": self.current_color}) if text else None
        elif not element: self._clear_selection()
    
    def rotate_element(self, element):
        new_rotation = (element['data'].get('rotation', 0) + 90) % 360
        original_pil = element['image_pil']; rotated_pil = original_pil.rotate(-new_rotation, expand=True, resample=Image.Resampling.BICUBIC)
        new_icon_tk = ImageTk.PhotoImage(rotated_pil)
        self.canvas.itemconfig(element['id'], image=new_icon_tk)
        element['data']['rotation'] = new_rotation; self.icon_references[element['id']] = new_icon_tk
    
    def select_player_dialog(self, x, y, team):
        players = self.db.get_all_players()
        if not players: messagebox.showwarning("No hay jugadores", "No hay jugadores en la BD."); return
        win=tk.Toplevel(self.frame); win.title("Seleccionar Jugador"); win.geometry("300x400"); win.grab_set()
        lb = tk.Listbox(win); lb.pack(fill="both", expand=True, padx=10, pady=10)
        for p in players: lb.insert(tk.END, f"{p[3] or '?'} - {p[1]}")
        def on_select():
            if lb.curselection(): self.add_player(x, y, players[lb.curselection()[0]], team); win.destroy()
        ttk.Button(win, text="Seleccionar", command=on_select).pack(pady=10)
    
    def add_player(self, x, y, player_data, team, rotation=0):
        pid, name, pos, num, *_ = player_data; pil_img = self._create_player_icon_pil(str(num or "?"), team)
        self.add_element(x, y, "player", image_pil=pil_img, player_id=pid, team=team, rotation=rotation)
        
    def add_element(self, x, y, el_type, **kwargs):
        offset_x, offset_y, field_w, field_h = self.get_field_geometry(self.canvas.winfo_width(), self.canvas.winfo_height())
        if field_w == 0 or field_h == 0: return
        
        kwargs['rel_x'] = (x - offset_x) / field_w
        kwargs['rel_y'] = (y - offset_y) / field_h
        
        # --- CORRECCIÓN: Separamos el objeto de imagen de los datos a guardar ---
        pil_img = kwargs.pop('image_pil', None)
        data_to_save = {"type": el_type, **kwargs}
        
        runtime_pil_img = pil_img
        rotation = kwargs.get('rotation', 0)
        text = kwargs.get('text')
        options = kwargs.get('options', {})

        if runtime_pil_img and rotation != 0: 
            runtime_pil_img = runtime_pil_img.rotate(-rotation, expand=True, resample=Image.Resampling.BICUBIC)
        
        photo_img = ImageTk.PhotoImage(runtime_pil_img) if runtime_pil_img else None
        
        element_id = None
        if photo_img:
            element_id = self.canvas.create_image(x, y, image=photo_img)
            self.icon_references[element_id] = photo_img
        elif text:
            element_id = self.canvas.create_text(x, y, text=text, font=("Arial", 12, "bold"), **options)
        
        if element_id:
            self.elements.append({"id": element_id, "data": data_to_save, "image_pil": pil_img})
    
    def on_canvas_drag(self, event):
        if self.dragging and self.drag_element_id:
            dx, dy = event.x - self.drag_start_x, event.y - self.drag_start_y
            self.canvas.move(self.drag_element_id, dx, dy); self.drag_start_x, self.drag_start_y = event.x, event.y
            if self.highlight_rect: self.canvas.move(self.highlight_rect, dx, dy)
            element = self.find_element_by_id(self.drag_element_id)
            if element:
                offset_x, offset_y, field_w, field_h = self.get_field_geometry(self.canvas.winfo_width(), self.canvas.winfo_height())
                if field_w > 0 and field_h > 0:
                    coords = self.canvas.coords(self.drag_element_id)
                    element['data']['rel_x'] = (coords[0] - offset_x) / field_w
                    element['data']['rel_y'] = (coords[1] - offset_y) / field_h
    
    def delete_element_by_id(self, element_id):
        if self.selected_element_id == element_id: self._clear_selection()
        self.canvas.delete(element_id)
        if element_id in self.icon_references: del self.icon_references[element_id]
        self.elements = [el for el in self.elements if el["id"] != element_id]
    
    def clear_canvas(self):
        for el in self.elements: self.canvas.delete(el["id"])
        self.elements.clear(); self.icon_references.clear(); self._clear_selection()
    
    def save_layout(self):
        if not self.elements: messagebox.showwarning("Campo Vacío", "No hay nada para guardar."); return
        name = simpledialog.askstring("Guardar Diseño", "Nombre para este diseño:", parent=self.frame)
        if not name or not name.strip(): return
        
        layout_to_save = [el['data'] for el in self.elements]
        try:
            self.db.save_layout(name, json.dumps(layout_to_save))
            messagebox.showinfo("Éxito", f"Diseño '{name}' guardado.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")
    
    def open_layout_manager(self): LayoutManagerWindow(self.frame, self.db, self.recreate_canvas_from_data)
    
    def recreate_canvas_from_data(self, layout_data):
        self.clear_canvas()
        offset_x, offset_y, field_w, field_h = self.get_field_geometry(self.canvas.winfo_width(), self.canvas.winfo_height())
        if field_w <= 1 or field_h <= 1:
            self.frame.after(100, self.recreate_canvas_from_data, layout_data)
            return

        for data in layout_data:
            el_type, rotation, options = data.get('type'), data.get('rotation', 0), data.get('options', {})
            
            if 'rel_x' in data and 'rel_y' in data:
                x = (data['rel_x'] * field_w) + offset_x
                y = (data['rel_y'] * field_h) + offset_y
            elif 'x' in data and 'y' in data:
                x, y = data['x'], data['y']
            else:
                continue

            if el_type == 'player':
                if p_data := self.db.get_player_by_id(data.get('player_id')): self.add_player(x, y, p_data, data.get('team'), rotation)
            elif el_type in ('cono', 'porteria', 'ball'): self.add_element(x, y, el_type, image_pil=self.images[f'{el_type}_pil'], rotation=rotation)
            elif el_type == 'text': self.add_element(x, y, 'text', text=data.get('text'), options=options)
            elif el_type == 'arrow' and 'rel_coords' in data:
                rc = data['rel_coords']; coords = ((rc[0]*field_w)+offset_x, (rc[1]*field_h)+offset_y, (rc[2]*field_w)+offset_x, (rc[3]*field_h)+offset_y)
                arrow_id = self.canvas.create_line(coords, **options); self.elements.append({"id": arrow_id, "data": data})
    
    def create_image_from_layout_data(self, layout_data):
        w, h = 800, 600; image = Image.new('RGB', (w, h), color='#2ECC71'); draw = ImageDraw.Draw(image)
        offset_x, offset_y, field_w, field_h = self.get_field_geometry(w, h)
        self.draw_field_on_image(draw, w, h)
        for data in layout_data: self.draw_element_on_image_from_data(draw, image, data, (offset_x, offset_y, field_w, field_h))
        return image
    
    def draw_field_on_image(self, draw, width, height):
        offset_x, offset_y, field_w, field_h = self.get_field_geometry(width, height)
        x1, y1, x2, y2 = offset_x, offset_y, offset_x + field_w, offset_y + field_h
        draw.rectangle((x1, y1, x2, y2), outline="white", width=3)
        draw.line((x1 + field_w/2, y1, x1 + field_w/2, y2), fill="white", width=3)
        radius = field_w * 0.1
        draw.ellipse((x1 + field_w/2 - radius, y1 + field_h/2 - radius, x1 + field_w/2 + radius, y1 + field_h/2 + radius), outline="white", width=3)
        area_w = field_w * 0.17; area_h = field_h * 0.5
        draw.rectangle((x1, y1 + field_h/2 - area_h/2, x1 + area_w, y1 + field_h/2 + area_h/2), outline="white", width=3)
        draw.rectangle((x2 - area_w, y1 + field_h/2 - area_h/2, x2, y1 + field_h/2 + area_h/2), outline="white", width=3)

    def draw_element_on_image_from_data(self, draw, image, data, field_geom):
        offset_x, offset_y, field_w, field_h = field_geom
        el_type, rotation, options = data.get('type'), data.get('rotation', 0), data.get('options', {})
        if 'rel_x' in data and 'rel_y' in data:
            x, y = (data['rel_x'] * field_w) + offset_x, (data['rel_y'] * field_h) + offset_y
        elif 'x' in data and 'y' in data:
            x, y = data['x'], data['y']
        else:
            return
        pil_image = None
        if el_type == "player":
            if p_data := self.db.get_player_by_id(data.get('player_id')): pil_image = self._create_player_icon_pil(str(p_data[3] or "?"), data.get('team'))
        elif el_type in ["cono", "ball", "porteria"]: pil_image = self.images[f'{el_type}_pil']
        elif el_type == "text":
            try: font = ImageFont.truetype(resource_path("arialbd.ttf"), 16)
            except IOError: font = ImageFont.load_default()
            draw.text((x, y), data.get('text', ''), fill=options.get("fill", "white"), font=font, anchor="mm"); return
        elif el_type == "arrow" and 'rel_coords' in data:
            rc = data['rel_coords']; coords = ((rc[0]*field_w)+offset_x, (rc[1]*field_h)+offset_y, (rc[2]*field_w)+offset_x, (rc[3]*field_h)+offset_y)
            draw.line(coords, fill=options.get("fill", "yellow"), width=options.get("width", 3)); return
        if pil_image:
            if rotation != 0: pil_image = pil_image.rotate(-rotation, expand=True, resample=Image.Resampling.BICUBIC)
            w, h = pil_image.size; x_paste, y_paste = int(x - w/2), int(y - h/2)
            if pil_image.mode == 'RGBA': image.paste(pil_image, (x_paste, y_paste), pil_image)
            else: image.paste(pil_image, (x_paste, y_paste))

    def capture_and_save_image(self):
        if not self.elements: messagebox.showwarning("Campo Vacío", "No hay elementos para capturar.", parent=self.frame); return
        try: image_to_save = self.create_image_from_layout_data([el['data'] for el in self.elements])
        except Exception as e: messagebox.showerror("Error", f"No se pudo generar la imagen: {e}", parent=self.frame); return
        if not os.path.exists("data/exercise_images"): os.makedirs("data/exercise_images")
        file_path = filedialog.asksaveasfilename(title="Guardar imagen del ejercicio", initialdir="data/exercise_images", defaultextension=".png", filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg")])
        if file_path:
            try: image_to_save.save(file_path); messagebox.showinfo("Éxito", f"Imagen guardada en:\n{file_path}", parent=self.frame)
            except Exception as e: messagebox.showerror("Error al Guardar", f"No se pudo guardar el archivo:\n{e}", parent=self.frame)