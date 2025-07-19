import os
from app import db
from dotenv import load_dotenv

from flask import Blueprint, render_template, flash
from flask_login import current_user, login_required, fresh_login_required

from app.models import Routers
from app.controllers.forms.set_clear_pppoe_session import SetClearPppoeSessionForm
from app.controllers.netmiko.junos.set_clear_pppoe_session import clear_pppoe_session as execute_clear_pppoe

from cryptography.fernet import Fernet

load_dotenv()

# Inicializa o Blueprint
set_clear_pppoe_session_bp = Blueprint('set_clear_pppoe_session_bp', __name__)
fernet_key = Fernet(os.getenv('MY_FERNET_KEY'))


# Rota: set_clear_pppoe_session
@set_clear_pppoe_session_bp.route('/set_clear_pppoe_session', methods=['GET', 'POST'])
@login_required
@fresh_login_required
def clear_pppoe_session():
    form = SetClearPppoeSessionForm()
    user_decrypted_password = fernet_key.decrypt(current_user.password).decode('utf-8')
    hosts = db.session.execute(db.select(Routers).order_by(Routers.ip_address)).scalars()
    form.hostname.choices = [(host.ip_address, host.hostname) for host in hosts]
    output = None

    if form.validate_on_submit():
        output = execute_clear_pppoe(
            hostname=form.hostname.data,
            username=current_user.username,
            password=user_decrypted_password,
            user_name=form.user_name.data,
        )

        flash('Comando executado!', category='success')

    else:
        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"Erro no campo {field}: {error}", category='danger')

    return render_template(
        'vendors/junos/set_clear_pppoe_session.html',
        form=form,
        output=output,
    )
