import os
from app import db
from dotenv import load_dotenv
from app.models import Users, Switches
from cryptography.fernet import Fernet
from flask import Blueprint, render_template, flash
from app.controllers.forms.mpls_l2vpn_tunnel import Mpls_l2vpn_form
from flask_login import current_user, login_required, fresh_login_required
from app.controllers.netmiko.dmos.mpls_l2vpn_tunnel import execute_mpls_l2vpn

load_dotenv()

mpls_l2vpn_tunnel_bp = Blueprint('mpls_l2vpn_bp', __name__)
fernet_key = Fernet(os.getenv('MY_FERNET_KEY'))


@mpls_l2vpn_tunnel_bp.route('/mpls_l2vpn', methods=['GET', 'POST'])
@login_required
@fresh_login_required
def mpls_l2vpn():
    form = Mpls_l2vpn_form()
    hosts = db.session.execute(db.select(Switches).order_by(Switches.hostname)).scalars()
    form.hostname.choices = [('', 'Selecione um Switch')] + [(host.ip_address, host.hostname) for host in hosts]

    output = None

    current_user_record = db.session.execute(db.select(Users).filter_by(username=current_user.username)).scalar_one_or_none()
    current_user_decrypted_password = fernet_key.decrypt(current_user_record.password).decode('utf-8')

    if form.validate_on_submit():
        # Coletar todas as interfaces
        interfaces = []
        # Interface master
        if form.interface.data:
            interfaces.append(form.interface.data)
        # Interfaces adicionais (vem como string separada por vírgulas do javaccript)
        if form.additional_interfaces.data:
            additional = form.additional_interfaces.data.split(',')
            for interface in additional:
                if interface.strip():
                    interfaces.append(interface.strip())

        if interfaces:
            output = execute_mpls_l2vpn(
                hostname=form.hostname.data,
                username=current_user.username,
                password=current_user_decrypted_password,
                vlan_id=form.vlan_id.data,
                description=form.description.data,
                neib=form.neib.data,
                interfaces=interfaces
            )

            flash('Comando enviado!', category='success')
        else:
            flash('Por favor, selecione pelo menos uma interface!', category='danger')

    else:
        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"Error in {field}: {error}", category='danger')

    return render_template(
        'vendors/dmos/mpls_l2vpn_tunnel.html',
        form=form,
        output=output,
    )
