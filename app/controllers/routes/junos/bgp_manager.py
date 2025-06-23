import os
from app import db
from dotenv import load_dotenv
from cryptography.fernet import Fernet
from app.controllers.forms.bgp_manager import BgpManagerForm
from app.models import Routers, NeighborBgpIpv4, NeighborBgpIpv6
from flask import Blueprint, request, render_template, flash, jsonify
from flask_login import current_user, login_required, fresh_login_required
from app.controllers.netmiko.junos.bgp_manager import bgp_manager as bgp

load_dotenv()

# Inicializa o Blueprint
bgp_manager_bp = Blueprint('bgp_manager_bp', __name__)
fernet_key = Fernet(os.getenv('MY_FERNET_KEY'))


# Rota: bgp_manager_bp
@bgp_manager_bp.route('/bgp_manager', methods=['GET', 'POST'])
@login_required
@fresh_login_required
def bgp_manager():
    form = BgpManagerForm()
    current_user_decrypted_password = fernet_key.decrypt(current_user.password).decode('utf-8')
    hosts = db.session.execute(db.select(Routers).order_by(Routers.hostname)).scalars().all()
    form.hostname.choices = [(host.ip_address, host.hostname) for host in hosts]

    # Atualiza as choices do neighbor baseado no grupo recebido
    if form.group.data:
        if form.group.data == 'Sessoes_Transito_IPv4':
            neighbors = db.session.execute(db.select(NeighborBgpIpv4).order_by(NeighborBgpIpv4.description)).scalars().all()
        else:
            neighbors = db.session.execute(db.select(NeighborBgpIpv6).order_by(NeighborBgpIpv6.description)).scalars().all()

    # Atualiza as opções do campo neighbor
    form.neighbor.choices = [(n.neighbor, n.description) for n in neighbors]

    output = None

    if form.validate_on_submit():

        output = bgp(
            hostname=form.hostname.data,
            username=current_user.username,
            password=current_user_decrypted_password,
            action=form.action.data,
            group=form.group.data,
            neighbor=form.neighbor.data
        )

        flash('Command sent successfully!', category='success')

    else:
        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"Error in {field}: {error}", category='danger')

    return render_template(
        'vendors/junos/bgp_manager.html',
        form=form,
        output=output,
    )


@bgp_manager_bp.route('/get_neighbors', methods=['GET', 'POST'])
@login_required
def get_neighbors():
    data = request.json
    group = data.get("group")

    if not group:
        return jsonify({"error": "O campo 'group' é obrigatório"}), 400

    if group == 'Sessoes_Transito_IPv4':
        neighbors = db.session.execute(db.select(NeighborBgpIpv4).order_by(NeighborBgpIpv4.description)).scalars().all()
    else:
        neighbors = db.session.execute(db.select(NeighborBgpIpv6).order_by(NeighborBgpIpv6.description)).scalars().all()

    response = jsonify([{"neighbor": n.neighbor, "description": n.description} for n in neighbors])
    return response
