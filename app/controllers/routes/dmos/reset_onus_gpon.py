import os
from app import db
from dotenv import load_dotenv
from app.models import Users, Olts
from cryptography.fernet import Fernet
from flask import Blueprint, render_template, flash
from app.controllers.forms.reset_onus_gpon import Reset_onus_gpon_form
from flask_login import current_user, login_required, fresh_login_required
from app.controllers.netmiko.dmos.reset_onus_gpon import execute_reset_onus_gpon

load_dotenv()

reset_onus_gpon_bp = Blueprint('reset_onus_gpon_bp', __name__)
fernet_key = Fernet(os.getenv('MY_FERNET_KEY'))


@reset_onus_gpon_bp.route('/reset_onus_gpon', methods=['GET', 'POST'])
@login_required
@fresh_login_required
def reset_onus_gpon():
    form = Reset_onus_gpon_form()
    hosts = db.session.execute(db.select(Olts).order_by(Olts.hostname)).scalars()
    form.hostname.choices = [('', 'Selecione uma OLT')] + [(host.ip_address, host.hostname) for host in hosts]

    current_user_record = db.session.execute(db.select(Users).filter_by(username=current_user.username)).scalar_one_or_none()
    current_user_decrypted_password = fernet_key.decrypt(current_user_record.password).decode('utf-8')

    if form.validate_on_submit():
        execute_reset_onus_gpon(
            hostname=form.hostname.data,
            username=current_user.username,
            password=current_user_decrypted_password,
            chassis=form.chassis.data,
            slot=form.slot.data,
            port_id=form.port_id.data
        )

        flash('Reset de ONUs executado com sucesso!', category='success')

    else:
        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"Error in {field}: {error}", category='danger')

    return render_template(
        'vendors/dmos/reset_onus_gpon.html',
        form=form
    )
