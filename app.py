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

@app.route('/add', methods=['POST'])
def add_task():
    # global tasks # Ya no es necesario si solo interactúas con la DB
    # global next_task_id # Ya no es necesario, SQLAlchemy maneja IDs

    if request.method == 'POST':
        task_content = request.form['content'].strip()
        # --- Obtener valores de los checkboxes ---
        # Si el checkbox está marcado, request.form.get() devolverá 'on'. Si no, None.
        # Lo convertimos a un booleano (True si 'on', False si None o cualquier otra cosa).
        is_urgent = 'is_urgent' in request.form # Más directo para checkboxes: si está en request.form, está marcado
        is_important = 'is_important' in request.form
        # ----------------------------------------

        if task_content:
            # Creamos un nuevo objeto Task con los nuevos valores
            new_task = Task(content=task_content, is_urgent=is_urgent, is_important=is_important)
            try:
                db.session.add(new_task)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Error al añadir tarea: {e}")

    return redirect(url_for('index'))


# --- Ejecutar la Aplicación ---
if __name__ == '__main__':
    app.run(debug=True)