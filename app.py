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
    due_date = db.Column(db.DateTime, nullable=True) # Mantener como DateTime si así lo tenías funcionando

    def __repr__(self):
        return (f'<Task {self.id}: {self.content[:20]}... - C:{self.completed}, '
                f'Urgent:{self.is_urgent}, Important:{self.is_important}, '
                f'Due:{self.due_date.strftime("%Y-%m-%d") if self.due_date else "N/A"}>')

# --- IMPORTANT: DATABASE CREATION INSTRUCTIONS ---
# If you make changes to the Task model (like adding/removing columns or changing types),
# you MUST recreate your database for the changes to take effect.
# 1. STOP your Flask server (Ctrl+C).
# 2. DELETE the 'todo.db' file from your project directory (or 'instance/' if you have one).
# 3. UNCOMMENT the following two lines:
# with app.app_context():
#     db.create_all()
# 4. Run your app once (`python app.py` or `flask run`). The database will be created.
# 5. ONCE IT STARTS SUCCESSFULLY, COMMENT OUT the two lines above again.
# This prevents the database from being recreated every time you run the app.
# --- END DATABASE INSTRUCTIONS ---

@app.route('/')
def index():
    # Capture the current view mode from URL, default to 'list'
    view_mode = request.args.get('view_mode', 'list')

    # --- INICIO DE CAMBIO ---
    # Obtener los filtros y convertirlos a None si son cadenas vacías
    filter_urgent_raw = request.args.get('urgent')
    filter_important_raw = request.args.get('important')

    filter_urgent = filter_urgent_raw if filter_urgent_raw != '' else None
    filter_important = filter_important_raw if filter_important_raw != '' else None
    # --- FIN DE CAMBIO ---

    base_query = Task.query

    # Apply filters to the base query
    # Note: These filters apply to the set of tasks that will be displayed in ALL views.
    if filter_urgent == 'true':
        base_query = base_query.filter_by(is_urgent=True)
    elif filter_urgent == 'false':
        base_query = base_query.filter_by(is_urgent=False)

    if filter_important == 'true':
        base_query = base_query.filter_by(is_important=True)
    elif filter_important == 'false':
        base_query = base_query.filter_by(is_important=False)

    # Order by completion first (incomplete tasks before completed), then due_date, then ID
    # This list will be used for the simple 'list' view when filters are active,
    # and also to populate the quadrants.
    all_tasks_for_display = base_query.order_by(
        Task.completed.asc(), Task.due_date.asc(), Task.id.asc()
    ).all()

    # Determine if "All" tasks are being shown (no specific filters applied)
    # This variable helps 'index.html' decide between showing all quadrant sections
    # or just a flat list of filtered tasks when in 'list' mode.
    # --- show_all_quadrants ahora funcionará correctamente con los filtros convertidos a None ---
    show_all_quadrants = (filter_urgent is None and filter_important is None)

    # Prepare quadrants data. This structure is always sent,
    # even if a specific filter is applied (the tasks within will just be filtered).
    quadrants = {
        'do': {'title': 'Cuadrante 1: Hacer (Hoy o Mañana)', 'tasks': [], 'class': 'quadrant-1'},
        'schedule': {'title': 'Cuadrante 2: Agendar (Próximas Semanas)', 'tasks': [], 'class': 'quadrant-2'},
        'delegate': {'title': 'Cuadrante 3: Delegar (Hacer Ahora)', 'tasks': [], 'class': 'quadrant-3'},
        'eliminate': {'title': 'Cuadrante 4: Eliminar (Posponer)', 'tasks': [], 'class': 'quadrant-4'},
    }

    # Populate quadrants with the *filtered* tasks for accurate display in matrix/list views
    for task in all_tasks_for_display:
        if task.is_urgent and task.is_important:
            quadrants['do']['tasks'].append(task)
        elif not task.is_urgent and task.is_important:
            quadrants['schedule']['tasks'].append(task)
        elif task.is_urgent and not task.is_important:
            quadrants['delegate']['tasks'].append(task)
        elif not task.is_urgent and not task.is_important:
            quadrants['eliminate']['tasks'].append(task)
    
    # Calculate counts for display (based on filtered tasks in quadrants)
    quadrant_counts = {key: len(data['tasks']) for key, data in quadrants.items()}

    return render_template(
        'index.html',
        tasks=all_tasks_for_display, # The filtered list of tasks for the simple list view
        quadrants=quadrants, # Quadrant data (contains filtered tasks for each quadrant)
        quadrant_counts=quadrant_counts, # Counts for each quadrant
        show_all_quadrants=show_all_quadrants, # True if "Todas" is selected, False if specific filters
        view_mode=view_mode, # The selected view mode ('list' or 'matrix')
        # Pass current filter states to the template for button active states and form hidden fields
        current_urgent_filter=filter_urgent, # Ahora será None o 'true'/'false'
        current_important_filter=filter_important # Ahora será None o 'true'/'false'
    )

@app.route('/add', methods=['POST'])
def add_task():
    if request.method == 'POST':
        task_content = request.form['content'].strip()
        is_urgent = 'is_urgent' in request.form
        is_important = 'is_important' in request.form
        
        due_date_str = request.form.get('due_date')
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.datetime.strptime(due_date_str, '%Y-%m-%d')
            except ValueError:
                print(f"Advertencia: Fecha límite '{due_date_str}' en formato incorrecto.")
        
        if task_content:
            new_task = Task(content=task_content, is_urgent=is_urgent, is_important=is_important, due_date=due_date)
            try:
                db.session.add(new_task)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Error al añadir tarea: {e}")
    # Redirect back to the current view mode and filters if they exist
    return redirect(url_for('index', 
                             view_mode=request.form.get('current_view_mode', 'list'),
                             urgent=request.form.get('current_urgent_filter'), # Puede ser '' o 'true'/'false'
                             important=request.form.get('current_important_filter'))) # Puede ser '' o 'true'/'false'

@app.route('/delete/<int:task_id>')
def delete_task(task_id):
    task_to_delete = Task.query.get_or_404(task_id)
    try:
        db.session.delete(task_to_delete)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error al eliminar tarea: {e}")
    # Redirect back to the current view mode and filters if they exist
    return redirect(url_for('index', 
                             view_mode=request.args.get('view_mode', 'list'),
                             urgent=request.args.get('urgent'),
                             important=request.args.get('important')))

@app.route('/complete/<int:task_id>')
def complete_task(task_id):
    task_to_complete = Task.query.get_or_404(task_id)
    try:
        task_to_complete.completed = not task_to_complete.completed
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error al completar/descompletar tarea: {e}")
    # Redirect back to the current view mode and filters if they exist
    return redirect(url_for('index', 
                             view_mode=request.args.get('view_mode', 'list'),
                             urgent=request.args.get('urgent'),
                             important=request.args.get('important')))

@app.route('/edit/<int:task_id>')
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    # Pass current view mode and filters to edit.html so it can pass them back to update_task
    return render_template('edit.html', 
                           task=task,
                           view_mode=request.args.get('view_mode', 'list'),
                           urgent=request.args.get('urgent'),
                           important=request.args.get('important'))

@app.route('/update/<int:task_id>', methods=['POST'])
def update_task(task_id):
    task_to_update = Task.query.get_or_404(task_id)
    if request.method == 'POST':
        updated_content = request.form['content'].strip()
        updated_is_urgent = 'is_urgent' in request.form
        updated_is_important = 'is_important' in request.form
        
        updated_due_date_str = request.form.get('due_date')
        updated_due_date = None
        if updated_due_date_str:
            try:
                updated_due_date = datetime.datetime.strptime(updated_due_date_str, '%Y-%m-%d')
            except ValueError:
                print(f"Advertencia: Fecha límite actualizada '{updated_due_date_str}' en formato incorrecto.")
        elif not updated_due_date_str: # If the field is left empty, set to None
            updated_due_date = None

        if updated_content:
            try:
                task_to_update.content = updated_content
                task_to_update.is_urgent = updated_is_urgent
                task_to_update.is_important = updated_is_important
                task_to_update.due_date = updated_due_date
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Error al actualizar tarea: {e}")
    # Redirect back to the current view mode and filters
    return redirect(url_for('index', 
                             view_mode=request.form.get('current_view_mode', 'list'),
                             urgent=request.form.get('current_urgent_filter'),
                             important=request.form.get('current_important_filter')))

if __name__ == '__main__':
    app.run(debug=True)