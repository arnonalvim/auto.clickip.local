import os
from app import db
from dotenv import load_dotenv
from app.models import Users, Olts
from cryptography.fernet import Fernet
from flask import Blueprint, render_template, flash, request
from app.controllers.forms.set_commands_massive import SetCommandsMassiveForm
from flask_login import current_user, login_required, fresh_login_required
from app.controllers.netmiko.dmos.set_commands_massive import execute_commands_massive

load_dotenv()

set_commands_massive_bp = Blueprint('set_commands_massive_bp', __name__)
fernet_key = Fernet(os.getenv('MY_FERNET_KEY'))


@set_commands_massive_bp.route('/set_commands_massive', methods=['GET', 'POST'])
@login_required
@fresh_login_required
def set_commands_massive():
    form = SetCommandsMassiveForm()
    hosts = db.session.execute(db.select(Olts).order_by(Olts.hostname)).scalars()
    form.hostnames.choices = [(host.ip_address, host.hostname) for host in hosts]

    results = None
    total_olts = 0
    successful_olts = 0
    failed_olts = 0

    current_user_record = db.session.execute(db.select(Users).filter_by(username=current_user.username)).scalar_one_or_none()
    current_user_decrypted_password = fernet_key.decrypt(current_user_record.password).decode('utf-8')

    if request.method == 'POST':
        # Debug: vamos ver o que está sendo enviado
        print("=== DEBUG INFO ===")
        print("Form data:", request.form)
        print("Selected hostnames:", request.form.getlist('hostnames'))
        print("Commands:", request.form.get('commands'))
        print("Form validates:", form.validate())
        if form.errors:
            print("Form errors:", form.errors)
        print("==================")

        if form.validate_on_submit():
            selected_hostnames = form.hostnames.data
            commands = form.commands.data

            # Filtra apenas IPs válidos
            selected_hostnames = [ip for ip in selected_hostnames if ip]

            if not selected_hostnames:
                flash('Por favor, selecione pelo menos uma OLT.', category='danger')
                return render_template(
                    'vendors/dmos/set_commands_massive.html',
                    form=form,
                    results=results,
                    total_olts=total_olts,
                    successful_olts=successful_olts,
                    failed_olts=failed_olts
                )

            if not commands or not commands.strip():
                flash('Por favor, digite pelo menos um comando.', category='danger')
                return render_template(
                    'vendors/dmos/set_commands_massive.html',
                    form=form,
                    results=results,
                    total_olts=total_olts,
                    successful_olts=successful_olts,
                    failed_olts=failed_olts
                )

            # Converte IPs selecionados para (ip, hostname)
            hosts_dict = {host.ip_address: host.hostname for host in db.session.execute(db.select(Olts)).scalars()}
            hostnames_data = [(ip, hosts_dict.get(ip, ip)) for ip in selected_hostnames if ip in hosts_dict]

            total_olts = len(hostnames_data)

            if hostnames_data:
                flash(f'Executando comandos em {total_olts} OLT(s)...', category='info')

                results = execute_commands_massive(
                    hostnames_data=hostnames_data,
                    username=current_user.username,
                    password=current_user_decrypted_password,
                    commands=commands
                )

                # Conta sucessos e falhas
                successful_olts = sum(1 for r in results if r.get('success', False))
                failed_olts = total_olts - successful_olts

                if successful_olts > 0:
                    flash(f'Comandos executados com sucesso em {successful_olts} OLT(s)!', category='success')

                if failed_olts > 0:
                    flash(f'Falha na execução em {failed_olts} OLT(s). Verifique os detalhes abaixo.', category='warning')

            else:
                flash('Nenhuma OLT válida foi selecionada.', category='danger')

        else:
            # Se a validação falhou, mostra os erros
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f"Erro: {error}", category='danger')

    return render_template(
        'vendors/dmos/set_commands_massive.html',
        form=form,
        results=results,
        total_olts=total_olts,
        successful_olts=successful_olts,
        failed_olts=failed_olts
    )
