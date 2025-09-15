import sqlite3
import os
import json
import sys

def resource_path(relative_path):
    """ Obtiene la ruta absoluta al recurso, funciona para dev y para PyInstaller """
    try:
        # PyInstaller crea una carpeta temporal y almacena la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class Database:
    def __init__(self):
        db_path = resource_path("data/barbate_cf.db")
        if not os.path.exists(os.path.dirname(db_path)):
            os.makedirs(os.path.dirname(db_path))
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY, name TEXT NOT NULL, position TEXT NOT NULL, number INTEGER, 
                date_of_birth TEXT, nationality TEXT, dominant_foot TEXT, height_cm INTEGER, 
                weight_kg INTEGER, photo_path TEXT, observations TEXT, shirt_name TEXT,
                phone TEXT, email TEXT, address TEXT, town TEXT, city TEXT
            )''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS coaches (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                name TEXT NOT NULL, 
                role TEXT, 
                photo_path TEXT,
                phone TEXT,
                address TEXT,
                town TEXT,
                province TEXT,
                observations TEXT
            )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS career_history (id INTEGER PRIMARY KEY, player_id INTEGER NOT NULL, season TEXT, team_name TEXT, matches_played INTEGER DEFAULT 0, goals_scored INTEGER DEFAULT 0, assists INTEGER DEFAULT 0, yellow_cards INTEGER DEFAULT 0, red_cards INTEGER DEFAULT 0, saves INTEGER DEFAULT 0, goals_conceded INTEGER DEFAULT 0, FOREIGN KEY (player_id) REFERENCES players (id) ON DELETE CASCADE)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS injuries (id INTEGER PRIMARY KEY, player_id INTEGER NOT NULL, injury_date TEXT, injury_type TEXT, recovery_period TEXT, notes TEXT, FOREIGN KEY (player_id) REFERENCES players (id) ON DELETE CASCADE)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS trainings (id INTEGER PRIMARY KEY, date TEXT NOT NULL, mesocycle TEXT, session_number INTEGER, coach TEXT, assistant_coach TEXT, material TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS exercises (id INTEGER PRIMARY KEY, training_id INTEGER, name TEXT, description TEXT, duration INTEGER, repetitions TEXT, space TEXT, objectives TEXT, rules TEXT, variants TEXT, image_path TEXT, category TEXT, FOREIGN KEY (training_id) REFERENCES trainings (id) ON DELETE CASCADE)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS training_attendance (training_id INTEGER NOT NULL, player_id INTEGER NOT NULL, status TEXT NOT NULL, PRIMARY KEY (training_id, player_id), FOREIGN KEY (training_id) REFERENCES trainings (id) ON DELETE CASCADE, FOREIGN KEY (player_id) REFERENCES players (id) ON DELETE CASCADE)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS field_layouts (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, layout_data TEXT NOT NULL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS match_callups (id INTEGER PRIMARY KEY AUTOINCREMENT, match_date TEXT, rival TEXT, venue TEXT, is_home BOOLEAN, city TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS callup_players (callup_id INTEGER NOT NULL, player_id INTEGER NOT NULL, status TEXT NOT NULL, pos_x INTEGER, pos_y INTEGER, PRIMARY KEY (callup_id, player_id), FOREIGN KEY (callup_id) REFERENCES match_callups (id) ON DELETE CASCADE, FOREIGN KEY (player_id) REFERENCES players (id) ON DELETE CASCADE)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS training_templates (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, exercises_data TEXT, attendance_data TEXT, material TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS matches (id INTEGER PRIMARY KEY AUTOINCREMENT, match_date TEXT, competition TEXT, rival TEXT, venue TEXT, is_home BOOLEAN, result TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS player_match_stats (match_id INTEGER NOT NULL, player_id INTEGER NOT NULL, minutes_played INTEGER DEFAULT 0, goals INTEGER DEFAULT 0, assists INTEGER DEFAULT 0, shots INTEGER DEFAULT 0, yellow_cards INTEGER DEFAULT 0, red_cards INTEGER DEFAULT 0, PRIMARY KEY (match_id, player_id), FOREIGN KEY (match_id) REFERENCES matches (id) ON DELETE CASCADE, FOREIGN KEY (player_id) REFERENCES players (id) ON DELETE CASCADE)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS callup_coaches (callup_id INTEGER NOT NULL, coach_id INTEGER NOT NULL, PRIMARY KEY (callup_id, coach_id), FOREIGN KEY (callup_id) REFERENCES match_callups (id) ON DELETE CASCADE, FOREIGN KEY (coach_id) REFERENCES coaches (id) ON DELETE CASCADE)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS formations (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, positions_json TEXT)''')
        
        coach_columns = [desc[1] for desc in cursor.execute("PRAGMA table_info(coaches)").fetchall()]
        new_coach_cols = {'phone': 'TEXT', 'address': 'TEXT', 'town': 'TEXT', 'province': 'TEXT', 'observations': 'TEXT'}
        for col, col_type in new_coach_cols.items():
            if col not in coach_columns:
                cursor.execute(f"ALTER TABLE coaches ADD COLUMN {col} {col_type}")

        self.conn.commit()

    # --- Métodos para Tácticas ---
    def get_all_formations(self):
        return self.conn.execute("SELECT * FROM formations ORDER BY name ASC").fetchall()
    
    def insert_formation(self, name, positions_json):
        self.conn.execute("INSERT INTO formations (name, positions_json) VALUES (?, ?)", (name, positions_json))
        self.conn.commit()
    
    def update_formation(self, f_id, name, positions_json):
        self.conn.execute("UPDATE formations SET name=?, positions_json=? WHERE id=?", (name, positions_json, f_id))
        self.conn.commit()
    
    def delete_formation(self, f_id):
        self.conn.execute("DELETE FROM formations WHERE id=?", (f_id,))
        self.conn.commit()

    # --- Métodos para Cuerpo Técnico ---
    def get_all_coaches(self):
        return self.conn.execute("SELECT id, name, role, photo_path, phone, address, town, province, observations FROM coaches ORDER BY name ASC").fetchall()
    
    def get_all_coach_names(self):
        """Devuelve una lista solo con los nombres de los entrenadores para los desplegables."""
        return [row[0] for row in self.conn.execute("SELECT name FROM coaches ORDER BY name ASC").fetchall()]
    
    def insert_coach(self, name, role, photo_path, phone, address, town, province, observations):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO coaches (name, role, photo_path, phone, address, town, province, observations) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (name, role, photo_path, phone, address, town, province, observations))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_coach(self, coach_id, name, role, photo_path, phone, address, town, province, observations):
        self.conn.execute("UPDATE coaches SET name=?, role=?, photo_path=?, phone=?, address=?, town=?, province=?, observations=? WHERE id=?", (name, role, photo_path, phone, address, town, province, observations, coach_id))
        self.conn.commit()
    
    def delete_coach(self, coach_id):
        self.conn.execute("DELETE FROM coaches WHERE id = ?", (coach_id,))
        self.conn.commit()
    
    # --- Métodos para Jugadores ---
    def get_all_players(self): 
        return self.conn.execute("SELECT id, name, position, number, date_of_birth, nationality, dominant_foot, height_cm, weight_kg, photo_path, observations, shirt_name, phone, email, address, town, city FROM players ORDER BY name ASC").fetchall()
    
    def get_player_by_id(self, player_id): 
        return self.conn.execute("SELECT id, name, position, number, date_of_birth, nationality, dominant_foot, height_cm, weight_kg, photo_path, observations, shirt_name, phone, email, address, town, city FROM players WHERE id = ?", (player_id,)).fetchone()
    
    def insert_player(self, name, pos, num, dob, nat, foot, h, w, photo, obs, s_name, phone, email, address, town, city):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO players (name, position, number, date_of_birth, nationality, dominant_foot, height_cm, weight_kg, photo_path, observations, shirt_name, phone, email, address, town, city) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (name, pos, num, dob, nat, foot, h, w, photo, obs, s_name, phone, email, address, town, city))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_player(self, pid, name, pos, num, dob, nat, foot, h, w, photo, obs, s_name, phone, email, address, town, city):
        self.conn.execute("UPDATE players SET name=?, position=?, number=?, date_of_birth=?, nationality=?, dominant_foot=?, height_cm=?, weight_kg=?, photo_path=?, observations=?, shirt_name=?, phone=?, email=?, address=?, town=?, city=? WHERE id=?", (name, pos, num, dob, nat, foot, h, w, photo, obs, s_name, phone, email, address, town, city, pid))
        self.conn.commit()
    
    def delete_player(self, player_id):
        self.conn.execute("DELETE FROM players WHERE id = ?", (player_id,))
        self.conn.commit()

    # --- Métodos para Convocatorias ---
    def get_all_match_callups(self):
        return self.conn.execute("SELECT id, match_date, rival FROM match_callups ORDER BY match_date DESC").fetchall()

    def get_match_callup_details(self, callup_id):
        return self.conn.execute("SELECT * FROM match_callups WHERE id = ?", (callup_id,)).fetchone()

    def get_players_for_callup(self, callup_id, status):
        return self.conn.execute("SELECT p.id, p.name, p.position, p.number, cp.pos_x, cp.pos_y FROM players p JOIN callup_players cp ON p.id = cp.player_id WHERE cp.callup_id = ? AND cp.status = ?", (callup_id, status)).fetchall()

    def get_players_for_callup_with_photo(self, callup_id, status):
        return self.conn.execute("SELECT p.id, p.name, p.shirt_name, p.number, p.photo_path FROM players p JOIN callup_players cp ON p.id = cp.player_id WHERE cp.callup_id = ? AND cp.status = ?", (callup_id, status)).fetchall()

    def get_coaches_for_callup(self, callup_id):
        return self.conn.execute("SELECT c.id, c.name, c.role FROM coaches c JOIN callup_coaches cc ON c.id = cc.coach_id WHERE cc.callup_id = ?", (callup_id,)).fetchall()

    def save_match_callup(self, details, player_lists, coach_ids):
        cursor = self.conn.cursor()
        callup_id = details.get('id')
        data = (details['match_date'], details['rival'], details['venue'], details['is_home'], details['city'])
        
        if callup_id:
            cursor.execute("UPDATE match_callups SET match_date=?, rival=?, venue=?, is_home=?, city=? WHERE id=?", (*data, callup_id))
        else:
            cursor.execute("INSERT INTO match_callups (match_date, rival, venue, is_home, city) VALUES (?, ?, ?, ?, ?)", data)
            callup_id = cursor.lastrowid
        
        cursor.execute("DELETE FROM callup_players WHERE callup_id = ?", (callup_id,))
        cursor.execute("DELETE FROM callup_coaches WHERE callup_id = ?", (callup_id,))

        for status, players in player_lists.items():
            if status == 'convocado':
                for p_id, x, y in players:
                    cursor.execute("INSERT INTO callup_players (callup_id, player_id, status, pos_x, pos_y) VALUES (?, ?, ?, ?, ?)", (callup_id, p_id, status, x, y))
            else:
                for p_id in players:
                    cursor.execute("INSERT INTO callup_players (callup_id, player_id, status) VALUES (?, ?, ?)", (callup_id, p_id, status))
        
        for coach_id in coach_ids:
            cursor.execute("INSERT INTO callup_coaches (callup_id, coach_id) VALUES (?, ?)", (callup_id, coach_id))

        self.conn.commit()
        return callup_id

    def delete_match_callup(self, callup_id):
        self.conn.execute("DELETE FROM match_callups WHERE id = ?", (callup_id,))
        self.conn.commit()
    
    # --- Métodos para Partidos y Estadísticas ---
    def get_all_matches(self):
        return self.conn.execute("SELECT id, match_date, rival, result FROM matches ORDER BY match_date DESC").fetchall()
    
    def get_match_details(self, match_id):
        return self.conn.execute("SELECT * FROM matches WHERE id = ?", (match_id,)).fetchone()
    
    def save_match(self, details):
        cursor = self.conn.cursor()
        match_id = details.get('id')
        data = (details['match_date'], details['competition'], details['rival'], details['venue'], details['is_home'], details['result'])
        if match_id:
            cursor.execute("UPDATE matches SET match_date=?, competition=?, rival=?, venue=?, is_home=?, result=? WHERE id=?", (*data, match_id))
        else:
            cursor.execute("INSERT INTO matches (match_date, competition, rival, venue, is_home, result) VALUES (?,?,?,?,?,?)", data)
            match_id = cursor.lastrowid
        self.conn.commit()
        return match_id
    
    def delete_match(self, match_id):
        self.conn.execute("DELETE FROM matches WHERE id = ?", (match_id,))
        self.conn.commit()
    
    def get_stats_for_match(self, match_id):
        return self.conn.execute("SELECT p.id, p.name, p.number, COALESCE(s.minutes_played, 0), COALESCE(s.goals, 0), COALESCE(s.assists, 0), COALESCE(s.shots, 0), COALESCE(s.yellow_cards, 0), COALESCE(s.red_cards, 0) FROM players p LEFT JOIN player_match_stats s ON p.id = s.player_id AND s.match_id = ? ORDER BY p.name ASC", (match_id,)).fetchall()
    
    def save_player_stats_for_match(self, match_id, stats_data):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM player_match_stats WHERE match_id = ?", (match_id,))
        for player_stats in stats_data:
            cursor.execute("INSERT INTO player_match_stats (match_id, player_id, minutes_played, goals, assists, shots, yellow_cards, red_cards) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (match_id, *player_stats))
        self.conn.commit()
    
    def get_squad_stats_report(self):
        return self.conn.execute("SELECT p.name, p.shirt_name, p.photo_path, COUNT(s.match_id), SUM(s.minutes_played), SUM(s.goals), SUM(s.assists), SUM(s.shots), SUM(s.yellow_cards), SUM(s.red_cards) FROM players p LEFT JOIN player_match_stats s ON p.id = s.player_id GROUP BY p.id HAVING COUNT(s.match_id) > 0 ORDER BY p.name ASC").fetchall()
    
    def get_match_stats_report(self, match_id):
        return self.conn.execute("SELECT p.name, p.shirt_name, p.photo_path, p.number, s.minutes_played, s.goals, s.assists, s.shots, s.yellow_cards, s.red_cards FROM player_match_stats s JOIN players p ON s.player_id = p.id WHERE s.match_id = ? ORDER BY s.minutes_played DESC, p.name ASC", (match_id,)).fetchall()

    # --- Métodos para Entrenamientos, Ejercicios, Plantillas y Diseños ---
    def get_all_trainings_for_dropdown(self): 
        return self.conn.execute("SELECT id, date, mesocycle, session_number FROM trainings ORDER BY date DESC").fetchall()

    def get_all_trainings(self): 
        return self.conn.execute("SELECT * FROM trainings ORDER BY date DESC").fetchall()

    def delete_training(self, training_id):
        """Elimina un entrenamiento y todos sus datos asociados manualmente."""
        cursor = self.conn.cursor()
        # Borrado manual en cascada para asegurar compatibilidad con BD antiguas
        cursor.execute("DELETE FROM exercises WHERE training_id = ?", (training_id,))
        cursor.execute("DELETE FROM training_attendance WHERE training_id = ?", (training_id,))
        # Finalmente, borra el entrenamiento
        cursor.execute("DELETE FROM trainings WHERE id = ?", (training_id,))
        self.conn.commit()

    def save_layout(self, name, layout_data):
        self.conn.execute("INSERT OR REPLACE INTO field_layouts (name, layout_data) VALUES (?, ?)", (name, layout_data))
        self.conn.commit()

    def update_layout_name(self, layout_id, new_name):
        self.conn.execute("UPDATE field_layouts SET name = ? WHERE id = ?", (new_name, layout_id))
        self.conn.commit()

    def delete_layout(self, layout_id):
        self.conn.execute("DELETE FROM field_layouts WHERE id = ?", (layout_id,))
        self.conn.commit()

    def get_all_layouts(self):
        return self.conn.execute("SELECT id, name FROM field_layouts ORDER BY name ASC").fetchall()

    def get_layout_data_by_id(self, layout_id):
        result = self.conn.execute("SELECT layout_data FROM field_layouts WHERE id = ?", (layout_id,)).fetchone()
        return result[0] if result else None

    def get_exercises_by_ids(self, exercise_ids):
        if not exercise_ids: return []
        placeholders = ', '.join('?' for _ in exercise_ids)
        query = f"SELECT * FROM exercises WHERE id IN ({placeholders})"
        return self.conn.execute(query, exercise_ids).fetchall()

    def get_exercises_by_training(self, training_id):
        if training_id is None:
            return self.conn.execute("SELECT * FROM exercises ORDER BY name ASC").fetchall()
        else:
            return self.conn.execute("SELECT * FROM exercises WHERE training_id = ? ORDER BY name ASC", (training_id,)).fetchall()
    
    def insert_training(self, date, mesocycle, session, coach, assistant, material):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO trainings (date, mesocycle, session_number, coach, assistant_coach, material) VALUES (?, ?, ?, ?, ?, ?)", (date, mesocycle, session, coach, assistant, material))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_training(self, tid, date, mesocycle, session, coach, assistant, material):
        self.conn.execute("UPDATE trainings SET date = ?, mesocycle = ?, session_number = ?, coach = ?, assistant_coach = ?, material = ? WHERE id = ?", (date, mesocycle, session, coach, assistant, material, tid))
        self.conn.commit()

    def insert_exercise(self, training_id, name, desc, dur, rep, space, obj, rules, var, img, category):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO exercises (training_id, name, description, duration, repetitions, space, objectives, rules, variants, image_path, category) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (training_id, name, desc, dur, rep, space, obj, rules, var, img, category))
        self.conn.commit()
        return cursor.lastrowid

    def update_exercise(self, eid, tid, name, desc, dur, rep, space, obj, rules, var, img, category):
        self.conn.execute("UPDATE exercises SET training_id=?, name=?, description=?, duration=?, repetitions=?, space=?, objectives=?, rules=?, variants=?, image_path=?, category=? WHERE id=?", (tid, name, desc, dur, rep, space, obj, rules, var, img, category, eid))
        self.conn.commit()

    def delete_exercise(self, exercise_id):
        self.conn.execute("DELETE FROM exercises WHERE id = ?", (exercise_id,))
        self.conn.commit()

    def get_exercise_by_id(self, exercise_id):
        return self.conn.execute("SELECT * FROM exercises WHERE id = ?", (exercise_id,)).fetchone()
    
    def get_attendance_for_training(self, training_id): 
        return self.conn.execute("SELECT p.id, p.name, p.position, ta.status, p.photo_path, p.shirt_name FROM players p JOIN training_attendance ta ON p.id = ta.player_id WHERE ta.training_id = ?", (training_id,)).fetchall()
    
    def get_unassigned_players(self, training_id):
        return self.conn.execute("SELECT * FROM players WHERE id NOT IN (SELECT player_id FROM training_attendance WHERE training_id = ?)", (training_id,)).fetchall()
    
    def set_player_attendance(self, training_id, player_id, status):
        self.conn.execute("INSERT INTO training_attendance (training_id, player_id, status) VALUES (?, ?, ?) ON CONFLICT(training_id, player_id) DO UPDATE SET status = excluded.status", (training_id, player_id, status))
        self.conn.commit()
    
    def remove_player_from_training(self, training_id, player_id):
        self.conn.execute("DELETE FROM training_attendance WHERE training_id = ? AND player_id = ?", (training_id, player_id))
        self.conn.commit()
        
    def save_training_as_template(self, training_id, template_name):
        cursor = self.conn.cursor()
        try:
            training_info = cursor.execute("SELECT material FROM trainings WHERE id=?", (training_id,)).fetchone()
            exercises = cursor.execute("SELECT name, description, duration, repetitions, space, objectives, rules, variants, image_path, category FROM exercises WHERE training_id=?", (training_id,)).fetchall()
            attendance = cursor.execute("SELECT player_id, status FROM training_attendance WHERE training_id=?", (training_id,)).fetchall()
            exercises_json = json.dumps(exercises); attendance_json = json.dumps(attendance)
            material = training_info[0] if training_info else ""
            cursor.execute("INSERT INTO training_templates (name, exercises_data, attendance_data, material) VALUES (?, ?, ?, ?)", (template_name, exercises_json, attendance_json, material))
            self.conn.commit()
            return True
        except self.conn.IntegrityError: return False
        except Exception as e: print(f"Error al guardar plantilla: {e}"); self.conn.rollback(); return False
    
    def get_all_templates(self):
        return self.conn.execute("SELECT id, name FROM training_templates ORDER BY name ASC").fetchall()
    
    def delete_template(self, template_id):
        self.conn.execute("DELETE FROM training_templates WHERE id = ?", (template_id,))
        self.conn.commit()
    
    def load_template_to_training(self, template_id, target_training_id):
        cursor = self.conn.cursor()
        try:
            template_data = cursor.execute("SELECT exercises_data, attendance_data, material FROM training_templates WHERE id=?", (template_id,)).fetchone()
            if not template_data: return False
            exercises_json, attendance_json, material = template_data
            exercises = json.loads(exercises_json); attendance = json.loads(attendance_json)
            cursor.execute("DELETE FROM exercises WHERE training_id = ?", (target_training_id,))
            cursor.execute("DELETE FROM training_attendance WHERE training_id = ?", (target_training_id,))
            for ex in exercises:
                cursor.execute("INSERT INTO exercises (training_id, name, description, duration, repetitions, space, objectives, rules, variants, image_path, category) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (target_training_id, *ex))
            for player_id, status in attendance:
                cursor.execute("INSERT INTO training_attendance (training_id, player_id, status) VALUES (?, ?, ?)", (target_training_id, player_id, status))
            cursor.execute("UPDATE trainings SET material = ? WHERE id = ?", (material, target_training_id))
            self.conn.commit()
            return True
        except Exception as e: print(f"Error al cargar plantilla: {e}"); self.conn.rollback(); return False

    # --- Métodos de Historial y Lesiones ---
    def get_career_history_for_player(self, player_id):
        return self.conn.execute("SELECT * FROM career_history WHERE player_id = ? ORDER BY season DESC", (player_id,)).fetchall()
    def insert_career_entry(self, data):
        self.conn.execute("INSERT INTO career_history (player_id, season, team_name, matches_played, goals_scored, assists, yellow_cards, red_cards, saves, goals_conceded) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", tuple(data.values()))
        self.conn.commit()
    def update_career_entry(self, entry_id, data):
        self.conn.execute("UPDATE career_history SET season=?, team_name=?, matches_played=?, goals_scored=?, assists=?, yellow_cards=?, red_cards=?, saves=?, goals_conceded=? WHERE id = ?", (*data.values(), entry_id))
        self.conn.commit()
    def delete_career_entry(self, entry_id):
        self.conn.execute("DELETE FROM career_history WHERE id = ?", (entry_id,))
        self.conn.commit()
    def get_injuries_for_player(self, player_id):
        return self.conn.execute("SELECT * FROM injuries WHERE player_id = ? ORDER BY injury_date DESC", (player_id,)).fetchall()
    def insert_injury(self, data):
        self.conn.execute("INSERT INTO injuries (player_id, injury_date, injury_type, recovery_period, notes) VALUES (?, ?, ?, ?, ?)", tuple(data.values()))
        self.conn.commit()
    def update_injury(self, injury_id, data):
        self.conn.execute("UPDATE injuries SET injury_date=?, injury_type=?, recovery_period=?, notes=? WHERE id = ?", (*data.values(), injury_id))
        self.conn.commit()
    def delete_injury(self, injury_id):
        self.conn.execute("DELETE FROM injuries WHERE id = ?", (injury_id,))
        self.conn.commit()