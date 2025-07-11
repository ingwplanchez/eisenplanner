# eisenplanner/app.py

from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    is_urgent = db.Column(db.Boolean, default=False, nullable=False)
    is_important = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return (f'<Task {self.id}: {self.content[:20]}... - C:{self.completed}, '
                f'Urgent:{self.is_urgent}, Important:{self.is_important}>')

# NOTA: Asegúrate de que db.create_all() esté COMENTADO aquí, a menos que vuelvas a borrar todo.
# with app.app_context():
#     db.create_all()

# --- Rutas de la Aplicación ---

@app.route('/')
def index():
    # Obtener parámetros de filtro de la URL
    # request.args.get() recupera el valor de un parámetro de query (ej. ?urgent=true)
    # Si el parámetro no está presente, devuelve None.
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

    # Ordenar y ejecutar la consulta
    tasks = query.order_by(Task.id.asc()).all()
    return render_template('index.html', tasks=tasks)

@app.route('/add', methods=['POST'])
def add_task():
    if request.method == 'POST':
        task_content = request.form['content'].strip()
        is_urgent = 'is_urgent' in request.form
        is_important = 'is_important' in request.form

        if task_content:
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
    task_to_delete = Task.query.get_or_404(task_id)
    try:
        db.session.delete(task_to_delete)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error al eliminar tarea: {e}")
    return redirect(url_for('index'))

@app.route('/complete/<int:task_id>')
def complete_task(task_id):
    task_to_complete = Task.query.get_or_404(task_id)
    try:
        task_to_complete.completed = not task_to_complete.completed
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error al completar/descompletar tarea: {e}")
    return redirect(url_for('index'))

@app.route('/edit/<int:task_id>')
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    return render_template('edit.html', task=task)

@app.route('/update/<int:task_id>', methods=['POST'])
def update_task(task_id):
    task_to_update = Task.query.get_or_404(task_id)
    if request.method == 'POST':
        updated_content = request.form['content'].strip()
        updated_is_urgent = 'is_urgent' in request.form
        updated_is_important = 'is_important' in request.form

        if updated_content:
            try:
                task_to_update.content = updated_content
                task_to_update.is_urgent = updated_is_urgent
                task_to_update.is_important = updated_is_important
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Error al actualizar tarea: {e}")
    return redirect(url_for('index'))

# --- Ejecutar la Aplicación ---
if __name__ == '__main__':
    app.run(debug=True)