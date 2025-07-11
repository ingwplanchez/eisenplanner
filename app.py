# eisenplanner/app.py

from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# --- Configuración de la Base de Datos ---
# Le decimos a Flask dónde se guardará la base de datos SQLite.
# '///todo.db' significa un archivo llamado 'todo.db' en el directorio raíz del proyecto.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Para silenciar una advertencia de SQLAlchemy

db = SQLAlchemy(app) # Creamos una instancia de SQLAlchemy, pasándole nuestra aplicación Flask

# --- Definición del Modelo de la Base de Datos (Tabla de Tareas) ---
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True) # Columna ID: entero, clave primaria, autoincremental
    content = db.Column(db.String(200), nullable=False) # Columna content: cadena de hasta 200 caracteres, no puede ser nula
    completed = db.Column(db.Boolean, default=False) # Columna completed: booleano, por defecto False
    # --- NUEVAS COLUMNAS para la Matriz de Eisenhower ---
    is_urgent = db.Column(db.Boolean, default=False, nullable=False) # True si es urgente, False si no
    is_important = db.Column(db.Boolean, default=False, nullable=False) # True si es importante, False si no
    # -----------------------------------------------------

    def __repr__(self):
        # Este método define cómo se representa un objeto Task cuando lo imprimes (útil para depuración)
        return (f'<Task {self.id}: {self.content[:20]}... - C:{self.completed}, '
                f'Urgent:{self.is_urgent}, Important:{self.is_important}>')

# --- CREAR LA BASE DE DATOS Y LAS TABLAS (solo la primera vez o al cambiar esquema) ---
# RECUERDA:
# 1. ELIMINA el archivo 'todo.db' de tu proyecto si has modificado el modelo Task.
# 2. DESCOMENTA las siguientes líneas:
# with app.app_context():
#     db.create_all()
# 3. Ejecuta 'python app.py' UNA SOLA VEZ.
# 4. VUELVE A COMENTAR estas líneas después de la ejecución exitosa.


# --- Rutas de la Aplicación ---

@app.route('/')
def index():
    # Obtener parámetros de filtro de la URL
    filter_urgent = request.args.get('urgent') # Puede ser 'true', 'false', o None
    filter_important = request.args.get('important') # Puede ser 'true', 'false', o None

    # Iniciar la consulta de la base de datos
    query = Task.query

    # Aplicar filtros basados en los parámetros de la URL
    if filter_urgent == 'true':
        query = query.filter_by(is_urgent=True)
    elif filter_urgent == 'false':
        query = query.filter_by(is_urgent=False)

    if filter_important == 'true':
        query = query.filter_by(is_important=True)
    elif filter_important == 'false':
        query = query.filter_by(is_important=False)

    all_filtered_tasks = query.order_by(Task.id.asc()).all()

    # --- Lógica de Agrupación para la visualización de Cuadrantes ---
    # Esto es nuevo: Creamos un diccionario para agrupar las tareas.
    quadrants = {
        'do': {'title': 'Cuadrante 1: Hacer (Urgente e Importante)', 'tasks': [], 'class': 'quadrant-1'},
        'schedule': {'title': 'Cuadrante 2: Agendar (Importante, No Urgente)', 'tasks': [], 'class': 'quadrant-2'},
        'delegate': {'title': 'Cuadrante 3: Delegar (Urgente, No Importante)', 'tasks': [], 'class': 'quadrant-3'},
        'eliminate': {'title': 'Cuadrante 4: Eliminar (No Urgente, No Importante)', 'tasks': [], 'class': 'quadrant-4'},
        # 'unclassified': {'title': 'Sin Clasificar', 'tasks': [], 'class': 'quadrant-4'} # Opcional: para tareas con datos inconsistentes
    }

    # Asigna cada tarea a su cuadrante correspondiente
    for task in all_filtered_tasks:
        if task.is_urgent and task.is_important:
            quadrants['do']['tasks'].append(task)
        elif not task.is_urgent and task.is_important:
            quadrants['schedule']['tasks'].append(task)
        elif task.is_urgent and not task.is_important:
            quadrants['delegate']['tasks'].append(task)
        elif not task.is_urgent and not task.is_important:
            quadrants['eliminate']['tasks'].append(task)
        # else: # Manejo de tareas 'sin clasificar' si fuera necesario
        #     quadrants['unclassified']['tasks'].append(task)

    # Si no hay filtros aplicados, devolvemos los cuadrantes agrupados.
    # Si hay filtros (el usuario ha seleccionado un cuadrante específico),
    # solo mostramos las tareas de ese cuadrante en una lista plana sin títulos de cuadrante.
    if filter_urgent is None and filter_important is None:
        # Pasa el diccionario de cuadrantes a la plantilla
        return render_template('index.html', quadrants=quadrants, show_all_quadrants=True)
    else:
        # Si hay filtros, simplemente pasa las tareas filtradas como antes
        return render_template('index.html', tasks=all_filtered_tasks, show_all_quadrants=False)

@app.route('/add', methods=['POST'])
def add_task():
    if request.method == 'POST':
        task_content = request.form['content'].strip()
        # Obtener valores de los checkboxes: 'is_urgent' y 'is_important' estarán en request.form si están marcados
        is_urgent = 'is_urgent' in request.form
        is_important = 'is_important' in request.form

        if task_content:
            # Creamos un nuevo objeto Task con los nuevos valores
            new_task = Task(content=task_content, is_urgent=is_urgent, is_important=is_important)
            try:
                db.session.add(new_task) # Añadimos el nuevo objeto a la sesión de la base de datos
                db.session.commit()      # Guardamos los cambios en la base de datos
            except Exception as e:
                db.session.rollback() # Si hay un error, revertimos la transacción
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
    task_to_update = Task.query.get_or_404(task_id) # Obtenemos la tarea a actualizar
    if request.method == 'POST':
        updated_content = request.form['content'].strip()
        # Obtener valores de los checkboxes para la actualización
        updated_is_urgent = 'is_urgent' in request.form
        updated_is_important = 'is_important' in request.form

        if updated_content:
            try:
                task_to_update.content = updated_content # Actualizamos el contenido
                task_to_update.is_urgent = updated_is_urgent # Actualiza el estado de urgencia
                task_to_update.is_important = updated_is_important # Actualiza el estado de importancia
                db.session.commit()                      # Guardamos el cambio
            except Exception as e:
                db.session.rollback()
                print(f"Error al actualizar tarea: {e}")
    return redirect(url_for('index'))

# --- Ejecutar la Aplicación ---
if __name__ == '__main__':
    app.run(debug=True)