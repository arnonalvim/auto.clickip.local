import os
from app import db
from dotenv import load_dotenv
from app.models import Users, Switches
from cryptography.fernet import Fernet
from flask import Blueprint, render_template, flash
from app.controllers.forms.vlan_config import Vlan_config_form
from flask_login import current_user, login_required, fresh_login_required
from app.controllers.netmiko.dmos.vlan_config import execute_vlan_config

load_dotenv()

vlan_config_bp = Blueprint('vlan_config_bp', __name__)
fernet_key = Fernet(os.getenv('MY_FERNET_KEY'))


@vlan_config_bp.route('/vlan_config', methods=['GET', 'POST'])
@login_required
@fresh_login_required
def vlan_config():
    form = Vlan_config_form()
    hosts = db.session.execute(db.select(Switches).order_by(Switches.hostname)).scalars()
    form.hostname.choices = [('', 'Selecione um Switch')] + [(host.ip_address, host.hostname) for host in hosts]

    output = None

    current_user_record = db.session.execute(db.select(Users).filter_by(username=current_user.username)).scalar_one_or_none()
    current_user_decrypted_password = fernet_key.decrypt(current_user_record.password).decode('utf-8')

    if form.validate_on_submit():
        output = execute_vlan_config(
            hostname=form.hostname.data,
            username=current_user.username,
            password=current_user_decrypted_password,
            vlan_id=form.vlan_id.data,
            description=form.description.data,
            interface=form.port_dest.data,
            tagoruntag=form.tagoruntag.data
        )

        flash('Comando enviado!', category='success')

    else:
        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"Error in {field}: {error}", category='danger')

    return render_template(
        'vendors/dmos/vlan_config.html',
        form=form,
        output=output,
    )
