from flask import Flask, render_template, request, jsonify
from datetime import datetime
from dotenv import load_dotenv
import json
import redis
import uuid
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-56549819'

# Carrega as variáveis do arquivo .env
load_dotenv()

redis_client = redis.Redis(
    host= os.getenv('REDIS_HOST'),
    port= int(os.getenv('REDIS_PORT')),
    username= os.getenv('REDIS_USERNAME'),
    password= os.getenv('REDIS_PASSWORD'),
    decode_responses= True,
)

TASKS_KEY = "todo_tasks"

def get_tasks():
    try:
        tasks_data = redis_client.get(TASKS_KEY)
        if tasks_data:
            return json.loads(tasks_data)
        return []
    except Exception as e:
        print(f"Erro ao buscar tarefas no Redis: {e}")
        return []

def save_tasks(tasks):
    try:
        redis_client.set(TASKS_KEY, json.dumps(tasks))
        return True
    except Exception as e:
        print(f"Erro ao salvar tarefas no Redis: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/tasks', methods=['GET'])
def api_get_tasks():
    try:
        tasks = get_tasks()
        tasks.sort(key=lambda x: x.get('order', 0))
        pending_count = len([task for task in tasks if not task['completed']])
        
        return jsonify({
            'success': True,
            'tasks': tasks,
            'pending_count': pending_count
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tasks', methods=['POST'])
def add_task():
    try:
        data = request.json
        text = data.get('text', '').strip()
        if not text:
            return jsonify({'success': False, 'error': 'O texto da tarefa não pode ser vazio'}), 400
        
        tasks = get_tasks()
        
        new_task = {
            "id": str(uuid.uuid4()),
            "text": text,
            "completed": False,
            "order": len(tasks),
            "created_at": datetime.now().isoformat()
        }
        
        tasks.append(new_task)
        if save_tasks(tasks):
            return jsonify({'success': True, 'task': new_task})
        return jsonify({'success': False, 'error': 'Erro ao salvar tarefa'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tasks/<task_id>/toggle', methods=['PUT'])
def toggle_task(task_id):
    try:
        tasks = get_tasks()
        task_found = False
        for task in tasks:
            if task['id'] == task_id:
                task['completed'] = not task['completed']
                task_found = True
                break
        
        if not task_found:
            return jsonify({'success': False, 'error': 'Tarefa não encontrada'}), 404
            
        if save_tasks(tasks):
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Erro ao atualizar status'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    try:
        tasks = get_tasks()
        initial_len = len(tasks)
        tasks = [task for task in tasks if task['id'] != task_id]
        
        if len(tasks) == initial_len:
            return jsonify({'success': False, 'error': 'Tarefa não encontrada'}), 404
        
        for i, task in enumerate(tasks):
            task['order'] = i
            
        if save_tasks(tasks):
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Erro ao remover tarefa'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tasks/reorder', methods=['PUT'])
def reorder_tasks():
    try:
        task_ids = request.json.get('task_ids', [])
        tasks = get_tasks()
        
        task_map = {task['id']: task for task in tasks}
        reordered_tasks = []
        
        for i, task_id in enumerate(task_ids):
            if task_id in task_map:
                task = task_map[task_id]
                task['order'] = i
                reordered_tasks.append(task)
        
        if save_tasks(reordered_tasks):
            return jsonify({
                'success': True,
                'message': 'Ordem das tarefas atualizada'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao reordenar tarefas'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)