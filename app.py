# eisenplanner/app.py

from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import datetime

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
    due_date = db.Column(db.DateTime, nullable=True) # AQUI

    def __repr__(self):
        return (f'<Task {self.id}: {self.content[:20]}... - C:{self.completed}, '
                f'Urgent:{self.is_urgent}, Important:{self.is_important}, '
                f'Due:{self.due_date.strftime("%Y-%m-%d") if self.due_date else "None"}>')

# NOTA: Asegúrate de que db.create_all() esté COMENTADO aquí.
# with app.app_context():
    # db.create_all()


@app.route('/')
def index():
    filter_urgent = request.args.get('urgent')
    filter_important = request.args.get('important')

    query = Task.query

    if filter_urgent == 'true':
        query = query.filter_by(is_urgent=True)
    elif filter_urgent == 'false':
        query = query.filter_by(is_urgent=False)

    if filter_important == 'true':
        query = query.filter_by(is_important=True)
    elif filter_important == 'false':
        query = query.filter_by(is_important=False)

    # Opcional: Ordenar por due_date (primero las más cercanas, luego por ID)
    query = query.order_by(Task.due_date.asc(), Task.id.asc())

    all_filtered_tasks = query.all()

    quadrants = {
        'do': {'title': 'Cuadrante 1: Hacer (Urgente e Importante)', 'tasks': [], 'class': 'quadrant-1'},
        'schedule': {'title': 'Cuadrante 2: Agendar (Importante, No Urgente)', 'tasks': [], 'class': 'quadrant-2'},
        'delegate': {'title': 'Cuadrante 3: Delegar (Urgente, No Importante)', 'tasks': [], 'class': 'quadrant-3'},
        'eliminate': {'title': 'Cuadrante 4: Eliminar (No Urgente, No Importante)', 'tasks': [], 'class': 'quadrant-4'},
    }

    for task in all_filtered_tasks:
        if task.is_urgent and task.is_important:
            quadrants['do']['tasks'].append(task)
        elif not task.is_urgent and task.is_important:
            quadrants['schedule']['tasks'].append(task)
        elif task.is_urgent and not task.is_important:
            quadrants['delegate']['tasks'].append(task)
        elif not task.is_urgent and not task.is_important:
            quadrants['eliminate']['tasks'].append(task)

    if filter_urgent is None and filter_important is None:
        return render_template('index.html', quadrants=quadrants, show_all_quadrants=True)
    else:
        return render_template('index.html', tasks=all_filtered_tasks, show_all_quadrants=False)

@app.route('/add', methods=['POST'])
def add_task():
    if request.method == 'POST':
        task_content = request.form['content'].strip()
        is_urgent = 'is_urgent' in request.form
        is_important = 'is_important' in request.form
        # --- NUEVO: Obtener la fecha límite ---
        due_date_str = request.form.get('due_date')
        due_date = None
        if due_date_str: # Solo intenta convertir si la cadena no está vacía
            try:
                # Convertir la cadena de fecha (YYYY-MM-DD) a un objeto datetime
                due_date = datetime.datetime.strptime(due_date_str, '%Y-%m-%d')
            except ValueError:
                # Manejar error si el formato de fecha es incorrecto (opcional)
                print(f"Advertencia: Fecha límite '{due_date_str}' en formato incorrecto.")
        # --------------------------------------

        if task_content:
            new_task = Task(content=task_content, is_urgent=is_urgent, is_important=is_important, due_date=due_date)
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
        # --- NUEVO: Obtener y procesar la fecha límite para la actualización ---
        updated_due_date_str = request.form.get('due_date')
        updated_due_date = None
        if updated_due_date_str:
            try:
                updated_due_date = datetime.datetime.strptime(updated_due_date_str, '%Y-%m-%d')
            except ValueError:
                print(f"Advertencia: Fecha límite actualizada '{updated_due_date_str}' en formato incorrecto.")
        # ---------------------------------------------------------------------

        if updated_content:
            try:
                task_to_update.content = updated_content
                task_to_update.is_urgent = updated_is_urgent
                task_to_update.is_important = updated_is_important
                task_to_update.due_date = updated_due_date # Asigna la fecha límite
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Error al actualizar tarea: {e}")
    return redirect(url_for('index'))

# --- Ejecutar la Aplicación ---
if __name__ == '__main__':
    app.run(debug=True)