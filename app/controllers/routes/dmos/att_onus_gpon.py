import os
from app import db
from dotenv import load_dotenv
from app.models import Users, Olts
from cryptography.fernet import Fernet
from flask import Blueprint, render_template, flash, request, jsonify
from app.controllers.forms.att_onus_gpon import Att_onus_gpon_form
from flask_login import current_user, login_required, fresh_login_required
from app.controllers.netmiko.dmos.att_onus_gpon import get_onus_info, execute_firmware_update

load_dotenv()

att_onus_gpon_bp = Blueprint('att_onus_gpon_bp', __name__)
fernet_key = Fernet(os.getenv('MY_FERNET_KEY'))


def parse_onus_data(json_data, chassis, slot, port_id, hostname):
    """
    Extrai as informações relevantes das ONUs do JSON retornado
    Suporta wildcards para buscar em múltiplas interfaces
    Agora inclui o hostname da OLT de origem
    """
    onus_list = []

    try:
        # Navegar pela estrutura JSON
        interfaces = json_data.get('data', {}).get('dmos-base:config', {}).get('interface', {})
        gpon_interfaces = interfaces.get('interface-pon:gpon', [])

        for gpon_interface in gpon_interfaces:
            interface_chassis = gpon_interface.get('chassis-id')
            interface_slot = gpon_interface.get('slot-id')
            interface_port = gpon_interface.get('port-id')

            # Verificar se a interface corresponde aos critérios (com suporte a wildcards)
            chassis_match = (chassis == '*' or interface_chassis == int(chassis))
            slot_match = (slot == '*' or interface_slot == int(slot))
            port_match = (port_id == '*' or interface_port == int(port_id))

            if chassis_match and slot_match and port_match:
                onus = gpon_interface.get('onu:onu', [])

                for onu in onus:
                    onu_status = onu.get('onu-status:onu-status', {})

                    onu_info = {
                        'interface': f"gpon {interface_chassis}/{interface_slot}/{interface_port}",
                        'chassis': str(interface_chassis),
                        'slot': str(interface_slot),
                        'port': str(interface_port),
                        'onu_id': onu.get('id', 'N/A'),
                        'oper_state': onu_status.get('oper-state', 'N/A'),
                        'serial_number': onu_status.get('serial-number', 'N/A'),
                        'active_fw': onu_status.get('active-fw', 'N/A'),
                        'standby_fw': onu_status.get('standby-fw', 'N/A'),
                        'eq_id': onu_status.get('eq-id', 'N/A'),
                        'hostname': hostname
                    }

                    onus_list.append(onu_info)

    except Exception as e:
        print(f"Erro ao processar dados JSON para {hostname}: {e}")

    return onus_list


@att_onus_gpon_bp.route('/att_onus_gpon_update', methods=['POST'])
@login_required
@fresh_login_required
def att_onus_gpon_update():
    """
    Rota AJAX para atualização de firmware sem recarregar a página
    """
    try:
        data = request.get_json()
        selected_olts = data.get('selected_olts', [])
        firmware_file = data.get('firmware_file')
        selected_onus = data.get('selected_onus')

        if not selected_olts or not firmware_file or not selected_onus:
            return jsonify({
                'success': False,
                'message': 'Dados incompletos para a atualização'
            })

        # Obter credenciais do usuário
        current_user_record = db.session.execute(
            db.select(Users).filter_by(username=current_user.username)
        ).scalar_one_or_none()
        current_user_decrypted_password = fernet_key.decrypt(current_user_record.password).decode('utf-8')

        # Buscar todos os hosts para criar mapeamento
        hosts_query = db.session.execute(db.select(Olts).order_by(Olts.hostname))
        hosts = hosts_query.scalars().all()
        # Criar mapeamento IP -> Host object e Hostname -> IP
        ip_to_host = {}
        hostname_to_ip = {}
        for host in hosts:
            ip_to_host[host.ip_address] = host
            hostname_to_ip[host.hostname] = host.ip_address

        # Agrupar ONUs por IP da OLT
        onus_by_ip = {}
        for onu_info in selected_onus:
            onu_hostname = onu_info.get('hostname')
            olt_ip = hostname_to_ip.get(onu_hostname)
            if not olt_ip:
                continue
            if olt_ip not in onus_by_ip:
                onus_by_ip[olt_ip] = []
            onus_by_ip[olt_ip].append(onu_info)

        # Verificar se as OLTs selecionadas correspondem às ONUs
        valid_olts = [olt_ip for olt_ip in selected_olts if olt_ip in onus_by_ip]

        if not valid_olts:
            return jsonify({
                'success': False,
                'message': 'Nenhuma OLT válida encontrada com as ONUs selecionadas'
            })

        results = []
        total_onus = 0
        successful_hosts = 0

        # Executar atualização para cada OLT válida
        for olt_ip in valid_olts:
            host_onus = onus_by_ip[olt_ip]
            total_onus += len(host_onus)
            # Buscar hostname para exibição
            host_obj = ip_to_host.get(olt_ip)
            display_name = host_obj.hostname if host_obj else olt_ip
            result = execute_firmware_update(
                hostname=olt_ip,
                username=current_user.username,
                password=current_user_decrypted_password,
                selected_onus=host_onus,
                firmware_file=firmware_file
            )
            results.append({
                'hostname': display_name,
                'ip': olt_ip,
                'success': result["success"],
                'message': result.get('output', '') if result["success"] else result.get('error', ''),
                'onu_count': len(host_onus)
            })
            if result["success"]:
                successful_hosts += 1

        # Preparar resposta consolidada
        if successful_hosts == len(valid_olts):
            return jsonify({
                'success': True,
                'message': f'✅ Comandos enviados com sucesso para {total_onus} ONUs em {successful_hosts} OLTs!',
                'details': results
            })
        elif successful_hosts > 0:
            return jsonify({
                'success': True,
                'message': f'⚠️ Sucesso parcial: {successful_hosts}/{len(valid_olts)} OLTs atualizadas. Total: {total_onus} ONUs processadas.',
                'details': results
            })
        else:
            return jsonify({
                'success': False,
                'message': f'❌ Falha em todas as {len(valid_olts)} OLTs selecionadas.',
                'details': results
            })

    except Exception as e:
        print(f"ERRO: Exceção na rota de atualização: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro ao processar requisição: {str(e)}'
        })


@att_onus_gpon_bp.route('/att_onus_gpon', methods=['GET', 'POST'])
@login_required
@fresh_login_required
def att_onus_gpon():
    form = Att_onus_gpon_form()
    try:
        hosts_query = db.session.execute(db.select(Olts).order_by(Olts.hostname))
        hosts = hosts_query.scalars().all()
    except Exception as e:
        print(f"ERRO: Erro na consulta à base de dados: {e}")
        hosts = []
    # Construir choices para o formulário
    form.hostname.choices = [('', 'Selecione uma OLT')] + [(host.ip_address, host.hostname) for host in hosts]

    current_user_record = db.session.execute(
        db.select(Users).filter_by(username=current_user.username)
    ).scalar_one_or_none()
    current_user_decrypted_password = fernet_key.decrypt(current_user_record.password).decode('utf-8')

    onus_data = []
    show_table = False

    if request.method == 'POST':
        if form.submit_get_info.data:
            # Obter OLTs selecionadas do campo oculto
            selected_olts_str = form.selected_olts.data
            if not selected_olts_str:
                flash('Por favor, selecione pelo menos uma OLT', 'danger')
                return render_template(
                    'vendors/dmos/att_onus_gpon.html',
                    form=form,
                    onus_data=onus_data,
                    show_table=show_table
                )
            selected_olts = [olt.strip() for olt in selected_olts_str.split(',') if olt.strip()]
            # Criar mapeamento IP -> hostname
            ip_to_hostname = {}
            for host in hosts:
                ip_to_hostname[host.ip_address] = host.hostname
            if form.chassis.data and form.slot.data and form.port_id.data:
                all_onus_data = []
                successful_queries = 0
                failed_hosts = []
                # Buscar ONUs em cada OLT selecionada
                for olt_ip in selected_olts:
                    # Buscar o hostname correspondente ao IP
                    olt_hostname = ip_to_hostname.get(olt_ip)
                    if not olt_hostname:
                        error_msg = f"IP {olt_ip} (hostname não encontrado)"
                        failed_hosts.append(error_msg)
                        continue
                    result = get_onus_info(
                        hostname=olt_ip,
                        username=current_user.username,
                        password=current_user_decrypted_password,
                        chassis=form.chassis.data,
                        slot=form.slot.data,
                        port_id=form.port_id.data
                    )

                    if result["success"]:
                        host_onus = parse_onus_data(
                            result["data"],
                            form.chassis.data,
                            form.slot.data,
                            form.port_id.data,
                            olt_hostname
                        )
                        all_onus_data.extend(host_onus)
                        successful_queries += 1
                    else:
                        error_msg = f"{olt_hostname} ({result['error']})"
                        failed_hosts.append(error_msg)

                # Preparar mensagens de feedback
                if all_onus_data:
                    show_table = True
                    pattern = f'{form.chassis.data}/{form.slot.data}/{form.port_id.data}'
                    success_msg = f'✅ Encontradas {len(all_onus_data)} ONUs no padrão GPON {pattern} em {successful_queries} OLTs'
                    if failed_hosts:
                        success_msg += f'. ⚠️ Falhas em: {", ".join(failed_hosts)}'
                    flash(success_msg, 'success' if not failed_hosts else 'warning')
                    onus_data = all_onus_data
                else:
                    pattern = f'{form.chassis.data}/{form.slot.data}/{form.port_id.data}'
                    if failed_hosts:
                        flash(f'❌ Nenhuma ONU encontrada. Falhas em: {", ".join(failed_hosts)}', 'danger')
                    else:
                        flash(f'⚠️ Nenhuma ONU encontrada no padrão GPON {pattern} nas OLTs selecionadas', 'warning')
            else:
                flash('Por favor, preencha todos os campos para buscar as ONUs', 'danger')

    if form.errors:
        for field, errors in form.errors.items():
            if field not in ['firmware_file', 'selected_olts']:
                for error in errors:
                    flash(f"Erro no campo {field}: {error}", 'danger')

    return render_template(
        'vendors/dmos/att_onus_gpon.html',
        form=form,
        onus_data=onus_data,
        show_table=show_table
    )
