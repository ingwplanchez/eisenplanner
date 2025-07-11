# eisenplaner/app.py

from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Definición del Modelo de la Base de Datos (Tabla de Tareas) ---
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    # --- NUEVAS COLUMNAS ajustadas para la Matriz de Eisenhower ---
    # is_urgent: True si es urgente, False si no lo es.
    is_urgent = db.Column(db.Boolean, default=False, nullable=False)
    # is_important: True si es importante, False si no lo es.
    is_important = db.Column(db.Boolean, default=False, nullable=False)
    # -------------------------------------------------------------

    def __repr__(self):
        return (f'<Task {self.id}: {self.content[:20]}... - C:{self.completed}, '
                f'Urgent:{self.is_urgent}, Important:{self.is_important}>')


# --- PASO CRUCIAL: Recrear la base de datos ---
# Necesitas hacer esto cada vez que cambies el esquema de la tabla (añadir/quitar/modificar columnas).
# 1. Detén el servidor Flask (Ctrl+C).
# 2. ELIMINA el archivo 'todo.db' de tu proyecto.
# 3. DESCOMENTA las siguientes líneas:
# with app.app_context():
    # db.create_all()
# 4. Ejecuta 'python app.py' UNA SOLA VEZ.
# 5. VUELVE A COMENTAR las líneas 'db.create_all()'.
# Esto asegura que tu base de datos tenga las nuevas columnas 'is_urgent' y 'is_important'.


# ... (el resto de tu código de app.py permanece igual por ahora) ...

# --- Ejecutar la Aplicación ---
if __name__ == '__main__':
    app.run(debug=True)