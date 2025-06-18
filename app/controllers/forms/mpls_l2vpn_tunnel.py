from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, IntegerField, StringField
# (FieldList, FormField nao usando no momento)
from wtforms.validators import DataRequired, NumberRange, Length


class InterfaceForm(FlaskForm):
    interface = SelectField(
        'Interface',
        choices=[],
        validators=[DataRequired(message='Por favor, selecione uma Interface')]
    )


class Mpls_l2vpn_form(FlaskForm):
    hostname = SelectField(
        '',
        choices=[],
        validators=[DataRequired(message='Por favor, selecione um Switch')]
    )

    vlan_id = IntegerField(
        'VLAN-ID',
        validators=[DataRequired(), NumberRange(min=1, max=4096)],
        default=1258
    )

    description = StringField(
        'Descrição',
        validators=[DataRequired(), Length(min=1, max=100)],
        render_kw={"placeholder": "Digite uma descrição para o VPN"}
    )

    neib = StringField(
        'Neighbor IP',
        validators=[DataRequired(), Length(min=7, max=15)],
        render_kw={"placeholder": "Ex: 192.168.1.1"}
    )

    eth_ports = [f"hundred-gigabit-ethernet-1/1/{i}" for i in range(1, 7)]
    ten_gig_ports = [f"ten-gigabit-ethernet-1/1/{i}" for i in range(1, 9)]
    twf_gig_ports = [f"twenty-five-g-ethernet-1/1/{i}" for i in range(1, 17)]
    lags = [f"lag-{i}" for i in range(1, 9)]

    port_choices = eth_ports + ten_gig_ports + twf_gig_ports + lags

    # Campo principal de interface (sempre presente)
    interface = SelectField(
        'Interface Principal',
        choices=[('', 'Selecione uma Interface')] + [(p, p) for p in port_choices],
        validators=[DataRequired(message='Por favor, selecione uma Interface')]
    )

    # Campo para interfaces adicionais (será preenchido via JavaScript)
    additional_interfaces = StringField('Interfaces Adicionais', default='')

    submit = SubmitField('Executar commit')
