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

class CoachesTab:
    def __init__(self, notebook, db):
        self.db = db
        self.frame = ttk.Frame(notebook)
        self.current_coach_id = None
        self.photo_path = None
        self.photo_image = None
        
        if not os.path.exists("data/coach_photos"):
            os.makedirs("data/coach_photos")

        self.setup_ui()
        self.load_coaches()

    def setup_ui(self):
        main_frame = ttk.Frame(self.frame, padding=10)
        main_frame.pack(fill="both", expand=True)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # Columna Izquierda: Lista de miembros
        list_frame = ttk.LabelFrame(main_frame, text="Miembros del Cuerpo Técnico")
        list_frame.grid(row=0, column=0, sticky="ns", padx=(0, 10))
        
        cols = ("id", "name", "role")
        self.coaches_tree = ttk.Treeview(list_frame, columns=cols, show="headings", height=25)
        self.coaches_tree.heading("id", text="ID"); self.coaches_tree.column("id", width=40)
        self.coaches_tree.heading("name", text="Nombre"); self.coaches_tree.column("name", width=200)
        self.coaches_tree.heading("role", text="Rol"); self.coaches_tree.column("role", width=150)
        self.coaches_tree.pack(fill="y", expand=True, side="top")
        self.coaches_tree.bind("<<TreeviewSelect>>", self.on_coach_select)

        list_btn_frame = ttk.Frame(list_frame)
        list_btn_frame.pack(fill="x", pady=5)
        ttk.Button(list_btn_frame, text="Nuevo Miembro", command=self.prepare_new_coach).pack(side="left", expand=True)
        ttk.Button(list_btn_frame, text="Eliminar", command=self.delete_coach).pack(side="right", expand=True)

        # Columna Derecha: Detalles del miembro
        details_frame = ttk.LabelFrame(main_frame, text="Detalles del Miembro")
        details_frame.grid(row=0, column=1, sticky="nsew")
        
        p_frame = ttk.Frame(details_frame, padding=10)
        p_frame.pack(fill="both", expand=True)
        
        # Frame superior para foto y datos básicos
        top_frame = ttk.Frame(p_frame)
        top_frame.pack(fill="x", pady=5)
        
        photo_container = tk.Frame(top_frame, width=150, height=150, relief="solid", bd=1)
        photo_container.pack_propagate(False) 
        photo_container.pack(side="left", padx=10, anchor="n")
        self.photo_label = tk.Label(photo_container, text="Sin Foto", bg="lightgrey")
        self.photo_label.pack(fill="both", expand=True)
        
        fields_frame = ttk.Frame(top_frame)
        fields_frame.pack(side="left", fill="x", expand=True, padx=10)
        
        ttk.Label(fields_frame, text="Nombre Completo:").grid(row=0, column=0, sticky="w", pady=3)
        self.coach_name = ttk.Entry(fields_frame, width=40); self.coach_name.grid(row=0, column=1, sticky="ew")
        ttk.Label(fields_frame, text="Rol/Cargo:").grid(row=1, column=0, sticky="w", pady=3)
        self.coach_role = ttk.Entry(fields_frame, width=40); self.coach_role.grid(row=1, column=1, sticky="ew")
        self.select_photo_btn = ttk.Button(fields_frame, text="Seleccionar Foto", command=self.select_photo)
        self.select_photo_btn.grid(row=2, column=1, pady=10, sticky="w")
        
        # Frame de contacto
        contact_frame = ttk.LabelFrame(p_frame, text="Información de Contacto")
        contact_frame.pack(fill="x", pady=10)
        contact_frame.columnconfigure(1, weight=1); contact_frame.columnconfigure(3, weight=1)
        ttk.Label(contact_frame, text="Teléfono:").grid(row=0, column=0, sticky="w", pady=3, padx=5)
        self.coach_phone = ttk.Entry(contact_frame); self.coach_phone.grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Label(contact_frame, text="Dirección:").grid(row=1, column=0, sticky="w", pady=3, padx=5)
        self.coach_address = ttk.Entry(contact_frame); self.coach_address.grid(row=1, column=1, columnspan=3, sticky="ew", padx=5)
        ttk.Label(contact_frame, text="Población:").grid(row=2, column=0, sticky="w", pady=3, padx=5)
        self.coach_town = ttk.Entry(contact_frame); self.coach_town.grid(row=2, column=1, sticky="ew", padx=5)
        ttk.Label(contact_frame, text="Provincia:").grid(row=2, column=2, sticky="w", pady=3, padx=5)
        self.coach_province = ttk.Entry(contact_frame); self.coach_province.grid(row=2, column=3, sticky="ew", padx=5)

        # Frame de observaciones
        obs_frame = ttk.LabelFrame(p_frame, text="Observaciones")
        obs_frame.pack(fill="both", expand=True, pady=10)
        self.coach_observations = tk.Text(obs_frame, height=5); self.coach_observations.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Botones de acción
        ttk.Button(p_frame, text="Guardar Cambios", command=self.save_changes).pack(side="right", pady=10)

    def load_coaches(self):
        for item in self.coaches_tree.get_children():
            self.coaches_tree.delete(item)
        for coach in self.db.get_all_coaches():
            self.coaches_tree.insert("", "end", values=coach[:3], iid=coach[0])
    
    def on_coach_select(self, event=None):
        selected_items = self.coaches_tree.selection()
        if not selected_items: return
        self.current_coach_id = int(selected_items[0])
        
        all_coaches = self.db.get_all_coaches()
        coach_data = next((c for c in all_coaches if c[0] == self.current_coach_id), None)
        
        if coach_data:
            self.clear_form()
            (cid, name, role, photo, phone, address, town, province, obs) = coach_data
            
            self.coach_name.insert(0, name or "")
            self.coach_role.insert(0, role or "")
            self.coach_phone.insert(0, phone or "")
            self.coach_address.insert(0, address or "")
            self.coach_town.insert(0, town or "")
            self.coach_province.insert(0, province or "")
            self.coach_observations.insert("1.0", obs or "")
            
            self.photo_path = photo
            self.load_coach_photo(self.photo_path)

    def save_changes(self):
        name = self.coach_name.get()
        if not name:
            messagebox.showwarning("Faltan Datos", "El nombre es obligatorio.")
            return

        data = (
            name, self.coach_role.get(), self.photo_path,
            self.coach_phone.get(), self.coach_address.get(),
            self.coach_town.get(), self.coach_province.get(),
            self.coach_observations.get("1.0", tk.END).strip()
        )

        if self.current_coach_id:
            self.db.update_coach(self.current_coach_id, *data)
            messagebox.showinfo("Éxito", "Miembro del cuerpo técnico actualizado.")
        else:
            self.db.insert_coach(*data)
            messagebox.showinfo("Éxito", "Nuevo miembro del cuerpo técnico añadido.")
        
        self.load_coaches()
        self.clear_form()
        self.prepare_new_coach()

    def prepare_new_coach(self):
        self.clear_form()
        self.current_coach_id = None
        if self.coaches_tree.selection():
            self.coaches_tree.selection_remove(self.coaches_tree.selection())

    def delete_coach(self):
        selected_items = self.coaches_tree.selection()
        if not selected_items:
            messagebox.showwarning("Sin Selección", "Seleccione un miembro para eliminar.")
            return
        
        coach_id = int(selected_items[0])
        coach_name = self.coaches_tree.item(selected_items[0])['values'][1]
        
        if messagebox.askyesno("Confirmar", f"¿Seguro que quieres eliminar a {coach_name}?"):
            self.db.delete_coach(coach_id)
            self.load_coaches()
            self.clear_form()
            self.prepare_new_coach()
            messagebox.showinfo("Eliminado", "Miembro eliminado.")

    def clear_form(self):
        self.coach_name.delete(0, tk.END)
        self.coach_role.delete(0, tk.END)
        self.coach_phone.delete(0, tk.END)
        self.coach_address.delete(0, tk.END)
        self.coach_town.delete(0, tk.END)
        self.coach_province.delete(0, tk.END)
        self.coach_observations.delete("1.0", tk.END)
        self.photo_path = None
        self.load_coach_photo(None)

    def select_photo(self):
        path = filedialog.askopenfilename(filetypes=[("Archivos de imagen", "*.jpg *.jpeg *.png")])
        if path:
            filename = os.path.basename(path)
            dest_folder = "data/coach_photos"
            if not os.path.exists(dest_folder): os.makedirs(dest_folder)
            dest_path = os.path.join(dest_folder, filename)
            shutil.copy(path, dest_path)
            self.photo_path = dest_path
            self.load_coach_photo(self.photo_path)

    def load_coach_photo(self, path):
        if not path or not os.path.exists(resource_path(path)):
            self.photo_label.config(image='', text="Sin Foto")
            self.photo_image = None
            return
        try:
            full_path = resource_path(path)
            # --- CORRECCIÓN: Usar 'Image' en lugar de 'PILImage' ---
            img = Image.open(full_path)
            img.thumbnail((150, 150), Image.LANCZOS)
            self.photo_image = ImageTk.PhotoImage(img)
            self.photo_label.config(image=self.photo_image, text="")
        except Exception as e:
            print(f"Error al cargar imagen de cuerpo técnico: {e}")
            self.photo_label.config(image='', text="Error Foto")