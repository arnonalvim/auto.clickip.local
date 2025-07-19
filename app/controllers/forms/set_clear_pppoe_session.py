from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Length
from wtforms import StringField, SubmitField, SelectField


class SetClearPppoeSessionForm(FlaskForm):
    hostname = SelectField(
        'Router',
        choices=[],
        validators=[DataRequired()]
    )
    user_name = StringField(
        'Nome do Usuário',
        validators=[
            DataRequired(),
            Length(min=1, max=100, message="O nome do usuário deve ter entre 1 e 100 caracteres")
        ],
        render_kw={"placeholder": "Digite o nome do usuário PPPoE"}
    )
    submit = SubmitField('Executar Clear')
