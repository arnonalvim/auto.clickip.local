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

# Ou você pode usar o decorator diretamente:
@home_bp.route('/dashboard')  # Rota alternativa protegida
@login_required
def dashboard():
    return render_template('home.html')
