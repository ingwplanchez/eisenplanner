# eisenplanner/app.py

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

# NOTA IMPORTANTE: Necesitas RECREAR tu base de datos para que incluya las nuevas columnas.
# PASO A SEGUIR:
# 1. COMENTA las siguientes líneas 'db.create_all()' si no lo estaban.
# 2. ELIMINA el archivo 'todo.db' de tu proyecto.
# 3. DESCOMENTA las siguientes líneas:
# with app.app_context():
    # db.create_all()
# 4. Ejecuta 'python app.py' UNA SOLA VEZ.
# 5. VUELVE A COMENTAR las líneas 'db.create_all()'.
# Esto es necesario porque SQLAlchemy no puede añadir columnas directamente a una tabla existente
# de esta manera simple. En proyectos más grandes, usarías "migrations" (migraciones) con herramientas
# como Flask-Migrate o Alembic, pero para este nivel, recrear la DB es lo más directo.

# --- Rutas de la Aplicación ---

@app.route('/')
def index():
    # Ahora obtenemos todas las tareas de la base de datos
    # .all() recupera todos los objetos Task de la tabla
    # Ahora ordena por ID ascendente para que la tarea más antigua (ID más bajo) aparezca primero.
    tasks = Task.query.order_by(Task.id.asc()).all()
    return render_template('index.html', tasks=tasks)

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

@app.route('/delete/<int:task_id>')
def delete_task(task_id):
    # Buscamos la tarea por su ID en la base de datos. .first_or_404() devuelve 404 si no la encuentra.
    task_to_delete = Task.query.get_or_404(task_id)
    try:
        db.session.delete(task_to_delete) # Marcamos el objeto para ser eliminado
        db.session.commit()               # Guardamos los cambios
    except Exception as e:
        db.session.rollback()
        print(f"Error al eliminar tarea: {e}")
    return redirect(url_for('index'))

@app.route('/complete/<int:task_id>')
def complete_task(task_id):
    task_to_complete = Task.query.get_or_404(task_id)
    try:
        task_to_complete.completed = not task_to_complete.completed # Alternamos el estado
        db.session.commit() # Guardamos el cambio
    except Exception as e:
        db.session.rollback()
        print(f"Error al completar/descompletar tarea: {e}")
    return redirect(url_for('index'))

@app.route('/edit/<int:task_id>')
def edit_task(task_id):
    task = Task.query.get_or_404(task_id) # Obtenemos la tarea para el formulario de edición
    return render_template('edit.html', task=task)

@app.route('/update/<int:task_id>', methods=['POST'])
def update_task(task_id):
    task_to_update = Task.query.get_or_404(task_id)
    if request.method == 'POST':
        updated_content = request.form['content'].strip()
        # --- Obtener valores de los checkboxes para la actualización ---
        # Similar a add_task, verificamos si están en request.form
        updated_is_urgent = 'is_urgent' in request.form
        updated_is_important = 'is_important' in request.form
        # -------------------------------------------------------------

        if updated_content:
            try:
                task_to_update.content = updated_content
                task_to_update.is_urgent = updated_is_urgent # Actualiza el estado de urgencia
                task_to_update.is_important = updated_is_important # Actualiza el estado de importancia
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Error al actualizar tarea: {e}")
    return redirect(url_for('index'))

# --- Ejecutar la Aplicación ---
if __name__ == '__main__':
    app.run(debug=True)