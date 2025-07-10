# flask_todo_list/app.py

from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy # Importamos SQLAlchemy

app = Flask(__name__)

# --- Configuración de la Base de Datos ---
# Le decimos a Flask dónde se guardará la base de datos SQLite.
# '///todo.db' significa un archivo llamado 'todo.db' en el directorio raíz del proyecto.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Para silenciar una advertencia de SQLAlchemy

db = SQLAlchemy(app) # Creamos una instancia de SQLAlchemy, pasándole nuestra aplicación Flask

# --- Definición del Modelo de la Base de Datos (Tabla de Tareas) ---
# Un modelo es una clase Python que representa una tabla en nuestra base de datos.
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True) # Columna ID: entero, clave primaria, autoincremental
    content = db.Column(db.String(200), nullable=False) # Columna content: cadena de hasta 200 caracteres, no puede ser nula
    completed = db.Column(db.Boolean, default=False) # Columna completed: booleano, por defecto False
    # Puedes añadir más columnas aquí, por ejemplo, fecha_creacion, etc.

    def __repr__(self):
        # Este método define cómo se representa un objeto Task cuando lo imprimes (útil para depuración)
        return f'<Task {self.id}: {self.content} - Completed: {self.completed}>'

# --- CREAR LA BASE DE DATOS Y LAS TABLAS (solo la primera vez) ---
# Descomenta y ejecuta esto UNA VEZ para crear el archivo todo.db y la tabla 'task'
# Después de la primera ejecución exitosa, vuelve a comentarlo o bórralo.
# with app.app_context():
    # db.create_all()


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
    if request.method == 'POST':
        task_content = request.form['content'].strip()
        if task_content:
            # Creamos un nuevo objeto Task
            new_task = Task(content=task_content)
            try:
                db.session.add(new_task) # Añadimos el nuevo objeto a la sesión de la base de datos
                db.session.commit()      # Guardamos los cambios en la base de datos (hacemos el 'commit')
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
        if updated_content:
            try:
                task_to_update.content = updated_content # Actualizamos el contenido
                db.session.commit()                      # Guardamos el cambio
            except Exception as e:
                db.session.rollback()
                print(f"Error al actualizar tarea: {e}")
    return redirect(url_for('index'))

# --- Ejecutar la Aplicación ---
if __name__ == '__main__':
    app.run(debug=True)