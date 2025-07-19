
import os
import threading
import uuid
from app import db
from dotenv import load_dotenv
from app.models import Users, Olts
from cryptography.fernet import Fernet
from flask import Blueprint, render_template, request, jsonify
from app.controllers.forms.reset_onus_gpon import Reset_onus_gpon_form
from flask_login import current_user, login_required, fresh_login_required
from app.controllers.netmiko.dmos.reset_onus_gpon import execute_reset_onus_gpon

load_dotenv()

reset_onus_gpon_bp = Blueprint('reset_onus_gpon_bp', __name__)
fernet_key = Fernet(os.getenv('MY_FERNET_KEY'))

# Dicionário
task_status = {}


def background_reset_task(task_id, hostnames, username, password, chassis, slot, port_ids):
    """Executa o reset em segundo plano com progresso incremental"""
    try:
        total_tasks = len(hostnames) * len(port_ids)
        completed_tasks = 0
        results = []
        # Inicializa o status da tarefa
        task_status[task_id] = {
            'status': 'running',
            'progress': 0,
            'total': total_tasks,
            'completed': completed_tasks,
            'results': [],
            'current_operation': 'Iniciando...'
        }
        # Executa cada combinação de hostname e porta
        for hostname in hostnames:
            for port_id in port_ids:
                # Atualiza status atual
                task_status[task_id]['current_operation'] = f'Processando {hostname} - Porta {port_id}'
                # Executa o reset para esta combinação
                result = execute_reset_onus_gpon(
                    hostname=hostname,
                    username=username,
                    password=password,
                    chassis=chassis,
                    slot=slot,
                    port_id=port_id
                )
                results.append(result)
                completed_tasks += 1
                # Atualiza progresso
                progress = (completed_tasks / total_tasks) * 100
                task_status[task_id].update({
                    'progress': progress,
                    'completed': completed_tasks,
                    'results': results,
                    'current_operation': f'Concluído {hostname} - Porta {port_id}'
                })
        # Finaliza a tarefa
        task_status[task_id].update({
            'status': 'completed',
            'progress': 100,
            'current_operation': 'Processo concluído!'
        })
    except Exception as e:
        task_status[task_id] = {
            'status': 'error',
            'error': str(e),
            'progress': 0,
            'total': 0,
            'completed': 0,
            'results': [],
            'current_operation': f'Erro: {str(e)}'
        }


@reset_onus_gpon_bp.route('/reset_onus_gpon', methods=['GET', 'POST'])
@login_required
@fresh_login_required
def reset_onus_gpon():
    form = Reset_onus_gpon_form()
    hosts = db.session.execute(db.select(Olts).order_by(Olts.hostname)).scalars()
    form.hostname.choices = [(host.ip_address, host.hostname) for host in hosts]

    if request.method == 'POST' and request.is_json:
        data = request.get_json()
        current_user_record = db.session.execute(
            db.select(Users).filter_by(username=current_user.username)
        ).scalar_one_or_none()
        current_user_decrypted_password = fernet_key.decrypt(current_user_record.password).decode('utf-8')
        # Gera ID único para a tarefa
        task_id = str(uuid.uuid4())
        # Inicia tarefa em segundo plano
        thread = threading.Thread(
            target=background_reset_task,
            args=(
                task_id,
                data.get('hostnames', []),
                current_user.username,
                current_user_decrypted_password,
                data.get('chassis'),
                data.get('slot'),
                data.get('port_ids', [])
            )
        )
        thread.daemon = True
        thread.start()
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': 'Reset iniciado em segundo plano!'
        })

    return render_template(
        'vendors/dmos/reset_onus_gpon.html',
        form=form
    )


@reset_onus_gpon_bp.route('/reset_onus_gpon/status/<task_id>')
@login_required
def get_task_status(task_id):
    """Retorna o status de uma tarefa"""
    status = task_status.get(task_id, {'status': 'not_found'})
    return jsonify(status)


@reset_onus_gpon_bp.route('/reset_onus_gpon/clear/<task_id>')
@login_required
def clear_task_status(task_id):
    """Remove uma tarefa da memória"""
    if task_id in task_status:
        del task_status[task_id]
    return jsonify({'success': True})
