from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField, HiddenField
from wtforms.validators import DataRequired


class Att_onus_gpon_form(FlaskForm):
    hostname = SelectField('Hostname', validators=[DataRequired()], choices=[])
    # Campo oculto para armazenar as OLTs selecionadas (valores separados por vírgula)
    selected_olts = HiddenField()
    # "*" como primeira opção serve para marcar tudo
    chassis = SelectField(
        'Chassis',
        validators=[DataRequired()],
        choices=[('1', '1')]
    )
    slot = SelectField(
        'Slot',
        validators=[DataRequired()],
        choices=[(str(i), str(i)) for i in range(1, 3)] + [('*', '* (Todas)')]
    )
    port_id = SelectField(
        'Porta',
        validators=[DataRequired()],
        choices=[(str(i), str(i)) for i in range(1, 33)] + [('*', '* (Todas)')]
    )
    firmware_file = StringField('Nome FW')
    selected_onus = HiddenField()
    submit_get_info = SubmitField('Buscar ONUs')
