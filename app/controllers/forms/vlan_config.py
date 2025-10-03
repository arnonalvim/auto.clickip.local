from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, IntegerField, StringField
from wtforms.validators import DataRequired, NumberRange, Length


class Vlan_config_form(FlaskForm):
    hostname = SelectField(
        '',
        choices=[],
        validators=[DataRequired(message='Por favor, selecione um Switch')]
    )

    vlan_id = IntegerField(
        'Vlan-ID',
        validators=[DataRequired(), NumberRange(min=1, max=4096)],
        default=1024
    )

    description = StringField(
        'Descrição',
        validators=[DataRequired(), Length(min=1, max=100)],
        render_kw={"placeholder": "Digite uma descrição para a VLAN"}
    )

    eth_ports = [f"hundred-gigabit-ethernet-1/1/{i}" for i in range(1, 48)]
    ten_gig_ports = [f"ten-gigabit-ethernet-1/1/{i}" for i in range(1, 48)]
    twf_gig_ports = [f"twenty-five-g-ethernet-1/1/{i}" for i in range(1, 48)]
    lags = [f"lag-{i}" for i in range(1, 20)]

    port_choices = eth_ports + ten_gig_ports + twf_gig_ports + lags

    port_dest = SelectField(
        'Porta de Destino',
        choices=[('', 'Selecione uma Porta')] + [(p, p) for p in port_choices],
        validators=[DataRequired(message='Por favor, selecione uma Porta')]
    )

    tagoruntag = SelectField(
        'Tipo',
        choices=[('tagged', 'Tagged'), ('untagged', 'Untagged')],
        validators=[DataRequired()]
    )

    submit = SubmitField('Executar commit')
