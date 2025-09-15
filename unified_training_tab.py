import tkinter as tk
from tkinter import ttk

# Importar las clases de las pestañas que vamos a unificar
from trainings_tab import TrainingsTab
from planning_tab import PlanningTab
from exercises_tab import ExercisesTab
from field_editor_tab import FieldEditorTab

class UnifiedTrainingTab:
    def __init__(self, parent, db):
        self.db = db
        self.frame = ttk.Frame(parent)
        
        # Creamos un Notebook interno para las pestañas de entrenamiento
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill="both", expand=True)

        # Creamos una instancia de cada pestaña que queremos agrupar
        # y guardamos una referencia a ellas para poder accederlas desde main.py
        self.trainings_tab = TrainingsTab(self.notebook, self.db)
        self.planning_tab = PlanningTab(self.notebook, self.db)
        self.exercises_tab = ExercisesTab(self.notebook, self.db)
        self.field_editor_tab = FieldEditorTab(self.notebook, self.db)

        # Añadimos las pestañas al notebook interno
        self.notebook.add(self.trainings_tab.frame, text='Entrenamientos')
        self.notebook.add(self.planning_tab.frame, text='Planificación de Asistencia')
        self.notebook.add(self.exercises_tab.frame, text='Ejercicios')
        self.notebook.add(self.field_editor_tab.frame, text='Editor de Campo')