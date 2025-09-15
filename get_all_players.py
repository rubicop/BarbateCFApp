import sqlite3
import os
import json

class Database:
    def __init__(self):
        if not os.path.exists("data"): os.makedirs("data")
        self.conn = sqlite3.connect('data/barbate_cf.db')
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY, name TEXT NOT NULL, position TEXT NOT NULL, number INTEGER, 
                date_of_birth TEXT, nationality TEXT, dominant_foot TEXT, height_cm INTEGER, 
                weight_kg INTEGER, photo_path TEXT, observations TEXT, shirt_name TEXT
            )''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS career_history (
                id INTEGER PRIMARY KEY, player_id INTEGER NOT NULL, season TEXT, team_name TEXT, 
                matches_played INTEGER DEFAULT 0, goals_scored INTEGER DEFAULT 0, assists INTEGER DEFAULT 0, 
                yellow_cards INTEGER DEFAULT 0, red_cards INTEGER DEFAULT 0, saves INTEGER DEFAULT 0, 
                goals_conceded INTEGER DEFAULT 0,
                FOREIGN KEY (player_id) REFERENCES players (id) ON DELETE CASCADE
            )''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS injuries (
                id INTEGER PRIMARY KEY, player_id INTEGER NOT NULL, injury_date TEXT,
                injury_type TEXT, recovery_period TEXT, notes TEXT,
                FOREIGN KEY (player_id) REFERENCES players (id) ON DELETE CASCADE
            )''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trainings (
                id INTEGER PRIMARY KEY, date TEXT NOT NULL, mesocycle TEXT, session_number INTEGER, 
                coach TEXT, assistant_coach TEXT, material TEXT
            )''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exercises (
                id INTEGER PRIMARY KEY, training_id INTEGER, name TEXT, description TEXT, 
                duration INTEGER, repetitions TEXT, space TEXT, objectives TEXT, 
                rules TEXT, variants TEXT, image_path TEXT,
                FOREIGN KEY (training_id) REFERENCES trainings (id) ON DELETE CASCADE
            )''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS training_attendance (
                training_id INTEGER NOT NULL, player_id INTEGER NOT NULL, status TEXT NOT NULL,
                PRIMARY KEY (training_id, player_id),
                FOREIGN KEY (training_id) REFERENCES trainings (id) ON DELETE CASCADE,
                FOREIGN KEY (player_id) REFERENCES players (id) ON DELETE CASCADE
            )''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS field_layouts (
                id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, layout_data TEXT NOT NULL
            )''')
        self.conn.commit()

    # --- Métodos para Diseños ---
    def save_layout(self, name, layout_data): cursor = self.conn.cursor(); cursor.execute("INSERT INTO field_layouts (name, layout_data) VALUES (?, ?)", (name, layout_data)); self.conn.commit()
    def update_layout_name(self, layout_id, new_name): cursor = self.conn.cursor(); cursor.execute("UPDATE field_layouts SET name = ? WHERE id = ?", (new_name, layout_id)); self.conn.commit()
    def delete_layout(self, layout_id): cursor = self.conn.cursor(); cursor.execute("DELETE FROM field_layouts WHERE id = ?", (layout_id,)); self.conn.commit()
    def get_all_layouts(self): cursor = self.conn.cursor(); cursor.execute("SELECT id, name FROM field_layouts ORDER BY name ASC"); return cursor.fetchall()
    def get_layout_data_by_id(self, layout_id): cursor = self.conn.cursor(); cursor.execute("SELECT layout_data FROM field_layouts WHERE id = ?", (layout_id,)); result = cursor.fetchone(); return result[0] if result else None

    # --- Métodos para Ejercicios ---
    def get_exercises_by_ids(self, exercise_ids):
        if not exercise_ids: return []
        cursor = self.conn.cursor(); placeholders = ', '.join('?' for _ in exercise_ids)
        query = f"SELECT * FROM exercises WHERE id IN ({placeholders})"; cursor.execute(query, exercise_ids); return cursor.fetchall()
    def get_exercises_by_training(self, training_id): cursor = self.conn.cursor(); cursor.execute("SELECT * FROM exercises WHERE training_id = ?", (training_id,)); return cursor.fetchall()

    # --- Métodos para Jugadores ---
    def get_all_players(self): 
        cursor = self.conn.cursor(); cursor.execute("SELECT * FROM players ORDER BY name ASC"); return cursor.fetchall()
    
    def get_player_by_id(self, player_id): 
        cursor = self.conn.cursor(); cursor.execute("SELECT * FROM players WHERE id = ?", (player_id,)); return cursor.fetchone()

    # --- Otros Métodos ---
    def get_all_trainings_for_dropdown(self): cursor = self.conn.cursor(); cursor.execute("SELECT id, date, mesocycle, session_number FROM trainings ORDER BY date DESC"); return cursor.fetchall()
    def copy_training_content(self, source_id, dest_id):
        cursor = self.conn.cursor()
        try:
            cursor.execute("DELETE FROM exercises WHERE training_id = ?", (dest_id,)); cursor.execute("DELETE FROM training_attendance WHERE training_id = ?", (dest_id,))
            cursor.execute("INSERT INTO exercises (training_id, name, description, duration, repetitions, space, objectives, rules, variants, image_path) SELECT ?, name, description, duration, repetitions, space, objectives, rules, variants, image_path FROM exercises WHERE training_id = ?", (dest_id, source_id))
            cursor.execute("INSERT INTO training_attendance (training_id, player_id, status) SELECT ?, player_id, status FROM training_attendance WHERE training_id = ?", (dest_id, source_id))
            self.conn.commit(); return True
        except Exception as e:
            self.conn.rollback(); print(f"Error al copiar plantilla: {e}"); return False
    def insert_player(self, name, pos, num, dob, nat, foot, h, w, photo, obs, s_name): cursor = self.conn.cursor(); cursor.execute("INSERT INTO players (name, position, number, date_of_birth, nationality, dominant_foot, height_cm, weight_kg, photo_path, observations, shirt_name) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (name, pos, num, dob, nat, foot, h, w, photo, obs, s_name)); self.conn.commit(); return cursor.lastrowid
    def update_player(self, pid, name, pos, num, dob, nat, foot, h, w, photo, obs, s_name): cursor = self.conn.cursor(); cursor.execute("UPDATE players SET name = ?, position = ?, number = ?, date_of_birth = ?, nationality = ?, dominant_foot = ?, height_cm = ?, weight_kg = ?, photo_path = ?, observations = ?, shirt_name = ? WHERE id = ?", (name, pos, num, dob, nat, foot, h, w, photo, obs, s_name, pid)); self.conn.commit()
    def delete_player(self, player_id): cursor = self.conn.cursor(); cursor.execute("DELETE FROM players WHERE id = ?", (player_id,)); self.conn.commit()
    def get_career_history_for_player(self, player_id): cursor = self.conn.cursor(); cursor.execute("SELECT * FROM career_history WHERE player_id = ? ORDER BY season DESC", (player_id,)); return cursor.fetchall()
    def insert_career_entry(self, data): cursor = self.conn.cursor(); cursor.execute("INSERT INTO career_history (player_id, season, team_name, matches_played, goals_scored, assists, yellow_cards, red_cards, saves, goals_conceded) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", tuple(data.values())); self.conn.commit()
    def update_career_entry(self, entry_id, data): cursor = self.conn.cursor(); cursor.execute("UPDATE career_history SET season=?, team_name=?, matches_played=?, goals_scored=?, assists=?, yellow_cards=?, red_cards=?, saves=?, goals_conceded=? WHERE id = ?", (*data.values(), entry_id)); self.conn.commit()
    def delete_career_entry(self, entry_id): cursor = self.conn.cursor(); cursor.execute("DELETE FROM career_history WHERE id = ?", (entry_id,)); self.conn.commit()
    def get_injuries_for_player(self, player_id): cursor = self.conn.cursor(); cursor.execute("SELECT * FROM injuries WHERE player_id = ? ORDER BY injury_date DESC", (player_id,)); return cursor.fetchall()
    def insert_injury(self, data): cursor = self.conn.cursor(); cursor.execute("INSERT INTO injuries (player_id, injury_date, injury_type, recovery_period, notes) VALUES (?, ?, ?, ?, ?)", tuple(data.values())); self.conn.commit()
    def update_injury(self, injury_id, data): cursor = self.conn.cursor(); cursor.execute("UPDATE injuries SET injury_date=?, injury_type=?, recovery_period=?, notes=? WHERE id = ?", (*data.values(), injury_id)); self.conn.commit()
    def delete_injury(self, injury_id): cursor = self.conn.cursor(); cursor.execute("DELETE FROM injuries WHERE id = ?", (injury_id,)); self.conn.commit()
    def insert_training(self, date, mesocycle, session, coach, assistant, material): cursor = self.conn.cursor(); cursor.execute("INSERT INTO trainings (date, mesocycle, session_number, coach, assistant_coach, material) VALUES (?, ?, ?, ?, ?, ?)", (date, mesocycle, session, coach, assistant, material)); self.conn.commit()
    def get_all_trainings(self): cursor = self.conn.cursor(); cursor.execute("SELECT * FROM trainings ORDER BY date DESC"); return cursor.fetchall()
    def update_training(self, tid, date, mesocycle, session, coach, assistant, material): cursor = self.conn.cursor(); cursor.execute("UPDATE trainings SET date = ?, mesocycle = ?, session_number = ?, coach = ?, assistant_coach = ?, material = ? WHERE id = ?", (date, mesocycle, session, coach, assistant, material, tid)); self.conn.commit()
    def delete_training(self, training_id): cursor = self.conn.cursor(); cursor.execute("DELETE FROM trainings WHERE id = ?", (training_id,)); self.conn.commit()
    def insert_exercise(self, tid, name, desc, dur, rep, space, obj, rules, var, img): cursor = self.conn.cursor(); cursor.execute("INSERT INTO exercises (training_id, name, description, duration, repetitions, space, objectives, rules, variants, image_path) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (tid, name, desc, dur, rep, space, obj, rules, var, img)); self.conn.commit(); return cursor.lastrowid
    def update_exercise(self, eid, tid, name, desc, dur, rep, space, obj, rules, var, img): cursor = self.conn.cursor(); cursor.execute("UPDATE exercises SET training_id=?, name=?, description=?, duration=?, repetitions=?, space=?, objectives=?, rules=?, variants=?, image_path=? WHERE id=?", (tid, name, desc, dur, rep, space, obj, rules, var, img, eid)); self.conn.commit()
    def delete_exercise(self, exercise_id): cursor = self.conn.cursor(); cursor.execute("DELETE FROM exercises WHERE id = ?", (exercise_id,)); self.conn.commit()
    def get_attendance_for_training(self, training_id): cursor = self.conn.cursor(); cursor.execute("SELECT p.id, p.name, p.position, ta.status, p.photo_path FROM players p JOIN training_attendance ta ON p.id = ta.player_id WHERE ta.training_id = ?", (training_id,)); return cursor.fetchall()
    def get_unassigned_players(self, training_id): cursor = self.conn.cursor(); cursor.execute("SELECT * FROM players WHERE id NOT IN (SELECT player_id FROM training_attendance WHERE training_id = ?)", (training_id,)); return cursor.fetchall()
    def set_player_attendance(self, training_id, player_id, status): cursor = self.conn.cursor(); cursor.execute("INSERT INTO training_attendance (training_id, player_id, status) VALUES (?, ?, ?) ON CONFLICT(training_id, player_id) DO UPDATE SET status = excluded.status", (training_id, player_id, status)); self.conn.commit()
    def remove_player_from_training(self, training_id, player_id): cursor = self.conn.cursor(); cursor.execute("DELETE FROM training_attendance WHERE training_id = ? AND player_id = ?", (training_id, player_id)); self.conn.commit()