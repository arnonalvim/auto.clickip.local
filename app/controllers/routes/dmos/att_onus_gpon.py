import os
# import json
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


def parse_onus_data(json_data, chassis, slot, port_id):
    """
    Extrai as informações relevantes das ONUs do JSON retornado
    Suporta wildcards para buscar em múltiplas interfaces
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
                        'eq_id': onu_status.get('eq-id', 'N/A')
                    }

                    onus_list.append(onu_info)

    except Exception as e:
        print(f"Erro ao processar dados JSON: {e}")

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

        hostname = data.get('hostname')
        firmware_file = data.get('firmware_file')
        selected_onus = data.get('selected_onus')

        if not hostname or not firmware_file or not selected_onus:
            return jsonify({
                'success': False,
                'message': 'Dados incompletos para a atualização'
            })

        current_user_record = db.session.execute(
            db.select(Users).filter_by(username=current_user.username)
        ).scalar_one_or_none()
        current_user_decrypted_password = fernet_key.decrypt(current_user_record.password).decode('utf-8')

        result = execute_firmware_update(
            hostname=hostname,
            username=current_user.username,
            password=current_user_decrypted_password,
            selected_onus=selected_onus,
            firmware_file=firmware_file
        )

        if result["success"]:
            return jsonify({
                'success': True,
                'message': f'Comandos de atualização enviados com sucesso para {len(selected_onus)} ONUs!',
                'output': result.get('output', '')
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Erro na atualização: {result["error"]}'
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao processar requisição: {str(e)}'
        })


@att_onus_gpon_bp.route('/att_onus_gpon', methods=['GET', 'POST'])
@login_required
@fresh_login_required
def att_onus_gpon():
    form = Att_onus_gpon_form()
    hosts = db.session.execute(db.select(Olts).order_by(Olts.hostname)).scalars()
    form.hostname.choices = [('', 'Selecione uma OLT')] + [(host.ip_address, host.hostname) for host in hosts]

    current_user_record = db.session.execute(
        db.select(Users).filter_by(username=current_user.username)
    ).scalar_one_or_none()
    current_user_decrypted_password = fernet_key.decrypt(current_user_record.password).decode('utf-8')

    onus_data = []
    show_table = False

    if request.method == 'POST':
        if form.submit_get_info.data:
            if form.hostname.data and form.chassis.data and form.slot.data and form.port_id.data:
                result = get_onus_info(
                    hostname=form.hostname.data,
                    username=current_user.username,
                    password=current_user_decrypted_password,
                    chassis=form.chassis.data,
                    slot=form.slot.data,
                    port_id=form.port_id.data
                )

                if result["success"]:
                    onus_data = parse_onus_data(
                        result["data"],
                        form.chassis.data,
                        form.slot.data,
                        form.port_id.data
                    )
                    if onus_data:
                        show_table = True
                        pattern = f'{form.chassis.data}/{form.slot.data}/{form.port_id.data}'
                        flash(
                            f'✅ Encontradas {len(onus_data)} ONUs no padrão GPON {pattern}',
                            'success'
                        )
                    else:
                        pattern = f'{form.chassis.data}/{form.slot.data}/{form.port_id.data}'
                        flash(f'⚠️ Nenhuma ONU encontrada no padrão GPON {pattern}', 'warning')
                else:
                    flash(f'Erro ao buscar informações: {result["error"]}', 'danger')
                    if "raw_output" in result:
                        flash(f'Saída bruta: {result["raw_output"][:500]}...', 'info')
            else:
                flash('Por favor, preencha todos os campos para buscar as ONUs', 'danger')

    if form.errors:
        for field, errors in form.errors.items():
            if field != 'firmware_file':
                for error in errors:
                    flash(f"Erro no campo {field}: {error}", 'danger')

    return render_template(
        'vendors/dmos/att_onus_gpon.html',
        form=form,
        onus_data=onus_data,
        show_table=show_table
    )
