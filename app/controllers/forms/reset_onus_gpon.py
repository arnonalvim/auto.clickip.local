from flask_wtf import FlaskForm
from wtforms import SelectMultipleField, SelectField, SubmitField
from wtforms.validators import DataRequired


class Reset_onus_gpon_form(FlaskForm):
    hostname = SelectMultipleField(
        'OLTs',
        choices=[],
        validators=[DataRequired(message='Por favor, selecione pelo menos uma OLT')]
    )

    chassis = SelectField(
        'chassi', choices=[('1', '1')]
    )

    slot = SelectField(
        'slot', choices=[(str(i), str(i)) for i in range(1, 3)]
    )

    port_id = SelectMultipleField(
        'gpon',
        choices=[(str(i), str(i)) for i in range(1, 33)],
        validators=[DataRequired(message='Por favor, selecione pelo menos uma porta GPON')]
    )

    submit = SubmitField('Executar Reset ONUs')
