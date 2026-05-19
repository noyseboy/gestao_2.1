from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import Usuario

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = Usuario.query.filter_by(
            username=request.form.get('username'),
            password=request.form.get('password')
        ).first()

        if user:
            session['usuario_logado'] = user.username
            session['role'] = user.role
            if user.role == 'instrutor':
                return redirect(url_for('treinamento.treinamento'))
            return redirect(url_for('alunos.dashboard'))
        else:
            flash("Usuário ou senha inválidos.", "danger")

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))