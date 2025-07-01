from flask_wtf import FlaskForm
from wtforms import SelectMultipleField, TextAreaField, SubmitField
from wtforms.validators import ValidationError
from wtforms.widgets import CheckboxInput, ListWidget


class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()


class SetCommandsMassiveForm(FlaskForm):
    hostnames = MultiCheckboxField(
        'Selecionar OLTs',
        choices=[],
        coerce=str  # Força a seleção de tipo, chatgpt me ajudou e resolver esse problema
    )

    commands = TextAreaField(
        'Comandos',
        render_kw={
            'placeholder': 'Digite os comandos aqui (um por linha)\nExemplo:\nshow platform\nshow interface link',
            'rows': 10
        }
    )

    submit = SubmitField('Executar comandos em massa')

    def validate_hostnames(self, field):
        """Validação customizada para hostnames"""
        if not field.data or len(field.data) == 0:
            raise ValidationError('Por favor, selecione pelo menos uma OLT')

    def validate_commands(self, field):
        """Validação customizada para commands"""
        if not field.data or not field.data.strip():
            raise ValidationError('Por favor, digite pelo menos um comando')
