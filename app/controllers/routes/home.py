from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

home_bp = Blueprint('home_bp', __name__)


@home_bp.route('/')
def home():
    # Se o usuário não estiver logado, redireciona para login
    if not current_user.is_authenticated:
        return redirect(url_for('auth_bp.login'))
    # Se estiver logado, mostra a home
    return render_template('home.html')


# Usano uma rota alternativa para a home caso o fábio crie uma, eu não vou
@home_bp.route('/')  # rota alternativa
@login_required
def dashboard():
    return render_template('home.html')
