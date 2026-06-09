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
    """API para buscar todas as tarefas"""
    try:
        tasks = get_tasks()
        # Ordenar por ordem
        tasks.sort(key=lambda x: x.get('order', 0))
        pending_count = get_pending_count()
        
        return jsonify({
            'success': True,
            'tasks': tasks,
            'pending_count': pending_count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tasks', methods=['POST'])
def api_add_task():
    """API para adicionar nova tarefa"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({
                'success': False,
                'error': 'Texto da tarefa é obrigatório'
            }), 400
        
        # ALUNOS: Esta parte funcionará apenas após implementar get_tasks() e save_tasks()
        tasks = get_tasks()
        
        # Criar nova tarefa
        new_task = {
            'id': str(uuid.uuid4()),
            'text': text,
            'completed': False,
            'order': len(tasks),
            'created_at': datetime.now().isoformat()
        }
        
        tasks.append(new_task)
        
        if save_tasks(tasks):
            return jsonify({
                'success': True,
                'task': new_task
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao salvar tarefa - Redis não implementado'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def api_delete_task(task_id):
    """API para remover tarefa"""
    try:
        # ALUNOS: Esta parte funcionará apenas após implementar get_tasks() e save_tasks()
        tasks = get_tasks()
        tasks = [task for task in tasks if task['id'] != task_id]
        
        if save_tasks(tasks):
            return jsonify({
                'success': True,
                'message': 'Tarefa removida com sucesso'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao remover tarefa - Redis não implementado'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tasks/<task_id>/toggle', methods=['PUT'])
def api_toggle_task(task_id):
    """API para marcar/desmarcar tarefa como concluída"""
    try:
        # ALUNOS: Esta parte funcionará apenas após implementar get_tasks() e save_tasks()
        tasks = get_tasks()
        
        for task in tasks:
            if task['id'] == task_id:
                task['completed'] = not task['completed']
                break
        
        if save_tasks(tasks):
            return jsonify({
                'success': True,
                'message': 'Status da tarefa atualizado'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao atualizar tarefa - Redis não implementado'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tasks/reorder', methods=['PUT'])
def api_reorder_tasks():
    """API para reordenar tarefas (drag and drop)"""
    try:
        data = request.get_json()
        task_ids = data.get('task_ids', [])
        
        # ALUNOS: Esta parte funcionará apenas após implementar get_tasks() e save_tasks()
        tasks = get_tasks()
        
        # Criar mapa de tarefas por ID
        task_map = {task['id']: task for task in tasks}
        
        # Reordenar tarefas conforme nova ordem
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
                'error': 'Erro ao reordenar tarefas - Redis não implementado'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)

# DICAS PARA ALUNOS:
#
# 1. CONFIGURAÇÃO REDIS:
#    redis_client = redis.Redis(
#        host='seu-host',
#        port=6379,
#        password='sua-senha',  # se necessário
#        db=0,
#        decode_responses=True
#    )
#
# 2. IMPLEMENTAR get_tasks():
#    try:
#        tasks_data = redis_client.get(TASKS_KEY)
#        if tasks_data:
#            return json.loads(tasks_data)
#        return []
#    except:
#        return []
#
# 3. IMPLEMENTAR save_tasks():
#    try:
#        redis_client.set(TASKS_KEY, json.dumps(tasks))
#        return True
#    except:
#        return False
#
# 4. TESTAR CONEXÃO:
#    try:
#        redis_client.ping()
#        print("Redis conectado!")
#    except:
#        print("Erro ao conectar ao Redis")
