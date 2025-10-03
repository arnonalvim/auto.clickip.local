import os
from app import db
from dotenv import load_dotenv
from app.models import Routers
from cryptography.fernet import Fernet
from flask import Blueprint, render_template, flash, request
from flask_login import login_required, fresh_login_required, current_user
from app.controllers.forms.general_network_forms import SetPolicyWhitelistForm, GetPolicyWhitelistForm
from app.controllers.netmiko.junos.set_policy_whitelist import set_policy_whitelist as whitelist, get_policy_whitelist as get_whitelist, manage_policy_whitelist

load_dotenv()

# Inicializa o Blueprint
set_policy_whitelist_bp = Blueprint('set_policy_whitelist_bp', __name__)
fernet_key = Fernet(os.getenv('MY_FERNET_KEY'))


@set_policy_whitelist_bp.route('/set_policy_whitelist', methods=['GET', 'POST'])
@login_required
@fresh_login_required
def set_policy_whitelist():
    form = SetPolicyWhitelistForm()
    hosts = db.session.execute(db.select(Routers).order_by(Routers.ip_address)).scalars().all()
    form.hostname.choices = [(host.ip_address, host.hostname) for host in hosts]
    current_user_decrypted_password = fernet_key.decrypt(current_user.password).decode('utf-8')

    output = None

    if form.validate_on_submit():
        output = whitelist(
            hostname=form.hostname.data,
            username=current_user.username,
            password=current_user_decrypted_password,
            prefix=form.prefix_address.data
        )

        flash('Comando enviado!', category='success')

    else:
        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"Error in {field}: {error}", category='danger')

    return render_template(
        'vendors/junos/set_policy_whitelist.html',
        form=form,
        output=output,
    )


@set_policy_whitelist_bp.route('/get_policy_whitelist', methods=['GET', 'POST'])
@login_required
@fresh_login_required
def get_policy_whitelist():
    form = GetPolicyWhitelistForm()
    hosts = db.session.execute(db.select(Routers).order_by(Routers.ip_address)).scalars().all()
    form.hostname.choices = [(host.ip_address, host.hostname) for host in hosts]
    current_user_decrypted_password = fernet_key.decrypt(current_user.password).decode('utf-8')

    output = None

    if form.validate_on_submit():
        output = get_whitelist(
            form.hostname.data,
            current_user.username,
            current_user_decrypted_password,
        )

        flash('Comando enviado!', category='success')

    else:
        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"Error in {field}: {error}", category='danger')

    return render_template(
        'vendors/junos/get_policy_whitelist.html',
        form=form,
        output=output,
    )


@set_policy_whitelist_bp.route('/manage_policy_whitelist', methods=['GET', 'POST'])
@login_required
@fresh_login_required
def manage_policy_whitelist_route():
    """Nova rota unificada para gerenciar policy whitelist"""
    action = request.args.get('action', 'get')
    # Usar o formulário correto baseado na ação
    if action == 'set':
        form = SetPolicyWhitelistForm()
    else:
        form = GetPolicyWhitelistForm()
        action = 'get'

    hosts = db.session.execute(db.select(Routers).order_by(Routers.ip_address)).scalars().all()
    form.hostname.choices = [(host.ip_address, host.hostname) for host in hosts]
    current_user_decrypted_password = fernet_key.decrypt(current_user.password).decode('utf-8')

    output = None

    if form.validate_on_submit():
        try:
            if action == 'set':
                output = manage_policy_whitelist(
                    hostname=form.hostname.data,
                    username=current_user.username,
                    password=current_user_decrypted_password,
                    prefix=form.prefix_address.data,
                    action='set'
                )
            else:
                output = manage_policy_whitelist(
                    hostname=form.hostname.data,
                    username=current_user.username,
                    password=current_user_decrypted_password,
                    action='get'
                )

            flash('Comando enviado!', category='success')
        except Exception as e:
            flash(f'Erro ao executar comando: {str(e)}', category='danger')

    else:
        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"Error in {field}: {error}", category='danger')

    # Usar templates existentes baseado na ação
    if action == 'set':
        template_name = 'vendors/junos/set_policy_whitelist.html'
    else:
        template_name = 'vendors/junos/get_policy_whitelist.html'

    return render_template(
        template_name,
        form=form,
        output=output,
    )
