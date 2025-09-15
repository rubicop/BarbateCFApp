# reports.py
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import colors
from datetime import datetime

class ReportGenerator:
    def __init__(self, db):
        self.db = db

    def generate_training_report(self, training_id, output_path):
        # Obtener datos del entrenamiento
        trainings = self.db.get_all_trainings()
        training = None
        for t in trainings:
            if t[0] == training_id:
                training = t
                break
        
        if not training:
            return False

        # Obtener ejercicios del entrenamiento
        exercises = self.db.get_exercises_by_training(training_id)

        # Crear el documento PDF
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        elements = []

        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            alignment=TA_LEFT
        )
        normal_style = styles['BodyText']

        # Título
        title_text = f"BARBATE C.F. - ENTRENAMIENTO"
        elements.append(Paragraph(title_text, title_style))
        elements.append(Spacer(1, 12))

        # Información del entrenamiento
        elements.append(Paragraph(f"Fecha: {training[1]}", normal_style))
        elements.append(Paragraph(f"Mesociclo: {training[2]}", normal_style))
        elements.append(Paragraph(f"Sesión: {training[3]}", normal_style))
        elements.append(Paragraph(f"Entrenador: {training[4]}", normal_style))
        elements.append(Paragraph(f"Asistente: {training[5]}", normal_style))
        elements.append(Paragraph(f"Material: {training[6]}", normal_style))
        elements.append(Spacer(1, 20))

        # Ejercicios
        if exercises:
            elements.append(Paragraph("EJERCICIOS", heading_style))
            
            for exercise in exercises:
                elements.append(Paragraph(f"Ejercicio: {exercise[2]}", normal_style))
                elements.append(Paragraph(f"Duración: {exercise[4]} minutos", normal_style))
                elements.append(Paragraph(f"Repeticiones: {exercise[5]}", normal_style))
                elements.append(Paragraph(f"Espacio: {exercise[6]}", normal_style))
                elements.append(Paragraph(f"Descripción: {exercise[3]}", normal_style))
                elements.append(Paragraph(f"Objetivos: {exercise[7]}", normal_style))
                elements.append(Paragraph(f"Normas: {exercise[8]}", normal_style))
                elements.append(Paragraph(f"Variantes: {exercise[9]}", normal_style))
                elements.append(Spacer(1, 15))
        else:
            elements.append(Paragraph("No hay ejercicios para este entrenamiento.", normal_style))

        # Generar PDF
        doc.build(elements)
        return True