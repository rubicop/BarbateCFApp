import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image as RLImage
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib import colors
import os
import sys
import json
from io import BytesIO
from PIL import Image as PILImage, ImageTk
import subprocess

try:
    import fitz  # PyMuPDF
except ImportError:
    messagebox.showerror("Librería Faltante", "PyMuPDF no está instalado. Por favor, ejecute 'pip install PyMuPDF' en su terminal.")
    fitz = None

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class SelectionDialog(tk.Toplevel):
    def __init__(self, parent, title, items, callback):
        super().__init__(parent)
        self.title(title); self.geometry("350x400"); self.transient(parent); self.grab_set()
        self.callback = callback
        self.items_map = {item[1]: item[0] for item in items}
        ttk.Label(self, text=f"Seleccione un {title.lower()}:").pack(pady=10)
        self.listbox = tk.Listbox(self)
        self.listbox.pack(fill="both", expand=True, padx=10, pady=5)
        for name in self.items_map.keys():
            self.listbox.insert(tk.END, name)
        ttk.Button(self, text="Aceptar", command=self.on_select).pack(pady=10)

    def on_select(self):
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Sin selección", "Por favor, seleccione un elemento de la lista.", parent=self)
            return
        selected_name = self.listbox.get(selected_indices[0])
        selected_id = self.items_map[selected_name]
        self.callback(selected_id)
        self.destroy()

class PreviewWindow(tk.Toplevel):
    def __init__(self, parent, pil_image, pdf_bytes):
        super().__init__(parent)
        self.title("Vista Preliminar del Reporte"); self.geometry("700x850"); self.transient(parent); self.grab_set()
        self.pdf_bytes = pdf_bytes
        canvas_frame = ttk.Frame(self); canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)
        canvas = tk.Canvas(canvas_frame)
        vsb = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        hsb = ttk.Scrollbar(canvas_frame, orient="horizontal", command=canvas.xview)
        canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y"); hsb.pack(side="bottom", fill="x")
        canvas.pack(side="left", fill="both", expand=True)
        self.photo_image = ImageTk.PhotoImage(pil_image)
        canvas.create_image(0, 0, image=self.photo_image, anchor="nw")
        canvas.config(scrollregion=canvas.bbox("all"))
        btn_frame = ttk.Frame(self); btn_frame.pack(fill="x", padx=10, pady=10)
        ttk.Button(btn_frame, text="Guardar como PDF", command=self.save_pdf).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side="right")

    def save_pdf(self):
        file_path = filedialog.asksaveasfilename(
            initialdir="reportes", defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")], title="Guardar Reporte como PDF"
        )
        if file_path:
            try:
                if not os.path.exists("reportes"):
                    os.makedirs("reportes")
                with open(file_path, "wb") as f: f.write(self.pdf_bytes)
                messagebox.showinfo("Éxito", f"Reporte PDF guardado en:\n{file_path}", parent=self.master)
                self.destroy()
            except PermissionError:
                messagebox.showerror(
                    "Permiso Denegado",
                    f"No se pudo guardar el archivo en:\n{file_path}\n\n"
                    "Causa más probable: El archivo PDF ya está abierto en otra aplicación.\n\n"
                    "Por favor, cierre el visor de PDF e intente guardar el reporte de nuevo.",
                    parent=self
                )
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar el archivo PDF:\n{e}", parent=self)

class ReportCustomizationDialog(tk.Toplevel):
    def __init__(self, parent, db, training_id, callback):
        super().__init__(parent)
        self.db = db; self.training_id = training_id; self.callback = callback
        self.title("Personalizar Reporte de Entrenamiento"); self.geometry("700x450"); self.transient(parent); self.grab_set()
        main_frame = ttk.Frame(self); main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        ex_frame = ttk.LabelFrame(main_frame, text="Seleccionar Ejercicios a Incluir"); ex_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        self.exercise_list = tk.Listbox(ex_frame, selectmode='multiple', exportselection=False); self.exercise_list.pack(fill="both", expand=True)
        ly_frame = ttk.LabelFrame(main_frame, text="Seleccionar Diseños de Campo a Incluir"); ly_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        self.layout_list = tk.Listbox(ly_frame, selectmode='multiple', exportselection=False); self.layout_list.pack(fill="both", expand=True)
        ttk.Button(self, text="Generar PDF", command=self.on_generate).pack(pady=10, ipady=4)
        self.populate_lists()

    def populate_lists(self):
        self.exercises = self.db.get_exercises_by_training(self.training_id)
        for ex in self.exercises: self.exercise_list.insert(tk.END, f"{ex[2]}")
        self.exercise_list.selection_set(0, tk.END)
        self.layouts = self.db.get_all_layouts()
        for lid, name in self.layouts: self.layout_list.insert(tk.END, name)

    def on_generate(self):
        selected_ex_indices = self.exercise_list.curselection(); selected_ly_indices = self.layout_list.curselection()
        selected_exercise_ids = [self.exercises[i][0] for i in selected_ex_indices]
        selected_layout_ids = [self.layouts[i][0] for i in selected_ly_indices]
        self.callback(self.training_id, selected_exercise_ids, selected_layout_ids)
        self.destroy()

class ReportsTab:
    def __init__(self, notebook, db, field_editor):
        self.db = db; self.field_editor = field_editor; self.frame = ttk.Frame(notebook)
        self.current_report_data = []; self.current_report_headers = []; self.current_report_title = ""
        self.setup_ui()
    
    def setup_ui(self):
        main_paned_window = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        main_paned_window.pack(fill="both", expand=True, padx=10, pady=10)
        controls_frame = ttk.Frame(main_paned_window, width=320)
        main_paned_window.add(controls_frame, weight=1)
        
        stats_frame = ttk.LabelFrame(controls_frame, text="Vista de Estadísticas")
        stats_frame.pack(fill="x", pady=5)
        stats_buttons = [("Estadísticas de Plantilla", self.show_squad_stats), ("Historial de Partidos", self.show_matches_history), ("Estadísticas por Partido", self.select_match_for_stats), ("Trayectoria por Jugador", self.select_player_for_career)]
        for text, command in stats_buttons:
            ttk.Button(stats_frame, text=text, command=command).pack(fill="x", padx=10, pady=4, ipady=2)
        
        self.preview_button = ttk.Button(stats_frame, text="Vista Previa y Exportar Tabla", state="disabled", command=self.open_preview)
        self.preview_button.pack(fill="x", padx=10, pady=(10, 4), ipady=2)

        training_report_frame = ttk.LabelFrame(controls_frame, text="Reporte de Entrenamiento")
        training_report_frame.pack(fill="x", pady=20)
        ttk.Label(training_report_frame, text="Seleccione entrenamiento:").pack(pady=5)
        self.training_var = tk.StringVar()
        self.training_dropdown = ttk.Combobox(training_report_frame, textvariable=self.training_var, state="readonly", width=35)
        self.training_dropdown.pack(pady=5, padx=10)
        ttk.Button(training_report_frame, text="Generar Reporte Personalizado", command=self.open_customization_dialog).pack(fill="x", padx=10, pady=10, ipady=2)
        
        ttk.Button(training_report_frame, text="Abrir Carpeta de Reportes", command=self.open_reports_folder).pack(fill="x", padx=10, pady=(0,10), ipady=2)

        data_frame = ttk.Frame(main_paned_window)
        main_paned_window.add(data_frame, weight=4)
        self.tree = ttk.Treeview(data_frame, show="headings")
        vsb = ttk.Scrollbar(data_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(data_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y"); hsb.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)
        
        self.frame.bind("<Visibility>", lambda event: self.load_trainings_dropdown())
        
    def open_reports_folder(self):
        reports_path = "reportes"
        try:
            if not os.path.exists(reports_path):
                os.makedirs(reports_path)
                messagebox.showinfo("Carpeta Creada", f"La carpeta '{reports_path}' no existía y ha sido creada.")
            
            if sys.platform == "win32":
                os.startfile(os.path.abspath(reports_path))
            elif sys.platform == "darwin":
                subprocess.run(["open", os.path.abspath(reports_path)])
            else:
                subprocess.run(["xdg-open", os.path.abspath(reports_path)])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la carpeta de reportes:\n{e}")

    def _setup_treeview(self, headers, data, title):
        self.current_report_headers = headers; self.current_report_data = data; self.current_report_title = title
        for item in self.tree.get_children(): self.tree.delete(item)
        self.tree["columns"] = [h[0] for h in headers]
        for col_id, text, width in headers:
            self.tree.heading(col_id, text=text, command=lambda c=col_id: self._sort_column(c, False))
            self.tree.column(col_id, width=width, anchor="center")
        for row in data:
            self.tree.insert("", "end", values=row)
        self.preview_button.config(state="normal")

    def _sort_column(self, col, reverse):
        try:
            data_list = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
            try: data_list.sort(key=lambda t: float(t[0]), reverse=reverse)
            except ValueError: data_list.sort(key=lambda t: t[0].lower(), reverse=reverse)
            for index, (val, k) in enumerate(data_list): self.tree.move(k, '', index)
            self.tree.heading(col, command=lambda: self._sort_column(col, not reverse))
        except Exception as e: print(f"Error al ordenar: {e}")

    def show_squad_stats(self):
        headers = [("name", "Jugador", 180), ("pj", "PJ", 50), ("mins", "Min", 50), ("g", "G", 50), ("a", "A", 50), ("t", "T", 50), ("ta", "TA", 50), ("tr", "TR", 50)]
        data = self.db.get_squad_stats_report(); processed_data = [(row[0], row[3], row[4], row[5], row[6], row[7], row[8], row[9]) for row in data]
        self._setup_treeview(headers, processed_data, "Reporte Global de Estadísticas de Plantilla")

    def show_matches_history(self):
        headers = [("date", "Fecha", 120), ("rival", "Rival", 200), ("result", "Resultado", 100)]
        data = self.db.get_all_matches(); processed_data = [(row[1], row[2], row[3]) for row in data]
        self._setup_treeview(headers, processed_data, "Historial de Partidos")

    def select_match_for_stats(self):
        matches = self.db.get_all_matches(); items_for_dialog = [(m[0], f"{m[1]} vs {m[2]} ({m[3]})") for m in matches]
        SelectionDialog(self.frame, "Partido", items_for_dialog, self._load_match_stats)

    def _load_match_stats(self, match_id):
        headers = [("name", "Jugador", 180), ("num", "Nº", 50), ("mins", "Min", 50), ("g", "G", 50), ("a", "A", 50), ("t", "T", 50), ("ta", "TA", 50), ("tr", "TR", 50)]
        data = self.db.get_match_stats_report(match_id); processed_data = [(row[0], row[3], row[4], row[5], row[6], row[7], row[8], row[9]) for row in data]
        match_details = self.db.get_match_details(match_id); title = f"Estadísticas del Partido: vs {match_details[3]} ({match_details[1]})"
        self._setup_treeview(headers, processed_data, title)

    def select_player_for_career(self):
        players = self.db.get_all_players(); items_for_dialog = [(p[0], p[1]) for p in players]
        SelectionDialog(self.frame, "Jugador", items_for_dialog, self._load_player_career)

    def _load_player_career(self, player_id):
        headers = [("season", "Temporada", 100), ("team", "Equipo", 180), ("pj", "PJ", 50), ("g", "G", 50), ("a", "A", 50), ("ta", "TA", 50), ("tr", "TR", 50)]
        data = self.db.get_career_history_for_player(player_id); processed_data = [(row[2], row[3], row[4], row[5], row[6], row[7], row[8]) for row in data]
        player_details = self.db.get_player_by_id(player_id); title = f"Trayectoria de {player_details[1]}"
        self._setup_treeview(headers, processed_data, title)

    def _create_stats_pdf_in_memory(self):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20*mm, leftMargin=15*mm, rightMargin=15*mm, bottomMargin=20*mm)
        elements = []; styles = getSampleStyleSheet()
        try:
            logo_path = resource_path("club_logo.png")
            if os.path.exists(logo_path):
                logo = RLImage(logo_path, width=30*mm, height=30*mm); logo.hAlign = 'CENTER'; elements.append(logo); elements.append(Spacer(1, 8*mm))
        except Exception as e: print(f"No se pudo cargar el logo: {e}")
        
        title_style = ParagraphStyle('CustomTitle', parent=styles['h1'], alignment=TA_CENTER, fontSize=16, spaceAfter=12)
        elements.append(Paragraph(self.current_report_title, title_style))
        table_headers = [h[1] for h in self.current_report_headers]
        table_data = [table_headers] + [list(map(str, row)) for row in self.current_report_data]
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table); doc.build(elements); pdf_bytes = buffer.getvalue(); buffer.close()
        return pdf_bytes

    def open_preview(self):
        if not self.current_report_data: messagebox.showwarning("Sin datos", "No hay datos para previsualizar."); return
        if not fitz: messagebox.showerror("Librería Faltante", "PyMuPDF no está instalado."); return
        try:
            pdf_bytes = self._create_stats_pdf_in_memory()
            pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf"); page = pdf_doc[0]
            pix = page.get_pixmap(dpi=150); pdf_doc.close()
            pil_image = PILImage.frombytes("RGB", [pix.width, pix.height], pix.samples)
            PreviewWindow(self.frame, pil_image, pdf_bytes)
        except Exception as e: messagebox.showerror("Error de Previsualización", f"No se pudo generar la vista previa:\n{e}")

    def load_trainings_dropdown(self):
        trainings = self.db.get_all_trainings()
        self.training_map = {f"{t[1]} - Sesión {t[3]}": t[0] for t in trainings}
        self.training_dropdown['values'] = list(self.training_map.keys())
        if self.training_dropdown['values']: self.training_dropdown.current(0)

    def open_customization_dialog(self):
        selected_text = self.training_var.get()
        if not selected_text: messagebox.showwarning("Sin Selección", "Por favor, seleccione un entrenamiento."); return
        training_id = self.training_map[selected_text]
        ReportCustomizationDialog(self.frame, self.db, training_id, self.start_pdf_generation)

    def start_pdf_generation(self, training_id, exercise_ids, layout_ids):
        if not os.path.exists("reportes"):
            os.makedirs("reportes")
        file_path = filedialog.asksaveasfilename(initialdir="reportes", defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")], title="Guardar Reporte de Entrenamiento")
        if not file_path: return
        
        try:
            self.build_training_pdf(training_id, exercise_ids, layout_ids, file_path)
            messagebox.showinfo("Éxito", f"Reporte generado en:\n{file_path}")
        except PermissionError:
            messagebox.showerror(
                "Permiso Denegado",
                f"No se pudo guardar el archivo en:\n{file_path}\n\n"
                "Causa más probable: El archivo PDF ya está abierto en otra aplicación.\n\n"
                "Por favor, cierre el visor de PDF e intente generar el reporte de nuevo."
            )
        except Exception as e:
            messagebox.showerror("Error Inesperado", f"Ocurrió un error al generar el reporte:\n\n{e}")

    def build_training_pdf(self, training_id, exercise_ids, layout_ids, file_path):
        doc = SimpleDocTemplate(file_path, pagesize=A4, topMargin=35*mm, leftMargin=15*mm, rightMargin=15*mm, bottomMargin=15*mm)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='ReportTitle', parent=styles['h1'], alignment=TA_CENTER, fontSize=18, spaceAfter=2))
        styles.add(ParagraphStyle(name='ReportSubTitle', parent=styles['h2'], alignment=TA_CENTER, fontSize=12, spaceAfter=12))
        styles.add(ParagraphStyle(name='SectionHeader', parent=styles['h3'], fontSize=11, spaceBefore=10, spaceAfter=5, textColor=colors.darkblue))
        styles.add(ParagraphStyle(name='ReportBodyText', parent=styles['Normal'], fontSize=9, leading=11))
        
        elements = []
        training_details = next((t for t in self.db.get_all_trainings() if t[0] == training_id), None)
        if not training_details: return

        info_data = [
            [Paragraph('<b>Fecha:</b>', styles['ReportBodyText']), Paragraph(training_details[1], styles['ReportBodyText']), Paragraph('<b>Mesociclo:</b>', styles['ReportBodyText']), Paragraph(training_details[2], styles['ReportBodyText'])],
            [Paragraph('<b>Nº de sesión:</b>', styles['ReportBodyText']), Paragraph(str(training_details[3]), styles['ReportBodyText']), '', ''],
            [Paragraph('<b>Entrenador:</b>', styles['ReportBodyText']), Paragraph(training_details[4], styles['ReportBodyText']), Paragraph('<b>2º Entrenador, PF:</b>', styles['ReportBodyText']), Paragraph(training_details[5], styles['ReportBodyText'])]
        ]
        info_table = Table(info_data, colWidths=[35*mm, 60*mm, 40*mm, 45*mm]); info_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
        elements.append(info_table); elements.append(Spacer(1, 8*mm))
        
        elements.append(Paragraph("CONVOCATORIA", styles['SectionHeader']))
        attendance = self.db.get_attendance_for_training(training_id)
        if attendance:
            player_groups = {"PORTEROS": [], "DEFENSAS": [], "MEDIOS": [], "EXTREMOS": [], "DELANTEROS": []}
            pos_map = {"Portero": "PORTEROS", "Defensa": "DEFENSAS", "Mediocentro": "MEDIOS"}
            for p_data in attendance:
                shirt_name = p_data[5]
                full_name = p_data[1]
                name_to_display = shirt_name if shirt_name else full_name
                player_pos = p_data[2]
                assigned_group = pos_map.get(player_pos, "DELANTEROS")
                player_groups[assigned_group].append(name_to_display)
            
            headers = [h for h in player_groups.keys()]
            max_rows = max(len(v) for v in player_groups.values()) if any(player_groups.values()) else 0
            player_table_data = [headers]
            for i in range(max_rows):
                row = [player_groups[cat][i] if i < len(player_groups[cat]) else '' for cat in player_groups.keys()]
                player_table_data.append(row)

            player_table = Table(player_table_data, colWidths=[30*mm]*len(player_groups))
            player_table.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.lightgrey), ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('FONTSIZE', (0,0), (-1,-1), 8), ('GRID', (0,0), (-1,-1), 1, colors.black)]))
            elements.append(player_table); elements.append(Spacer(1, 8*mm))
        
        if training_details[6]:
            elements.append(Paragraph("MATERIAL", styles['SectionHeader'])); elements.append(Paragraph(training_details[6].replace('\n', '<br/>'), styles['ReportBodyText'])); elements.append(Spacer(1, 8*mm))
        
        if layout_ids:
            elements.append(Paragraph("DISEÑOS TÁCTICOS", styles['SectionHeader']))
            for lid in layout_ids:
                layout_json = self.db.get_layout_data_by_id(lid)
                if layout_json:
                    layout_data = json.loads(layout_json)
                    field_image = self.field_editor.create_image_from_layout_data(layout_data)
                    buffer = BytesIO()
                    field_image.save(buffer, format="PNG")
                    buffer.seek(0)
                    elements.append(RLImage(buffer, width=180*mm, height=112.5*mm))
                    elements.append(Spacer(1, 5*mm))
            elements.append(PageBreak())
            
        selected_exercises = self.db.get_exercises_by_ids(exercise_ids)
        if selected_exercises:
            exercise_groups = {}
            for ex in selected_exercises:
                category = ex[11] or "Ejercicios Generales"
                if category not in exercise_groups: exercise_groups[category] = []
                exercise_groups[category].append(ex)
                
            category_order = ["Calentamiento", "Físico", "Técnico", "Táctico", "Estrategia", "Vuelta a la Calma", "Ejercicios Generales"]
            
            for category in category_order:
                if category in exercise_groups:
                    elements.append(Paragraph(category.upper(), styles['SectionHeader']))
                    for ex in exercise_groups[category]: elements.extend(self.format_exercise_for_pdf(ex, styles))
                    elements.append(Spacer(1, 5*mm))
                    del exercise_groups[category]

            for category, exercises in exercise_groups.items():
                elements.append(Paragraph(category.upper(), styles['SectionHeader']))
                for ex in exercises: elements.extend(self.format_exercise_for_pdf(ex, styles))
                elements.append(Spacer(1, 5*mm))

        def header_footer(canvas, doc):
            canvas.saveState()
            try:
                logo_path = resource_path("club_logo.png")
                if os.path.exists(logo_path): canvas.drawImage(logo_path, 15*mm, A4[1] - 30*mm, width=25*mm, height=25*mm, preserveAspectRatio=True, mask='auto')
            except Exception as e: print(f"Error al dibujar logo: {e}")
            p_title = Paragraph("BARBATE C. F.", styles['ReportTitle']); p_subtitle = Paragraph(training_details[2] or "Entrenamiento", styles['ReportSubTitle'])
            p_title.wrapOn(canvas, doc.width - 40*mm, doc.topMargin); p_title.drawOn(canvas, doc.leftMargin + 30*mm, A4[1] - 20*mm)
            p_subtitle.wrapOn(canvas, doc.width - 40*mm, doc.topMargin); p_subtitle.drawOn(canvas, doc.leftMargin + 30*mm, A4[1] - 27*mm)
            canvas.restoreState()
            
        doc.build(elements, onFirstPage=header_footer, onLaterPages=header_footer)
        
    def format_exercise_for_pdf(self, ex_data, styles):
        (eid, tid, name, desc, dur, rep, space, obj, rules, var, img_path, category) = ex_data
        
        desc = desc.replace('\n', '<br/>') if desc else ''
        obj = obj.replace('\n', '<br/>') if obj else ''
        rules = rules.replace('\n', '<br/>') if rules else ''
        var = var.replace('\n', '<br/>') if var else ''

        header_data = [
            Paragraph(f"<b>Tarea:</b> {name or ''}", styles['ReportBodyText']),
            Paragraph(f"<b>Tiempo:</b> {str(dur) if dur else ''}'", styles['ReportBodyText']),
            Paragraph(f"<b>Rep:</b> {str(rep) if rep else ''}", styles['ReportBodyText']),
            Paragraph(f"<b>Espacio:</b> {space or ''}", styles['ReportBodyText'])]
        header_table = Table([header_data], colWidths=[85*mm, 25*mm, 25*mm, 45*mm])
        header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
        
        left_cell_content = [
            Paragraph(f"<b>Descripción:</b> {desc}", styles['ReportBodyText']), Spacer(1, 2*mm),
            Paragraph(f"<b>Objetivos:</b> {obj}", styles['ReportBodyText']), Spacer(1, 2*mm),
            Paragraph(f"<b>Normas:</b> {rules}", styles['ReportBodyText']), Spacer(1, 2*mm),
            Paragraph(f"<b>Variantes:</b> {var}", styles['ReportBodyText'])]
        right_cell_content = []
        if img_path and os.path.exists(resource_path(img_path)):
            try:
                img = RLImage(resource_path(img_path), width=73*mm, height=55*mm)
                img.preserveAspectRatio = True
                img.hAlign = 'CENTER'
                right_cell_content.append(img)
            except Exception as e: 
                print(f"Error al cargar imagen de ejercicio en PDF: {e}")
                right_cell_content.append(Paragraph("Error al cargar imagen.", styles['ReportBodyText']))
        
        body_table = Table([[left_cell_content, right_cell_content]], colWidths=[105*mm, 75*mm])
        body_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (0,0), 'TOP'), 
            ('VALIGN', (1,0), (1,0), 'MIDDLE'),
            ('ALIGN', (1,0), (1,0), 'CENTER'),
        ]))
        
        container_table = Table([[header_table], [body_table]], rowHeights=[None, None], colWidths=[180*mm])
        container_table.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 1, colors.black),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ]))
        return [container_table, Spacer(1, 5*mm)]